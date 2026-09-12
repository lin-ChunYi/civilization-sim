#!/usr/bin/env python3
"""Cockpit 薄接力入口：只管**队列与回执**，不做验收。

这份脚本做什么：
  * 把已批准的派工投进本机 Cockpit hub 的 outbox（`reply_inject`），
  * 持续收 durable 回执与目标会话的助手输出，落盘持久化，
  * 把状态整理成一份脱敏的 STATUS，供人和主控看。

这份脚本**不做**什么（都是有意为之）：
  * 不做独立验收：助手自报 `CIV_RESULT_*` 只会让任务进入 `review`，
    真正的 `done` 必须由外部（已在运行的 Codex 主控 / 心跳）带证据 `accept`。
  * 不杀、不关、不重启任何用户自己的会话；暂停只发一次**协作式**通知。
  * 结果未知时不自动重发，不绕过额度或权限限制。
  * 不开网络端口、不起服务、不引入任何第三方依赖（Python 3.9+ 标准库）。

命令：start / watch / stop / status / submit / tick / pause / resume / accept / requeue
"""
import argparse
import datetime as dt
import fcntl
import hashlib
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import time
import uuid
from contextlib import contextmanager
from pathlib import Path

MARKER_PREFIX = 'CIV_RESULT_'
# 没有 durable 回执时，多久算"投递结果未知"。未知 = 停下来等人看，不是失败、更不是重发。
UNKNOWN_AFTER_SEC = 120
# snapshot 多旧就不再派单（Cockpit 不在线时不要盲投）
SNAPSHOT_STALE_SEC = 60
QUOTA_HINTS = ('quota', 'rate limit', 'rate_limit', 'usage limit', '额度', '限流')
# 文字与回车**已经送到**、只是没看到画面推进 —— 这类绝不是失败，更不能当成"没执行过"。
STALL_HINTS = ('agent_prompt_stalled', 'stalled', 'no visible progress', 'prompt_stalled')
# 只有这些能证明"根本没送到对面"的失败，才允许无确认重排。
NOT_DELIVERED_HINTS = ('session not found', 'no such session', 'device offline',
                       'not controllable', 'invalid envelope', 'unknown op',
                       'bad request', 'rejected before delivery', 'session gone')

class Busy(Exception):
    """项目操作锁被别人占着。守护应当跳过这一轮，独立命令应当如实报告繁忙。"""


RECEIPT_STATES = (
    'none',              # 还没发出去
    'queued',            # 信封已落 outbox，等桥接处理
    'bridge_ack',        # 桥接确认收到（非终态）
    'durable_ok',        # 落地回执 ok:true —— 只代表**送达**，不代表任务完成
    'failed',            # 明确失败（ok:false / .err）
    'quota_blocked',     # 明确的额度/限流阻塞
    'unknown',           # 超时仍无回执：结果未知，绝不自动重发
)


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def atomic(path, value):
    """原子落盘 0600。崩溃时要么是旧值、要么是完整新值，不会留半个文件。"""
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    tmp = path.with_name('.' + path.name + '.' + uuid.uuid4().hex + '.tmp')
    with tmp.open('x', encoding='utf-8') as fh:
        os.chmod(tmp, 0o600)
        json.dump(value, fh, ensure_ascii=False, indent=2)
        fh.write('\n')
        fh.flush()
        os.fsync(fh.fileno())
    tmp.replace(path)


def atomic_text(path, text, mode=0o600):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    tmp = path.with_name('.' + path.name + '.' + uuid.uuid4().hex + '.tmp')
    with tmp.open('x', encoding='utf-8') as fh:
        os.chmod(tmp, mode)
        fh.write(text)
        fh.flush()
        os.fsync(fh.fileno())
    tmp.replace(path)


def load_queue(root):
    """读队列。**不存在**可以初始化空的；**损坏**则保留原件并拒绝派发，
    绝不能让 watch/status 拿一个空队列把真实任务账覆盖掉。"""
    path = root / 'queue.json'
    if not path.exists():
        return {'paused': False, 'jobs': {}}, None
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
        if not isinstance(data, dict) or not isinstance(data.get('jobs'), dict):
            raise ValueError('queue.json has an unexpected shape')
        return data, None
    except (OSError, ValueError) as exc:
        backup = root / ('queue.corrupt.' + time.strftime('%Y%m%dT%H%M%S') + '.json')
        if not backup.exists():
            try:
                shutil.copy2(path, backup)
            except OSError:
                backup = path
        return None, ('queue.json is unreadable (%s); original preserved at %s; '
                      'dispatch is blocked until a human repairs it' % (exc, backup.name))


def read(path, default=None):
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return default


def sha(data):
    return hashlib.sha256(data).hexdigest()


# ---------------------------------------------------------------- 会话与转录

def session(snapshot, job):
    """在 snapshot 里找到这次派工登记的那个会话，并核对身份没有被换掉。"""
    for device in snapshot.get('devices', []):
        if device.get('device_id') != job['device_id']:
            continue
        if not device.get('online') or not device.get('controllable'):
            raise ValueError('target device offline or not controllable')
        for item in device.get('sessions', []):
            if item.get('session_id') == job['session_id']:
                if item.get('source') != job['owner'] or item.get('cwd') != job['session_cwd']:
                    raise ValueError('session source/cwd differs from registered identity')
                return item
    raise ValueError('registered session is absent')


def normalize_ws(text):
    """把 CR/LF/Tab 与连续空白折成单个空格 —— Cockpit 的 composeInjection 就是这么做的
    （cockpit-cloud-hub/internal/inject/attachment.go:94），所以转录里的用户记录
    和我们本地的提示词长得不一样，必须按同一规范比对。"""
    return ' '.join((text or '').split())


def inject_tag(task_id, corr):
    """每次投递的唯一前缀。它不含换行、不会被规范化改形，是最可靠的重绑定锚点。"""
    return '[dispatch %s %s]' % (task_id, corr[:8])


def parse_records(raw):
    """把 jsonl 文本切成记录。半条（最后一行没写完）不算证据，直接丢。"""
    out = []
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except ValueError:
            continue
    return out


def record_role(item, owner):
    """判断一条记录是不是**助手**说的。用户说的一律不算 —— 派工提示词里本来就带着
    CIV_RESULT_ 模板，把它当成完成信号是本脚本最容易犯的错。"""
    if owner == 'claude':
        if item.get('type') == 'assistant':
            return 'assistant'
        if item.get('type') == 'user':
            return 'user'
        return 'other'
    update = item.get('params', {}).get('update', {})
    kind = update.get('sessionUpdate')
    if kind == 'agent_message_chunk':
        return 'assistant'
    if kind in ('user_message_chunk', 'user_message'):
        return 'user'
    return 'other'


def record_text(item, owner):
    """取出一条记录里的文本。两种真实格式都要认：
       * Claude：assistant 记录的 message.content[] 里 type=text 的块，一条就是一整段；
       * Grok ACP：agent_message_chunk，**同一句话可能被拆成多条 chunk**，
         所以必须原样拼接、不能各自补换行，否则跨 chunk 的标记会被拆断。"""
    if owner == 'claude':
        parts = []
        for content in item.get('message', {}).get('content', []) or []:
            if isinstance(content, dict) and content.get('type') == 'text':
                parts.append(content.get('text', ''))
        return '\n'.join(parts)
    return item.get('params', {}).get('update', {}).get('content', {}).get('text', '')


def join_texts(owner, texts):
    # Claude 的块之间补换行；Grok 的 chunk 直接拼（它本来就是被拆开的一句话）
    return ('\n'.join(texts) + '\n') if owner == 'claude' and texts else ''.join(texts)


def assistant_text(job):
    """取"本次派工之后"的助手输出。

    真实坑：`request_transcript(tail_bytes)` 会把本机物化的转录文件**截短重写**，
    于是派工时记下的 transcript_offset 立刻失效（文件变小，或大小相同但内容整体前移）。
    处理办法是双保险：
      1. 记 offset 的同时记一个锚（offset 之前 512 字节的 sha256）。锚还对得上 -> 走快路。
      2. 对不上 -> 重新绑定：在**当前**文件里找到最后一条包含本次提示词开头的**用户**记录，
         只认它之后的助手记录。找不到就返回 unknown —— 宁可等人看，也不拿旧内容当完成。
    """
    path = Path(job['transcript'])
    if not path.exists():
        return '', 'transcript-missing'
    raw = path.read_bytes()
    offset = job.get('transcript_offset', 0)
    anchor = job.get('transcript_anchor')
    if len(raw) >= offset and (not anchor or sha(raw[max(0, offset - 512):offset]) == anchor):
        records = parse_records(raw[offset:].decode('utf-8', 'replace'))
        texts = [record_text(i, job['owner']) for i in records
                 if record_role(i, job['owner']) == 'assistant']
        return join_texts(job['owner'], texts), 'offset'

    # 重新绑定：按**实际投递文本**的规范化形式找那条用户记录。
    # 三件事一起处理：
    #   * Cockpit 会把 CR/LF/Tab 折成空格 -> 两边都 normalize_ws 再比；
    #   * Grok 会把用户提示词拆成多条 user chunk -> 连续的用户记录先拼起来再比；
    #   * 每次投递带唯一 [dispatch TASK CORR8] 前缀 -> 旧任务的同名标记冒充不了。
    tag = normalize_ws(job.get('inject_tag') or '')
    head = normalize_ws(job.get('inject_head') or job.get('prompt_head') or '')
    records = parse_records(raw.decode('utf-8', 'replace'))
    start, buffer = None, ''
    for idx, item in enumerate(records):
        role = record_role(item, job['owner'])
        if role == 'user':
            # Grok 的连续 user chunk 是**同一句话被切开的**，必须原样接起来：
            # 中间补空格会把跨 chunk 的 tag（如 "[dispa" + "tch T1 ..."）拼成
            # "[dispa tch T1 ..." 而找不到。Claude 的每条 text 是独立消息，保留换行分隔。
            buffer += record_text(item, job['owner']) if job['owner'] == 'grok' \
                else ('\n' + record_text(item, job['owner']))
            probe = normalize_ws(buffer)
            if (tag and tag in probe) or (not tag and head and head in probe):
                start = idx + 1
        else:
            buffer = ''
    if start is None:
        return '', 'rebind-failed'
    texts = [record_text(i, job['owner']) for i in records[start:]
             if record_role(i, job['owner']) == 'assistant']
    return join_texts(job['owner'], texts), 'rebound'


def find_marker(text, task_id):
    """只认单行 JSON 的唯一标记，取最后一次出现的那条。"""
    pattern = re.escape(MARKER_PREFIX + task_id) + r'\s+(\{[^\n]*\})'
    matches = re.findall(pattern, text)
    for candidate in reversed(matches):
        try:
            return json.loads(candidate)
        except ValueError:
            continue
    return None


# ---------------------------------------------------------------- 回执分类

def _hint(blob, hints):
    return any(h in blob for h in hints)


def classify_receipt(job, hub):
    """把投递结果分成互不含糊的几类。

    三条铁律：
      * **送达 ≠ 完成**；
      * **未知 ≠ 失败** —— 没有终态回执就是 unknown，到点也要判 unknown，
        不能因为 outbox 里还留着信封或 .ack 就永远停在 queued/bridge_ack；
      * 只有能证明"**根本没送到对面**"的失败，才允许无确认重排（safe_requeue）。
        `agent_prompt_stalled`（文字和回车都送到了、只是没看到画面推进）与
        半写/无法解析的回执，一律 unknown，重排必须人确认。
    """
    corr = job.get('corr_id')
    if not corr:
        return {'state': 'none', 'detail': '', 'safe_requeue': True}
    out = hub / 'outbox'
    waited = time.time() - job.get('started_epoch', time.time())
    overdue = waited > UNKNOWN_AFTER_SEC

    result = out / (corr + '.result.json')
    if result.exists():
        try:
            raw = result.read_text(encoding='utf-8', errors='replace')
            receipt = json.loads(raw)
            if not isinstance(receipt, dict):
                raise ValueError('receipt is not an object')
        except (OSError, ValueError) as exc:
            return {'state': 'unknown', 'safe_requeue': False,
                    'detail': 'result receipt unreadable/half-written (%s); outcome unknown, '
                              'no auto-resend' % exc}
        blob = json.dumps(receipt, ensure_ascii=False).lower()
        if receipt.get('ok') is True:
            return {'state': 'durable_ok', 'detail': '', 'receipt': receipt, 'safe_requeue': False}
        if _hint(blob, STALL_HINTS):
            return {'state': 'unknown', 'receipt': receipt, 'safe_requeue': False,
                    'detail': 'agent_prompt_stalled: text and Enter were delivered, only the '
                              'visible progress is missing; outcome unknown, no auto-resend'}
        if _hint(blob, QUOTA_HINTS):
            return {'state': 'quota_blocked', 'receipt': receipt, 'safe_requeue': False,
                    'detail': str(receipt.get('error', ''))[:200]}
        return {'state': 'failed', 'receipt': receipt,
                'safe_requeue': _hint(blob, NOT_DELIVERED_HINTS),
                'detail': str(receipt.get('error', ''))[:200]}

    err = out / (corr + '.err')
    if err.exists():
        detail = err.read_text(encoding='utf-8', errors='replace')[:300]
        low = detail.lower()
        if _hint(low, STALL_HINTS):
            return {'state': 'unknown', 'safe_requeue': False,
                    'detail': 'agent_prompt_stalled receipt; outcome unknown, no auto-resend'}
        if _hint(low, QUOTA_HINTS):
            return {'state': 'quota_blocked', 'detail': detail, 'safe_requeue': False}
        return {'state': 'failed', 'detail': detail,
                'safe_requeue': _hint(low, NOT_DELIVERED_HINTS)}

    # 没有终态回执。**无论 outbox 里还留着什么痕迹**，到点都要判 unknown。
    trace = 'envelope still in outbox'
    if any((out / (corr + suffix)).exists() for suffix in ('.ack.json', '.ack')):
        trace = 'bridge ack only'
    elif not (out / (corr + '.json')).exists():
        trace = 'envelope consumed'
    if overdue:
        return {'state': 'unknown', 'safe_requeue': False,
                'detail': 'no terminal receipt within %ds (%s); delivery outcome unknown, '
                          'no auto-resend' % (UNKNOWN_AFTER_SEC, trace)}
    if trace == 'bridge ack only':
        return {'state': 'bridge_ack', 'detail': '', 'safe_requeue': False}
    return {'state': 'queued', 'detail': trace, 'safe_requeue': False}


# ---------------------------------------------------------------- 收集与派发

def collect(job, root, hub, snapshot):
    """收一次：回执分类 + 会话状态 + 助手输出 + 标记判定。只读，不改别人的东西。"""
    if job['status'] not in ('running', 'blocked') or not job.get('corr_id'):
        return
    verdict = classify_receipt(job, hub)
    job['receipt_state'] = verdict['state']
    job['receipt_detail'] = verdict['detail']
    job['receipt_safe_requeue'] = bool(verdict.get('safe_requeue'))
    if 'receipt' in verdict:
        job['receipt'] = verdict['receipt']
        atomic(root / 'logs' / (job['task_id'] + '.receipt.json'), verdict['receipt'])
    if verdict['state'] in ('failed', 'quota_blocked'):
        job['status'] = 'blocked'
        job['blocking_reason'] = ('%s: %s' % (verdict['state'], verdict['detail'])).strip(': ')
        return
    if verdict['state'] == 'unknown':
        job['status'] = 'blocked'
        job['blocking_reason'] = verdict['detail']
        # 注意：不 return —— 投递结果未知，但助手可能已经在干活了，继续看它的输出。

    try:
        current = session(snapshot, job)
        job['agent_state'] = current.get('state')
        job['pending_count'] = len(current.get('pending') or [])
        job.pop('attention', None)
    except (ValueError, OSError) as exc:
        job['attention'] = str(exc)
        return

    text, mode = assistant_text(job)
    job['transcript_read_mode'] = mode
    if mode in ('rebind-failed', 'transcript-missing'):
        job['attention'] = ('transcript was truncated/replaced and could not be re-anchored; '
                            'inspect manually, no completion is inferred')
        return
    if text:
        log = root / 'logs' / (job['task_id'] + '.assistant.txt')
        atomic_text(log, text)
        job['output_log'] = str(log)
        job['last_output'] = text[-1200:]

    report = find_marker(text, job['task_id'])
    if report:
        job['report'] = report
        if current.get('state') in ('waiting', 'idle'):
            # 自报完成只到 review。done 必须由外部带证据 accept。
            job['status'] = 'blocked' if report.get('status') == 'blocked' else 'review'
            job['finished_at'] = now()
            job['blocking_reason'] = report.get('blocking_reason', '') or job.get('blocking_reason', '')
    elif job.get('pending_count'):
        job['status'] = 'blocked' if job['status'] == 'blocked' else job['status']
        job['attention'] = ('agent has a permission/question item; inspect the transcript, '
                            'do not blanket approve')
        job['receipt_state'] = 'permission_pending' if job['receipt_state'] == 'durable_ok' \
            else job['receipt_state']


def envelope_for(job, hub, text):
    corr = uuid.uuid4().hex.upper()
    return corr, {'corr_id': corr, 'device_id': job['device_id'], 'session_id': job['session_id'],
                  'op': 'reply_inject', 'data': {'text': text}}


def dispatch(job, root, hub, snapshot, queue):
    """派一次工。**先持久化认领，再投信封** —— 崩溃绝不能造成重复派发。"""
    current = session(snapshot, job)
    if current.get('state') not in ('waiting', 'idle') or current.get('pending'):
        raise ValueError('target is not at an idle turn boundary')
    if job['owner'] == 'claude' and not current.get('claude_pid'):
        raise ValueError('existing session has no live PID; do not guess a resume command')
    path = hub / 'transcript' / job['device_id'] / (job['session_id'] + '.jsonl')
    if not path.exists():
        raise ValueError('transcript missing; request history before dispatch')
    prompt = Path(job['prompt_file']).read_text(encoding='utf-8')
    raw = path.read_bytes()
    offset = len(raw)
    corr = uuid.uuid4().hex.upper()
    tag = inject_tag(job['task_id'], corr)
    text = tag + '\n' + prompt          # 唯一前缀：重绑定用它，比提示词开头稳
    envelope = {'corr_id': corr, 'device_id': job['device_id'], 'session_id': job['session_id'],
                'op': 'reply_inject', 'data': {'text': text}}
    job.update(status='running', corr_id=corr, started_at=now(), started_epoch=time.time(),
               transcript=str(path), transcript_offset=offset,
               transcript_anchor=sha(raw[max(0, offset - 512):offset]),
               inject_tag=tag, inject_head=normalize_ws(text)[:120],
               inject_text_sha=sha(text.encode('utf-8')),
               prompt_head=prompt.strip()[:120], prompt_sha=sha(prompt.encode('utf-8')),
               receipt_state='queued', receipt_detail='envelope published',
               registered_pid=current.get('claude_pid'), owns_session=False,
               dispatch_count=job.get('dispatch_count', 0) + 1)
    atomic(root / 'queue.json', queue)                       # 认领先落盘
    atomic(root / 'logs' / (job['task_id'] + '.command.json'), envelope)
    atomic(hub / 'outbox' / (corr + '.json'), envelope)       # 再投递


PAUSE_NOTE = ('[dispatcher] 已请求暂停：请在**下一个安全点**停下并说明当前进度，不要中断正在写的文件。'
              '这是协作式请求，不会打断你当前这一步，也不会关闭会话。')


def send_pause_notice(job, root, hub, snapshot):
    """对本调度登记、且仍在跑的回合，**只发一次**协作式暂停请求。
    不杀进程、不关会话，也不承诺立刻中断。"""
    if job.get('pause_notice_sent') or job['status'] != 'running':
        return False
    try:
        session(snapshot, job)                    # 会话不在就别发
    except (ValueError, OSError):
        return False
    corr, envelope = envelope_for(job, hub, PAUSE_NOTE)
    job['pause_notice_sent'] = True
    job['pause_corr_id'] = corr
    job['pause_requested_at'] = now()
    atomic(root / 'logs' / (job['task_id'] + '.pause.json'), envelope)
    atomic(hub / 'outbox' / (corr + '.json'), envelope)
    return True


def tick_once(root, hub, queue, allow_dispatch=True):
    """收一轮 + 必要时派一单。返回 (queue, 本轮是否派出去了)。"""
    snapshot_path = hub / 'snapshot.json'
    snapshot = read(snapshot_path, {}) or {}
    for job in queue['jobs'].values():
        collect(job, root, hub, snapshot)

    if queue.get('paused'):
        for job in queue['jobs'].values():
            if send_pause_notice(job, root, hub, snapshot):
                queue['pause_notices'] = queue.get('pause_notices', 0) + 1
        return queue, False

    if not allow_dispatch:
        return queue, False
    try:
        stale = time.time() - snapshot_path.stat().st_mtime > SNAPSHOT_STALE_SEC
    except OSError:
        stale = True
    if stale:
        queue['note'] = 'Cockpit snapshot is stale or missing; no dispatch this round'
        return queue, False
    queue.pop('note', None)

    # review/blocked 会占住 owner（防止越过验收就发下一个任务），
    # 但**明确指向它的返工任务**可以放行。rejected 不占用。
    # 占位身份按优先级取：running > blocked > review —— 已经在跑的那条必须优先占住 owner，
    # 否则字典顺序会让一条 review 顶掉真正在跑的任务。
    rank = {'running': 0, 'blocked': 1, 'review': 2}
    holding = {}
    for j in queue['jobs'].values():
        if j['status'] not in rank:
            continue
        cur = holding.get(j['owner'])
        if cur is None or rank[j['status']] < rank[queue['jobs'][cur]['status']]:
            holding[j['owner']] = j['task_id']
    busy = set(holding)
    sent = False
    for job in sorted(queue['jobs'].values(), key=lambda j: j.get('created_at', '')):
        if job['status'] != 'pending':
            continue
        if job['owner'] in busy:
            target = job.get('rework_of')
            prior = queue['jobs'].get(target) if target else None
            rework_ok = bool(prior) and prior['owner'] == job['owner'] and \
                prior['status'] in ('review', 'rejected', 'blocked') and \
                holding.get(job['owner']) in (target, None)
            if not rework_ok:
                continue
        if any(queue['jobs'].get(dep, {}).get('status') != 'done' for dep in job['dependencies']):
            continue
        try:
            dispatch(job, root, hub, snapshot, queue)
            # 立刻把本轮的占用身份换成刚派出去的这条。
            # 少了这一步，第二条 rework_of 指向同一个 review 的 pending 任务
            # 会在**同一个 tick 里**被一起派出去（同一个会话收到两份活）。
            busy.add(job['owner'])
            holding[job['owner']] = job['task_id']
            sent = True
        except (ValueError, OSError) as exc:
            job['blocking_reason'] = str(exc)
    return queue, sent


# ---------------------------------------------------------------- STATUS

def render_status(queue, root, hub):
    """脱敏摘要：当前任务 / 下一项 / 提交 / 实测 / 截图 / 阻塞。
    完整提示词与转录只留在 logs/（0600），这里一个字都不放。"""
    rows = []
    for job in sorted(queue['jobs'].values(), key=lambda j: j.get('created_at', '')):
        report = job.get('report') or {}
        tests = report.get('tests') or []
        rows.append({
            'task_id': job['task_id'], 'owner': job['owner'], 'status': job['status'],
            'receipt_state': job.get('receipt_state', 'none'),
            'agent_state': job.get('agent_state'),
            'transcript_read_mode': job.get('transcript_read_mode'),
            'commit': report.get('commit', ''),
            'branch': report.get('branch', job.get('branch', '')),
            'tests': [str(t)[:120] for t in tests[:6]],
            'screenshots': ([s for s in (report.get('screenshots') or []) if s]
                            or ([report['screenshot']] if report.get('screenshot') else [])),
            'blocking_reason': (job.get('blocking_reason') or '')[:200],
            'attention': (job.get('attention') or '')[:200],
            'accepted_at': job.get('accepted_at', ''),
        })
    nxt = next((r['task_id'] for r in rows if r['status'] == 'pending'), '')
    current = next((r['task_id'] for r in rows if r['status'] == 'running'), '')
    watch = read(root / 'watch.json', {}) or {}
    summary = {'generated_at': now(), 'paused': bool(queue.get('paused')),
               'watcher': {'pid': watch.get('pid'), 'alive': watcher_alive(root),
                           'heartbeat': watch.get('heartbeat')},
               'current': current, 'next': nxt, 'note': queue.get('note', ''),
               'acceptance': 'independent acceptance is NOT done here; '
                             'self-reported results stop at "review"',
               'jobs': rows}
    atomic(root / 'STATUS.json', summary)
    lines = ['# dispatch STATUS', '', '- generated: %s' % summary['generated_at'],
             '- paused: %s' % summary['paused'],
             '- watcher: pid=%s alive=%s heartbeat=%s' % (watch.get('pid'),
                                                          summary['watcher']['alive'],
                                                          watch.get('heartbeat')),
             '- current: %s' % (current or '-'), '- next: %s' % (nxt or '-'),
             '- note: %s' % (summary['note'] or '-'),
             '- acceptance: %s' % summary['acceptance'], '']
    for r in rows:
        lines.append('## %s (%s)' % (r['task_id'], r['owner']))
        lines.append('- status: %s / receipt: %s / agent: %s / transcript: %s'
                     % (r['status'], r['receipt_state'], r['agent_state'], r['transcript_read_mode']))
        if r['commit']:
            lines.append('- commit: %s' % r['commit'])
        if r['tests']:
            lines.append('- tests: %s' % '; '.join(r['tests']))
        if r['screenshots']:
            lines.append('- screenshots: %s' % '; '.join(str(x)[:120] for x in r['screenshots']))
        if r['blocking_reason']:
            lines.append('- blocking: %s' % r['blocking_reason'])
        if r['attention']:
            lines.append('- attention: %s' % r['attention'])
        lines.append('')
    atomic_text(root / 'STATUS.md', '\n'.join(lines), 0o600)
    return summary


# ---------------------------------------------------------------- 进程与锁

@contextmanager
def op_lock(root, wait=0.0):
    """短时操作锁：同一项目同一时刻只有一个进程在改队列。

    `wait > 0` 时最多等这么久（守护用），拿不到就抛 Busy —— 守护跳过这一轮继续活着，
    **不能**因为 status/submit/pause 正常占了一下锁就退出。独立命令用 wait=0，如实报繁忙。
    """
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    deadline = time.time() + max(0.0, wait)
    with (root / 'controller.lock').open('a+') as lock:
        while True:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if time.time() >= deadline:
                    raise Busy('another controller operation holds the project lock')
                time.sleep(0.2)
        yield


def watch_identity(root):
    """三态判定：(True/False/None, info, 说明)。

    True  = 确认是**本脚本、本 state-dir、本次 watch** 的进程；
    False = 确认已经不在了；
    None  = **查不出来**（ps 不可用、或 pid 活着但不是我们的 —— 典型是 PID 被复用）。
    None 一律不发信号：宁可留个孤儿状态文件让人看，也不能误杀别人的进程。
    """
    info = read(root / 'watch.json', {}) or {}
    pid, token = info.get('pid'), info.get('token')
    if not pid or not token:
        return False, info, 'no live watcher recorded'
    try:
        os.kill(int(pid), 0)
    except ProcessLookupError:
        return False, info, 'recorded pid is gone'
    except (OSError, ValueError, TypeError) as exc:
        return None, info, 'cannot probe pid (%s); identity unknown' % exc
    try:
        out = subprocess.run(['ps', '-p', str(pid), '-o', 'command='],
                             capture_output=True, text=True, timeout=5)
    except Exception as exc:                                    # noqa: BLE001
        return None, info, 'ps unavailable (%s); identity unknown' % exc
    if out.returncode != 0:
        return False, info, 'process disappeared while probing'
    line = out.stdout or ''
    if 'dispatch.py' in line and 'watch' in line and str(root) in line:
        return True, info, 'identity confirmed'
    return None, info, ('pid %s is alive but is not this state-dir watcher '
                        '(likely PID reuse); refusing to signal it' % pid)


def watcher_alive(root):
    """只有**确认是自己人**才算活着。查不出来不算活，也不会被当成死。"""
    return watch_identity(root)[0] is True


def cmd_watch(root, hub, interval, once=False, lock_wait=10.0):
    """前台守护：唯一控制进程。收结果 -> 持久化 -> 必要时派单。"""
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    lock_file = (root / 'watch.lock').open('a+')
    try:
        fcntl.flock(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        raise SystemExit('another watcher already holds the project watch lock')
    stop_flag = {'stop': False}

    def handler(signum, _frame):
        stop_flag['stop'] = True
    signal.signal(signal.SIGTERM, handler)
    signal.signal(signal.SIGINT, handler)
    stop_request = root / 'stop.request'
    token = uuid.uuid4().hex
    if stop_request.exists():
        stop_request.unlink()          # 上一任留下的停止请求不该停到我头上
    atomic(root / 'watch.json', {'pid': os.getpid(), 'token': token, 'started_at': now(),
                                 'hub': str(hub), 'state_dir': str(root),
                                 'interval': interval, 'heartbeat': now(),
                                 'last_round': None, 'skipped_rounds': 0})
    skipped = 0

    def stop_requested():
        """只认写着**我的 token** 的停止请求（或明确的 'any'）。"""
        if not stop_request.exists():
            return False
        try:
            want = stop_request.read_text(encoding='utf-8').strip()
        except OSError:
            return False
        return want in (token, 'any', '')

    try:
        while not stop_flag['stop']:
            round_note = 'ok'
            try:
                with op_lock(root, wait=lock_wait):
                    queue, problem = load_queue(root)
                    if problem:
                        # 队列文件坏了：保留原件、拦住派发、如实上报，绝不写回空队列
                        round_note = problem
                        atomic(root / 'BLOCKED.json', {'at': now(), 'reason': problem})
                    else:
                        queue, _ = tick_once(root, hub, queue)
                        queue['updated_at'] = now()
                        atomic(root / 'queue.json', queue)
                        render_status(queue, root, hub)
            except Busy as exc:
                # 别人（status/submit/pause）正常占锁 —— 跳过这一轮，**不退出**
                skipped += 1
                round_note = 'skipped: %s' % exc
            info = read(root / 'watch.json', {}) or {}
            info.update(heartbeat=now(), last_round=round_note, skipped_rounds=skipped)
            atomic(root / 'watch.json', info)
            if once:
                break
            for _ in range(max(1, int(interval))):
                if stop_flag['stop'] or stop_requested():
                    stop_flag['stop'] = True
                    break
                time.sleep(1)
    finally:
        info = read(root / 'watch.json', {}) or {}
        info.update(stopped_at=now(), pid=None, token=None)
        atomic(root / 'watch.json', info)
        if stop_request.exists() and stop_requested_token_matches(stop_request, token):
            stop_request.unlink()
        fcntl.flock(lock_file, fcntl.LOCK_UN)
        lock_file.close()
    return 0


def stop_requested_token_matches(path, token):
    try:
        return path.read_text(encoding='utf-8').strip() in (token, 'any', '')
    except OSError:
        return False


def cmd_start(root, hub, interval):
    if watcher_alive(root):
        raise SystemExit('watcher already running (pid %s); refusing to start a second controller'
                         % (read(root / 'watch.json', {}) or {}).get('pid'))
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    (root / 'logs').mkdir(parents=True, exist_ok=True, mode=0o700)
    log = (root / 'logs' / 'watch.log').open('a', encoding='utf-8')
    proc = subprocess.Popen([sys.executable, str(Path(__file__).resolve()),
                             '--state-dir', str(root), '--hub-dir', str(hub),
                             'watch', '--interval', str(interval)],
                            stdout=log, stderr=log, start_new_session=True)
    for _ in range(50):
        if watcher_alive(root):
            break
        time.sleep(0.1)
    return {'started': True, 'pid': proc.pid, 'alive': watcher_alive(root),
            'log': str(root / 'logs' / 'watch.log')}


def cmd_stop(root, grace=15):
    """只停**自己启动的 watch 进程**。绝不碰任何被借用的用户会话。

    顺序是：先核对身份 -> 写一个带 token 的协作式 stop.request -> 只有身份确认才发 SIGTERM。
    身份查不出来（ps 不可用、或 PID 被别的进程复用）一律**不发信号**。
    """
    confirmed, info, why = watch_identity(root)
    pid = info.get('pid')
    if confirmed is False:
        return {'stopped': False, 'signalled': False, 'pid': pid, 'reason': why}
    if confirmed is None:
        return {'stopped': False, 'signalled': False, 'pid': pid, 'reason': why,
                'hint': 'inspect the process manually; this command will not signal an '
                        'unverified pid'}
    atomic_text(root / 'stop.request', info.get('token') or 'any')
    try:
        os.kill(int(pid), signal.SIGTERM)
    except OSError as exc:
        return {'stopped': False, 'signalled': False,
                'reason': 'signal failed: %s' % exc, 'pid': pid}
    for _ in range(grace * 10):
        if watch_identity(root)[0] is not True:
            return {'stopped': True, 'signalled': True, 'pid': pid, 'forced': False}
        time.sleep(0.1)
    return {'stopped': False, 'signalled': True, 'pid': pid,
            'reason': 'watcher did not exit within grace; inspect before escalating '
                      '(state is written atomically, nothing is lost)'}


# ---------------------------------------------------------------- 子命令

REQUIRED_FIELDS = ('task_id', 'owner', 'objective', 'allowed_paths', 'baseline_sha',
                   'dependencies', 'acceptance', 'workdir', 'branch', 'device_id',
                   'session_id', 'session_cwd', 'prompt_file')


def cmd_submit(queue, job_file):
    job = read(job_file)
    if job is None:
        raise ValueError('job file is not readable JSON')
    for field in REQUIRED_FIELDS:
        if field not in job:
            raise ValueError('missing task field: ' + field)
    if job['owner'] not in ('claude', 'grok') or not re.fullmatch(r'[A-Z0-9_]+', job['task_id']):
        raise ValueError('owner/task_id rejected')
    if job['task_id'] in queue['jobs']:
        raise ValueError('task already exists; use a new revision ID')
    if not Path(job['prompt_file']).is_file():
        raise ValueError('prompt_file does not exist')
    # 返工任务：允许在同一个 owner 还压着一条 review/rejected 的情况下派出去。
    # 但必须明确指向那一条，且 owner 相同 —— 正常的下一个任务仍然要等 accept。
    target = job.get('rework_of')
    if target:
        prior = queue['jobs'].get(target)
        if prior is None:
            raise ValueError('rework_of points to an unknown task')
        if prior['owner'] != job['owner']:
            raise ValueError('rework_of must stay with the same owner')
        if prior['status'] not in ('review', 'rejected', 'blocked'):
            raise ValueError('rework_of target is not in review/rejected/blocked')
    job.update(status='pending', created_at=now(), receipt_state='none', dispatch_count=0)
    queue['jobs'][job['task_id']] = job
    return job


def cmd_reject(queue, task_id, reason):
    """外部复核认为不合格：review -> rejected。owner 随之解锁，可以接返工任务。
    这是**受控**闭环，不是让人去手改 queue.json 绕过。"""
    job = queue['jobs'].get(task_id)
    if job is None:
        raise ValueError('unknown task')
    if job['status'] not in ('review', 'blocked'):
        raise ValueError('only a task in review/blocked can be rejected')
    job.update(status='rejected', rejected_at=now(), reject_reason=reason)
    return job


def cmd_accept(queue, task_id, evidence):
    job = queue['jobs'].get(task_id)
    if job is None:
        raise ValueError('unknown task')
    if job['status'] != 'review':
        raise ValueError('only an independently reviewed task can be accepted')
    if not Path(evidence).is_file():
        raise ValueError('acceptance evidence file does not exist')
    job.update(status='done', accepted_at=now(),
               acceptance_evidence=str(Path(evidence).resolve()))
    return job


def cmd_requeue(queue, task_id, acknowledge):
    """重排的唯一免确认条件：**能证明根本没送到对面**（receipt_safe_requeue）。

    `agent_prompt_stalled`、半写回执、任何 unknown、以及原因不明的失败，
    都必须 `--acknowledge-duplicate-risk` —— 因为文字可能已经送到了，重排就是重复派工。
    """
    job = queue['jobs'].get(task_id)
    if job is None:
        raise ValueError('unknown task')
    state = job.get('receipt_state')
    if state not in ('failed', 'quota_blocked', 'unknown', 'none'):
        raise ValueError('refusing to requeue a task whose delivery state is %r' % state)
    safe = bool(job.get('receipt_safe_requeue')) or state == 'none'
    if not safe and not acknowledge:
        raise ValueError('delivery may already have reached the target (state=%s, detail=%s); '
                         'pass --acknowledge-duplicate-risk only after a human confirmed it '
                         'never arrived' % (state, (job.get('receipt_detail') or '')[:120]))
    job.update(status='pending', corr_id=None, receipt_state='none', receipt_detail='',
               blocking_reason='', requeued_at=now())
    job.pop('report', None)
    return job


def summarize(queue):
    keys = ('task_id', 'owner', 'status', 'receipt_state', 'agent_state', 'corr_id',
            'blocking_reason', 'attention', 'report')
    return {'paused': bool(queue.get('paused')), 'note': queue.get('note', ''),
            'jobs': [{k: j.get(k) for k in keys} for j in queue['jobs'].values()]}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    default_state = Path(__file__).resolve().parents[1] / '.dispatch'
    default_hub = Path(os.environ.get('COCKPIT_HUB_DIR', str(Path.home() / '.cockpit' / 'hub')))
    ap.add_argument('--state-dir', type=Path, default=default_state)
    ap.add_argument('--hub-dir', type=Path, default=default_hub)
    sub = ap.add_subparsers(dest='command', required=True)
    sub.add_parser('submit').add_argument('job_file', type=Path)
    for name in ('tick', 'status', 'pause', 'resume'):
        sub.add_parser(name)
    w = sub.add_parser('watch'); w.add_argument('--interval', type=int, default=20)
    w.add_argument('--once', action='store_true')
    # 守护等待项目锁的上限；等不到就跳过这一轮**继续活着**，不是退出
    w.add_argument('--lock-wait', type=float, default=10.0)
    s = sub.add_parser('start'); s.add_argument('--interval', type=int, default=20)
    sub.add_parser('stop')
    done = sub.add_parser('accept')
    done.add_argument('task_id'); done.add_argument('--evidence', required=True)
    rq = sub.add_parser('requeue')
    rq.add_argument('task_id'); rq.add_argument('--acknowledge-duplicate-risk', action='store_true')
    rj = sub.add_parser('reject')
    rj.add_argument('task_id'); rj.add_argument('--reason', required=True)
    args = ap.parse_args(argv)
    root, hub = args.state_dir.resolve(), args.hub_dir.resolve()
    root.mkdir(parents=True, exist_ok=True, mode=0o700)

    if args.command == 'watch':
        return cmd_watch(root, hub, args.interval, args.once, args.lock_wait)
    if args.command == 'start':
        print(json.dumps(cmd_start(root, hub, args.interval), ensure_ascii=False, indent=2))
        return 0
    if args.command == 'stop':
        print(json.dumps(cmd_stop(root), ensure_ascii=False, indent=2))
        return 0

    try:
        lock_ctx = op_lock(root)
        lock_ctx.__enter__()
    except Busy as exc:
        print(json.dumps({'busy': True, 'reason': str(exc)}, ensure_ascii=False, indent=2))
        return 3
    try:
        queue, problem = load_queue(root)
        if problem:
            # 队列坏了：原件已保留，这里只报告并拦住一切改动，绝不写回空队列
            print(json.dumps({'blocked': True, 'reason': problem}, ensure_ascii=False, indent=2))
            return 2
        if args.command == 'submit':
            cmd_submit(queue, args.job_file)
        elif args.command == 'pause':
            queue['paused'] = True          # 立刻拦住新派单；已在跑的回合只发一次协作式通知
            queue, _ = tick_once(root, hub, queue, allow_dispatch=False)
        elif args.command == 'resume':
            queue['paused'] = False
            for job in queue['jobs'].values():
                job.pop('pause_notice_sent', None)
        elif args.command == 'accept':
            cmd_accept(queue, args.task_id, args.evidence)
        elif args.command == 'reject':
            cmd_reject(queue, args.task_id, args.reason)
        elif args.command == 'requeue':
            cmd_requeue(queue, args.task_id, args.acknowledge_duplicate_risk)
        elif args.command == 'status':
            queue, _ = tick_once(root, hub, queue, allow_dispatch=False)
        else:                                # tick
            queue, _ = tick_once(root, hub, queue, allow_dispatch=not queue.get('paused'))
        queue['updated_at'] = now()
        atomic(root / 'queue.json', queue)
        render_status(queue, root, hub)
        print(json.dumps(summarize(queue), ensure_ascii=False, indent=2))
    finally:
        lock_ctx.__exit__(None, None, None)
    return 0


if __name__ == '__main__':
    sys.exit(main())
