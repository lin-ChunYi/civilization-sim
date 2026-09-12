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
import traceback
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
# 这些回执明说了"结果未知"或"投递本身不安全/没重试"，**一律 unknown**：
# 继续观察，绝不自动重发。真实例子：原生 Grok 终端回的
# `[delivery state=unknown retry=none] ... native terminal unsafe ...`
# 以前被归成 failed（虽然 safe_requeue=false），口径是错的 —— 它不是失败，是不知道。
UNKNOWN_HINTS = ('delivery state=unknown', 'state=unknown', 'retry=none',
                 'native terminal unsafe', 'terminal unsafe', 'outcome unknown',
                 'result unknown', 'unsafe to retry')
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
    # --- 以下只出现在 transport=grok-cli 的任务上 ---
    'cli_launching',          # 认领已落盘，进程刚起（或还没确认起来）
    'cli_running',            # 已核验是本调度启动的那个进程，仍在跑
    'cli_observing',          # 接管观察的既有进程：只看，不发信号
    'cli_exited_incomplete',  # 子进程退了，但日志没写完/读不全 —— 结果未知
    'cli_no_unique_result',   # 退了、也没报错，但日志里没有唯一的结果标记
    'permission_cancelled',   # 工具权限被取消（stopReason=cancelled）—— 不是完成，也不是用户放弃
    'cli_failed',             # 明确的非零退出且不是上面几类
)

# 权限取消的真实证据（Grok CLI 的 JSON 输出里出现过这两个字段）。
# **这不是"用户取消了整个任务"**：它只说明某一次工具调用没被允许。
PERMISSION_CANCEL_HINTS = ('permissioncancelled', 'permission_cancelled',
                           'permission cancelled', 'cancellationcategory')


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
        if _hint(blob, UNKNOWN_HINTS):
            # 回执自己说了结果未知 / 投递不安全 / 没有重试 —— 那就是 unknown，不是失败。
            return {'state': 'unknown', 'receipt': receipt, 'safe_requeue': False,
                    'detail': 'receipt reports an unknown delivery outcome (%s); keep observing, '
                              'no auto-resend' % str(receipt.get('error', ''))[:160]}
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
        if _hint(low, UNKNOWN_HINTS):
            return {'state': 'unknown', 'safe_requeue': False,
                    'detail': 'receipt reports an unknown delivery outcome; keep observing, '
                              'no auto-resend: ' + detail[:160]}
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
    if report is not None:
        job['report'] = report                    # 原件照原样保留，一个字不动
        # 标记后面未必是对象：可能是数组、字符串、数字。取字段前先确认类型，
        # 别在非字典上调 .get()，那是 C04 这类"报告格式边界"的另一半。
        fields = report if isinstance(report, dict) else {}
        if current.get('state') in ('waiting', 'idle'):
            # 自报完成**只到 review**。done 必须由外部带证据 accept —— 报告是 agent 自己写的，
            # 格式再标准也不构成验收。
            job['status'] = 'blocked' if fields.get('status') == 'blocked' else 'review'
            job['finished_at'] = now()
            job['self_reported_at'] = now()
            job['blocking_reason'] = (one_line(fields.get('blocking_reason') or '', 200)
                                      or job.get('blocking_reason', ''))
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
        try:
            if is_cli(job):
                cli_reclaim(job, root, queue)     # 重启后先按 token 认回来，不重跑
                collect_cli(job, root)
            else:
                collect(job, root, hub, snapshot)
            job.pop('collect_error', None)
        except Exception as exc:                                     # noqa: BLE001
            # 一条任务的转录/回执/报告有问题，只记在这条任务上，**继续收其他任务**。
            # 它的状态一个字不动（不会被当成完成，也不会被当成失败）。
            job['collect_error'] = '%s: %s' % (type(exc).__name__, one_line(exc, 160))
            job['attention'] = ('collect failed for this task; inspect logs/ and the raw report, '
                                'do not accept on this evidence')

    if queue.get('paused'):
        for job in queue['jobs'].values():
            # grok-cli 是 headless 的，**没有安全的输入框**：一个字都不往里注入。
            sent = cli_pause(job, root) if is_cli(job) \
                else send_pause_notice(job, root, hub, snapshot)
            if sent:
                queue['pause_notices'] = queue.get('pause_notices', 0) + 1
        return queue, False

    if not allow_dispatch:
        return queue, False
    try:
        stale = time.time() - snapshot_path.stat().st_mtime > SNAPSHOT_STALE_SEC
    except OSError:
        stale = True
    if stale:
        # 只拦 Cockpit 通道。grok-cli 不经 Cockpit，它的可用性跟 snapshot 无关。
        queue['note'] = ('Cockpit snapshot is stale or missing; no dispatch on the Cockpit '
                         'transport this round (grok-cli tasks are unaffected)')
        if not any(is_cli(j) and j['status'] == 'pending' for j in queue['jobs'].values()):
            return queue, False
    else:
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
        if stale and not is_cli(job):
            continue                              # Cockpit 不在线：这条先不派
        try:
            if is_cli(job):
                # 同一个 owner 只要还有活着的 CLI 进程，就不派下一个。
                live = [j for j in queue['jobs'].values()
                        if j is not job and j['owner'] == job['owner'] and is_cli(j)
                        and j['status'] in ('running', 'blocked')
                        and probe_cli(j) in ('alive', 'unknown')]
                if live:
                    job['blocking_reason'] = (
                        'owner %s still has a live/unverified CLI run (%s); not launching'
                        % (job['owner'], live[0]['task_id']))
                    continue
                if (job.get('cli') or {}).get('adopt'):
                    adopt_cli(job, root, queue)
                else:
                    launch_cli(job, root, queue)
            else:
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


# ------------------------------------------------- transport = grok-cli
# 另一条投递通道：直接以**订阅版 headless CLI**跑一轮，和默认的 Cockpit 通道并存。
# 边界写在前面，别指望这里有的东西：
#   * 不经 Cockpit：CLI 是 headless 的，没有安全的输入框，**绝不 reply_inject**。
#   * 不做实时 checkpoint：进程跑到哪一步我们看不见，只能读它自己写出来的日志。
#     "下一个安全点停下"是**下一轮不再派**，不是把当前这一轮掐断。
#   * 不切付费 API、不改任何全局配置、不自动 bypass / always-approve。
#     权限规则必须在任务里逐条写明，缺一条就是缺一条。
#   * 只对**本调度启动、且身份核验过**的 PID 发信号；接管观察的既有进程一个信号都不发。
CLI_TRANSPORT = 'grok-cli'
# 一次派工的唯一身份：写进 per-dispatch 的提示词文件名，所以它会出现在命令行里，
# 重启之后能靠 `ps` 把那个进程重新认出来（而不是靠"我记得 pid 是多少"）。
CLI_TOKEN_PREFIX = 'ciltok'
# 本进程这一趟启动的子进程。守护是长期进程，Popen 不 poll 就会把子进程留成僵尸
# （僵尸的 kill(pid,0) 照样成功，probe 会永远报 alive）。重启之后这里是空的，
# 那时子进程已经被 init 接管，不会有僵尸，退出码也就拿不到了 —— 如实记 null。
_CLI_PROCS = {}


def is_cli(job):
    return (job or {}).get('transport') == CLI_TRANSPORT


def cli_spec(job):
    """校验并归一化任务里的 CLI 声明。缺什么就说缺什么，不猜、不补默认命令。"""
    spec = job.get('cli')
    if not isinstance(spec, dict):
        raise ValueError('transport=grok-cli requires a "cli" object')
    binary = spec.get('bin')
    if not binary or not isinstance(binary, str):
        raise ValueError('cli.bin (existing CLI path) is required')
    if not Path(binary).is_file():
        raise ValueError('cli.bin does not exist: ' + binary)
    cwd = spec.get('cwd')
    if not cwd or not Path(cwd).is_dir():
        raise ValueError('cli.cwd must be an existing directory')
    sid = spec.get('session_id')
    if sid is not None and not re.fullmatch(r'[0-9a-fA-F-]{8,64}', str(sid)):
        raise ValueError('cli.session_id must look like a session UUID')
    for key in ('allow', 'deny', 'extra_args'):
        val = spec.get(key)
        if val is not None and (not isinstance(val, list)
                                or not all(isinstance(x, str) for x in val)):
            raise ValueError('cli.%s must be a list of strings' % key)
    if spec.get('permission_mode') in ('bypassPermissions', 'bypass', 'alwaysApprove',
                                       'always-approve', 'yolo'):
        raise ValueError('refusing a blanket permission mode; list the rules explicitly')
    adopt = spec.get('adopt')
    if adopt is not None and not isinstance(adopt, dict):
        raise ValueError('cli.adopt must be an object {pid, session_id?, journal?}')
    return spec


def cli_argv(job, prompt_path):
    """拼出**显式**命令数组。不过 shell、不拼字符串、不带任何隐藏默认值。"""
    spec = job['cli']
    argv = [spec['bin'], '--cwd', spec['cwd']]
    if spec.get('session_id'):
        argv += ['--resume', str(spec['session_id'])]       # 续用既有会话
    argv += ['--prompt-file', str(prompt_path)]
    if spec.get('output_format'):
        argv += ['--output-format', str(spec['output_format'])]
    if spec.get('permission_mode'):
        argv += ['--permission-mode', str(spec['permission_mode'])]
    for rule in spec.get('allow') or []:
        argv += ['--allow', rule]
    for rule in spec.get('deny') or []:
        argv += ['--deny', rule]
    if spec.get('max_turns'):
        argv += ['--max-turns', str(int(spec['max_turns']))]
    argv += list(spec.get('extra_args') or [])
    return argv


def proc_line(pid):
    """(lstart, command)。查不到返回 None，查不了返回 'unknown'。"""
    try:
        os.kill(int(pid), 0)
    except ProcessLookupError:
        return None
    except PermissionError:
        return 'unknown'
    except (OSError, ValueError, TypeError):
        return 'unknown'
    try:
        r = subprocess.run(['ps', '-p', str(int(pid)), '-o', 'lstart=,command='],
                           capture_output=True, text=True, timeout=5)
    except Exception:                                                # noqa: BLE001
        return 'unknown'
    if r.returncode != 0:
        try:
            os.kill(int(pid), 0)
        except ProcessLookupError:
            return None
        except Exception:                                            # noqa: BLE001
            return 'unknown'
        return 'unknown'
    line = ' '.join((r.stdout or '').split())
    if '<defunct>' in line or '(' + str(pid) + ')' == line:
        return None            # 僵尸：进程已经结束了，只是还没被父进程收走
    return line


def probe_cli(job):
    """这次派工的 CLI 进程现在怎么样：alive / gone / unknown。

    判据是**出生身份**，不是"我记得 pid 是多少"：启动时记下 `ps` 的启动时刻与完整命令行，
    现在必须还对得上。对不上就是 pid 被复用了（gone），查不了就是 unknown ——
    unknown 既不算活也不算死，更不是发信号的理由。
    """
    pid = job.get('cli_pid')
    if not pid:
        return 'gone'
    line = proc_line(pid)
    if line is None:
        return 'gone'
    if line == 'unknown':
        return 'unknown'
    token = job.get('cli_token') or ''
    birth = job.get('cli_birth') or ''
    if token and token in line:
        return 'alive'
    if birth and line == birth:
        return 'alive'
    return 'gone'                      # 这个 pid 现在是别人的进程


def find_by_token(token):
    """靠 token 在进程表里重新找回那次派工。返回 pid / None / 'unknown'。

    重启之后用它认领自己启动过的进程 —— 而不是"没看到 pid 就再跑一遍"。
    """
    if not token:
        return None
    try:
        r = subprocess.run(['ps', '-ax', '-o', 'pid=,command='],
                           capture_output=True, text=True, timeout=8)
    except Exception:                                                # noqa: BLE001
        return 'unknown'
    if r.returncode != 0:
        return 'unknown'
    hits = [ln.strip() for ln in (r.stdout or '').splitlines() if token in ln]
    hits = [h for h in hits if ' ps ' not in h and not h.endswith(' ps')]
    if not hits:
        return None
    if len(hits) > 1:
        return 'unknown'               # 不止一个：宁可等人看，也不乱认
    try:
        return int(hits[0].split(None, 1)[0])
    except (ValueError, IndexError):
        return 'unknown'


def launch_cli(job, root, queue):
    """起一轮 CLI。**先把认领落盘，再启动进程** —— 崩溃绝不能造成重复派发。"""
    spec = cli_spec(job)
    if job.get('cli_token'):
        raise ValueError('this task already has a launch token; refusing to launch twice')
    prompt = Path(job['prompt_file']).read_text(encoding='utf-8')
    token = CLI_TOKEN_PREFIX + '-' + job['task_id'] + '-' + uuid.uuid4().hex[:12]
    pdir = root / 'prompts'
    pdir.mkdir(parents=True, exist_ok=True, mode=0o700)
    # per-dispatch 的提示词副本：内容一字不改，但文件名带 token，
    # 于是 token 出现在命令行里，重启后能靠 ps 把这个进程重新认出来。
    prompt_path = pdir / (token + '.txt')
    atomic_text(prompt_path, prompt)
    journal = root / 'logs' / (token + '.stdout.jsonl')
    journal_err = root / 'logs' / (token + '.stderr.txt')
    argv = cli_argv(job, prompt_path)
    job.update(status='running', transport=CLI_TRANSPORT, started_at=now(),
               started_epoch=time.time(), cli_token=token, cli_argv=argv,
               cli_session_mode=('resume' if spec.get('session_id') else 'new'),
               cli_session_id=spec.get('session_id'),
               cli_prompt_copy=str(prompt_path), journal=str(journal),
               journal_err=str(journal_err), journal_offset=0,
               prompt_head=prompt.strip()[:120], prompt_sha=sha(prompt.encode('utf-8')),
               receipt_state='cli_launching',
               receipt_detail='claim persisted; process not confirmed yet',
               owns_process=True, cli_pid=None, cli_birth='', cli_rc=None,
               dispatch_count=job.get('dispatch_count', 0) + 1)
    atomic(root / 'queue.json', queue)                       # 认领先落盘
    atomic(root / 'logs' / (job['task_id'] + '.command.json'),
           {'argv': argv, 'cwd': spec['cwd'], 'token': token,
            'session_mode': job['cli_session_mode'], 'session_id': spec.get('session_id')})
    out = journal.open('ab')
    err = journal_err.open('ab')
    try:
        proc = subprocess.Popen(argv, cwd=spec['cwd'], stdin=subprocess.DEVNULL,
                                stdout=out, stderr=err, start_new_session=True)
    finally:
        out.close()
        err.close()
    for path in (journal, journal_err, prompt_path):
        try:
            os.chmod(path, 0o600)
        except OSError:
            pass
    _CLI_PROCS[job['task_id']] = proc
    job['cli_pid'] = proc.pid
    job['cli_birth'] = proc_line(proc.pid) if proc_line(proc.pid) != 'unknown' else ''
    job['receipt_state'] = 'cli_running'
    job['receipt_detail'] = 'launched pid %s (%s session)' % (proc.pid, job['cli_session_mode'])
    atomic(root / 'queue.json', queue)


def adopt_cli(job, root, queue):
    """接管观察一个**已经在跑**的 CLI 任务：只读日志、只探测，一个信号都不发。"""
    spec = cli_spec(job)
    adopt = spec['adopt']
    pid = adopt.get('pid')
    if not pid:
        raise ValueError('cli.adopt.pid is required to observe an existing run')
    line = proc_line(pid)
    if line is None:
        raise ValueError('cli.adopt.pid is not running')
    job.update(status='running', transport=CLI_TRANSPORT, started_at=now(),
               started_epoch=time.time(), cli_pid=int(pid),
               cli_birth=('' if line == 'unknown' else line),
               cli_token=adopt.get('token') or '',
               cli_session_mode='adopted', cli_session_id=adopt.get('session_id'),
               journal=str(adopt.get('journal') or ''), journal_offset=0,
               journal_err=str(adopt.get('journal_err') or ''),
               owns_process=False, cli_rc=None,
               receipt_state='cli_observing',
               receipt_detail='observing an existing run started elsewhere; '
                              'this dispatcher will never signal it')
    atomic(root / 'queue.json', queue)


def journal_text(job):
    """读日志正文。返回 (text, complete)。

    `complete=False` 表示最后一行是半条（进程正在写、或写到一半就退了）——
    半条一律不参与判定，宁可报"日志没写完"。
    """
    path = job.get('journal')
    if not path:
        return '', True
    try:
        raw = Path(path).read_bytes()
    except OSError:
        return '', False
    if not raw:
        return '', True
    complete = raw.endswith(b'\n')
    text = raw.decode('utf-8', errors='replace')
    if not complete:
        text = text[:text.rfind('\n') + 1]
    return text, complete


def journal_signals(text):
    """从日志里挑出**结构化**的线索。解析不了就退回全文扫描，不硬要求某种格式。"""
    hits = {'permission_cancelled': False, 'quota': False, 'stop_reasons': [],
            'session_id': None, 'records': 0}
    low = text.lower()
    if _hint(low, PERMISSION_CANCEL_HINTS):
        hits['permission_cancelled'] = True
    if _hint(low, QUOTA_HINTS):
        hits['quota'] = True
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith('{'):
            continue
        try:
            rec = json.loads(line)
        except ValueError:
            continue
        if not isinstance(rec, dict):
            continue
        hits['records'] += 1
        blob = json.dumps(rec, ensure_ascii=False).lower()
        if _hint(blob, PERMISSION_CANCEL_HINTS):
            hits['permission_cancelled'] = True
        if _hint(blob, QUOTA_HINTS):
            hits['quota'] = True
        for key in ('stopreason', 'stop_reason'):
            for k, v in rec.items():
                if k.lower() == key and isinstance(v, str):
                    hits['stop_reasons'].append(v)
        for k, v in rec.items():
            if k.lower() in ('session_id', 'sessionid') and isinstance(v, str):
                hits['session_id'] = v
    return hits


def _strings(value, out):
    if isinstance(value, str):
        out.append(value)
    elif isinstance(value, dict):
        for v in value.values():
            _strings(v, out)
    elif isinstance(value, list):
        for v in value:
            _strings(v, out)


def journal_search_text(text):
    """把日志变成可搜索的正文。

    `--output-format json` 下，助手正文是 JSON 字符串里的**转义**内容，直接在原始字节上
    找 `CIV_RESULT_X {...}` 会捞到一串 `\"` 根本解析不了。所以先把每条 JSON 记录里的
    字符串值解出来搜；解不出来再拿原始正文兜底（别的输出格式仍然能用）。
    """
    decoded = []
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith(('{', '[')):
            continue
        try:
            rec = json.loads(line)
        except ValueError:
            continue
        _strings(rec, decoded)
    return ['\n'.join(decoded), text]


def _markers_in(text, task_id):
    pattern = re.escape(MARKER_PREFIX + task_id) + r'\s+(\{[^\n]*\})'
    found = re.findall(pattern, text)
    parsed = []
    for cand in found:
        try:
            parsed.append(json.loads(cand))
        except ValueError:
            continue
    return parsed, len(found)


def unique_marker(text, task_id):
    """日志里必须有**唯一**的结果标记。零个或多个互相矛盾的，都算"没有唯一结果"。"""
    best_hits = 0
    for candidate in journal_search_text(text):
        parsed, raw_hits = _markers_in(candidate, task_id)
        best_hits = max(best_hits, raw_hits, len(parsed))
        if not parsed:
            continue
        distinct = {json.dumps(x, ensure_ascii=False, sort_keys=True) for x in parsed}
        if len(distinct) > 1:
            return None, len(parsed)
        return parsed[-1], len(parsed)
    return None, best_hits


def _reap(job):
    """把本进程启动的那个子进程收一下，拿到退出码。收不到就保持 None，不猜。"""
    proc = _CLI_PROCS.get(job['task_id'])
    if proc is None or proc.pid != job.get('cli_pid'):
        return
    try:
        rc = proc.poll()
        if rc is None:
            rc = proc.wait(timeout=0.3)
    except Exception:                                                # noqa: BLE001
        return
    if rc is not None:
        job['cli_rc'] = rc
        _CLI_PROCS.pop(job['task_id'], None)


def collect_cli(job, root):
    """收一次 grok-cli 任务。只读日志 + 探测进程，不发任何信号、不改别人的东西。

    **退出码 0 不等于完成。** 结论必须同时看：进程是不是真的结束了、日志有没有写完、
    有没有唯一的结果标记、有没有权限取消 / 额度限制。任何一条对不上就给准确的状态，
    停在那里等人看，不忙着重试。
    """
    if job['status'] not in ('running', 'blocked') or not is_cli(job):
        return
    _reap(job)                                 # 顺手回收，别留僵尸
    probe = probe_cli(job)
    if probe == 'gone':
        _reap(job)                             # 刚好在这一瞬间退出的，再收一次退出码
    job['cli_probe'] = probe
    text, complete = journal_text(job)
    job['journal_offset'] = len(text.encode('utf-8'))
    sig = journal_signals(text)
    if sig['session_id'] and not job.get('cli_session_id'):
        job['cli_session_id'] = sig['session_id']       # 新建会话：记下它报出来的 id
    report, hits = unique_marker(text, job['task_id'])
    if text:
        job['last_output'] = text[-1200:]
        job['output_log'] = job.get('journal')

    # 进程还在：继续观察。**不因为"暂时没输出"做任何判断。**
    if probe == 'alive':
        job['receipt_state'] = 'cli_running' if job.get('owns_process') else 'cli_observing'
        job['receipt_detail'] = 'pid %s still running (%d journal records)' % (
            job.get('cli_pid'), sig['records'])
        if sig['permission_cancelled']:
            job['attention'] = ('a tool permission was cancelled in this run; inspect the '
                                'journal and fix the permission rules, do not blanket approve')
        return
    if probe == 'unknown':
        # 查不到 ≠ 结束。不发信号、不下结论。
        job['receipt_state'] = 'unknown'
        job['receipt_detail'] = ('cannot verify the CLI process identity (ps unavailable / '
                                 'permission denied); outcome unknown, no auto-relaunch')
        job['status'] = 'blocked'
        job['blocking_reason'] = job['receipt_detail']
        return

    # 进程确认结束了。退出码只有"本进程这一趟启动的"才拿得到；
    # 重启之后认回来的、以及接管观察的，退出码就是拿不到 —— 如实记 null，不猜 0。
    rc = job.get('cli_rc')
    rc_note = ('' if rc is not None else
               ' (exit code unavailable: this controller process did not launch it — '
               'the verdict below comes from the journal, not from rc)')
    if not complete:
        job['receipt_state'] = 'cli_exited_incomplete'
        job['receipt_detail'] = ('the CLI process is gone but its journal ends mid-record; '
                                 'outcome unknown, no auto-relaunch')
        job['status'] = 'blocked'
        job['blocking_reason'] = job['receipt_detail']
        return
    if sig['quota']:
        job['receipt_state'] = 'quota_blocked'
        job['receipt_detail'] = 'the journal reports a quota/rate limit; not retrying'
        job['status'] = 'blocked'
        job['blocking_reason'] = job['receipt_detail']
        return
    if sig['permission_cancelled'] and report is None:
        job['receipt_state'] = 'permission_cancelled'
        job['receipt_detail'] = (
            'a tool permission was cancelled (stopReason=cancelled / PermissionCancelled). '
            'This is NOT a completed task and NOT the user abandoning the run: one tool call '
            'was refused. Fix the allow rules and let the operator decide whether to continue '
            'the same session.')
        job['status'] = 'blocked'
        job['blocking_reason'] = job['receipt_detail']
        return
    if report is None and rc not in (None, 0):
        job['receipt_state'] = 'cli_failed'
        job['receipt_detail'] = ('the CLI process exited with rc=%s and left no result marker; '
                                 'not retrying' % rc)
        job['status'] = 'blocked'
        job['blocking_reason'] = job['receipt_detail']
        return
    if report is None:
        job['receipt_state'] = 'cli_no_unique_result'
        job['receipt_detail'] = (
            'the CLI process exited but the journal has %s usable %s marker; '
            'outcome unknown, no auto-relaunch (rc=%s)%s'
            % (('no' if hits == 0 else '%d conflicting' % hits),
               MARKER_PREFIX + job['task_id'], rc, rc_note))
        job['status'] = 'blocked'
        job['blocking_reason'] = job['receipt_detail']
        return

    # 有唯一结果标记：**也只到 review**。done 必须由外部带证据 accept。
    job['report'] = report
    fields = report if isinstance(report, dict) else {}
    job['receipt_state'] = 'durable_ok'
    job['receipt_detail'] = ('process exited (rc=%s) and the journal carries one unique '
                             'result marker; self-reported only, still needs accept%s'
                             % (rc, rc_note))
    job['status'] = 'blocked' if fields.get('status') == 'blocked' else 'review'
    job['finished_at'] = now()
    job['self_reported_at'] = now()
    job['blocking_reason'] = (one_line(fields.get('blocking_reason') or '', 200)
                              or job.get('blocking_reason', ''))


def cli_pause(job, root):
    """暂停一个 grok-cli 任务。

    默认只做一件事：**下一轮不再派**，并在任务上记一句话。不打断当前这一轮 ——
    headless CLI 没有安全的输入通道，我们也做不到实时 checkpoint，别承诺做不到的事。

    只有任务里显式写了 `cli.graceful_cancel: true` 才会发 CLI 官方的 SIGINT，
    而且**三个条件缺一不可**：是本调度启动的（owns_process）、身份当场核验为 alive、
    只发这一次。身份未知一律不发。永不 SIGKILL，日志一律保留。
    """
    if job.get('pause_notice_sent') or job['status'] != 'running':
        return False
    job['pause_requested_at'] = now()
    job['pause_notice_sent'] = True
    if not ((job.get('cli') or {}).get('graceful_cancel') and job.get('owns_process')):
        job['pause_note'] = ('paused: no further rounds will be dispatched for this owner. '
                             'The current CLI turn is NOT interrupted (headless CLI has no safe '
                             'composer, and this dispatcher cannot checkpoint mid-turn).')
        return True
    if probe_cli(job) != 'alive':
        job['pause_note'] = ('paused: the CLI process identity could not be confirmed, so no '
                             'signal was sent. No further rounds will be dispatched.')
        return True
    try:
        os.kill(int(job['cli_pid']), signal.SIGINT)      # 官方的 graceful cancel
    except OSError as exc:
        job['pause_note'] = 'paused: SIGINT could not be delivered (%s); no further signals' % exc
        return True
    job['pause_signal'] = 'SIGINT'
    job['pause_note'] = ('paused: sent one SIGINT to our own verified pid %s (the CLI\'s own '
                         'graceful cancel). Never SIGKILL; the journal is kept as-is.'
                         % job.get('cli_pid'))
    return True


def cli_reclaim(job, root, queue):
    """守护重启后把自己启动过的 CLI 任务认回来 —— **绝不因为"没看到 pid"就重跑一遍**。"""
    if not is_cli(job) or job['status'] != 'running' or not job.get('cli_token'):
        return
    if probe_cli(job) == 'alive':
        return
    found = find_by_token(job['cli_token'])
    if isinstance(found, int):
        line = proc_line(found)
        job['cli_pid'] = found
        job['cli_birth'] = '' if line in (None, 'unknown') else line
        job['receipt_detail'] = 'reclaimed pid %d by launch token after a controller restart' % found
    elif found == 'unknown':
        job['receipt_state'] = 'unknown'
        job['receipt_detail'] = ('cannot scan the process table to reclaim this run; '
                                 'outcome unknown, no auto-relaunch')


# ---------------------------------------------------------------- STATUS

# 显示层上限。原始 report 一个字不删地留在 queue.json 的 job['report'] 里，
# 这里只决定 STATUS.md / STATUS.json 上摘要显示多少。
DISPLAY_ITEMS = 6
DISPLAY_WIDTH = 120


def one_line(value, width=DISPLAY_WIDTH):
    """任何对象 -> 一行可显示的短文本。

    只做 str() / json.dumps()，**不取下标、不切片、不格式化、不求值、不执行**里面的内容。
    自报报告是 agent 写的，对显示层来说它是数据，不是指令。
    """
    if isinstance(value, str):
        text = value
    else:
        try:
            text = json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
        except (TypeError, ValueError):
            try:
                text = repr(value)
            except Exception:                                        # noqa: BLE001
                text = '<unrenderable %s>' % type(value).__name__
    text = ' '.join(str(text).replace('\r', ' ').replace('\n', ' ').replace('\t', ' ').split())
    return text[:width] + ('…' if len(text) > width else '')


def as_text_list(value, limit=DISPLAY_ITEMS, width=DISPLAY_WIDTH):
    """把自报的汇总字段归一成短文本列表。**只管显示，不改原始报告。**

    约定里 tests / screenshots 是列表，但实际接力中 agent 会写成对象、字符串、
    数字甚至 null —— C04 之前 `tests[:6]` 直接在一个 dict 上炸掉，把 watch 打死了
    （Python 3.12 报 KeyError、更早的版本报 TypeError: unhashable type: slice，
    两种都是致命的）。这里对任何类型都给得出结果，给不出就如实写成一行占位文本。

    条数超出上限时**不静默丢弃**：末尾补一条"另有 N 项"，提醒去看完整 report。
    """
    if value is None:
        return []
    if isinstance(value, str):
        items = [value] if value.strip() else []
    elif isinstance(value, dict):
        try:
            pairs = sorted(value.items(), key=lambda kv: one_line(kv[0], 60))
        except Exception:                                            # noqa: BLE001
            pairs = list(value.items())
        items = ['%s: %s' % (one_line(k, 60), one_line(v, width)) for k, v in pairs]
    elif isinstance(value, (list, tuple)):
        items = list(value)
    elif isinstance(value, (set, frozenset)):
        items = sorted(value, key=lambda x: one_line(x, width))
    else:
        items = [value]
    out = [one_line(x, width) for x in items[:max(0, int(limit))]]
    out = [x for x in out if x != '']
    extra = len(items) - max(0, int(limit))
    if extra > 0:
        out.append('…（另有 %d 项，完整内容见 report）' % extra)
    return out


def safe_get(obj, key, default=None):
    """取字段时连取值本身出错都兜住 —— 兜底行不能用会再炸一次的取法。"""
    try:
        if isinstance(obj, dict):
            return dict.get(obj, key, default)     # 绕开被覆盖的 .get
        return getattr(obj, key, default)
    except Exception:                                                # noqa: BLE001
        return default


def status_row(job):
    """单条任务的脱敏摘要行。**这个函数不允许抛异常** —— 一条报告畸形不能连累其他任务。"""
    report = job.get('report')
    if not isinstance(report, dict):
        # agent 把标记后面写成了数组/字符串/数字：原件已经留在 job['report']，
        # 这里只如实标注"报告不是对象"，不去猜它想说什么。
        note = '' if report is None else 'report is not an object: ' + one_line(report)
        report, row_note = {}, note
    else:
        row_note = ''
    row = {
        'task_id': one_line(job.get('task_id'), 80), 'owner': one_line(job.get('owner'), 40),
        'status': one_line(job.get('status'), 40),
        'receipt_state': one_line(job.get('receipt_state', 'none'), 40),
        'agent_state': job.get('agent_state'),
        'transcript_read_mode': job.get('transcript_read_mode'),
        'commit': one_line(report.get('commit', ''), 80),
        'branch': one_line(report.get('branch', job.get('branch', '')), 80),
        'tests': as_text_list(report.get('tests')),
        'screenshots': (as_text_list(report.get('screenshots'))
                        or as_text_list(report.get('screenshot'))),
        'blocking_reason': one_line(job.get('blocking_reason') or '', 200),
        'attention': one_line(job.get('attention') or '', 200),
        'accepted_at': job.get('accepted_at', ''),
        'report_kind': type(job.get('report')).__name__ if job.get('report') is not None else '',
        'self_reported': bool(job.get('report')),
        'transport': one_line(job.get('transport') or 'cockpit', 20),
    }
    if is_cli(job):
        # 一行人话，够人判断就行：谁在跑、是新开还是续用、我们能不能对它发信号。
        row['cli'] = {
            'pid': job.get('cli_pid'), 'probe': one_line(job.get('cli_probe') or '', 20),
            'session_mode': one_line(job.get('cli_session_mode') or '', 20),
            'session_id': one_line(job.get('cli_session_id') or '', 64),
            'rc': job.get('cli_rc'), 'ours': bool(job.get('owns_process')),
            'journal': one_line(job.get('journal') or '', 200),
            'summary': one_line(job.get('receipt_detail') or '', 200),
        }
        if job.get('pause_note'):
            row['cli']['pause'] = one_line(job['pause_note'], 200)
    if row_note:
        row['report_note'] = row_note
    return row


def render_status(queue, root, hub):
    """脱敏摘要：当前任务 / 下一项 / 提交 / 实测 / 截图 / 阻塞。
    完整提示词与转录只留在 logs/（0600），这里一个字都不放。"""
    rows = []
    try:
        jobs = sorted(queue['jobs'].values(),
                      key=lambda j: one_line(safe_get(j, 'created_at', ''), 40))
    except Exception:                                                # noqa: BLE001
        jobs = list(safe_get(queue, 'jobs', {}).values())
    for job in jobs:
        try:
            rows.append(status_row(job))
        except Exception as exc:                                     # noqa: BLE001
            # 一条任务渲染不出来，不能让整份 STATUS（和 watch）跟着完蛋。
            rows.append({'task_id': one_line(safe_get(job, 'task_id', '?'), 80),
                         'owner': one_line(safe_get(job, 'owner', ''), 40),
                         'status': one_line(safe_get(job, 'status', 'unknown'), 40),
                         'receipt_state': 'unknown', 'agent_state': None,
                         'transcript_read_mode': None, 'commit': '', 'branch': '',
                         'tests': [], 'screenshots': [], 'blocking_reason': '',
                         'attention': '', 'accepted_at': '', 'self_reported': False,
                         'render_error': '%s: %s' % (type(exc).__name__, one_line(exc, 160))})
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
    if any(r.get('render_error') for r in rows):
        lines.insert(-1, '- render_errors: %d 条任务的摘要渲染失败（原始 report 未改动，见 queue.json）'
                     % sum(1 for r in rows if r.get('render_error')))
    for r in rows:
        lines.append('## %s (%s)' % (r['task_id'], r['owner']))
        if r.get('render_error'):
            lines.append('- render_error: %s' % r['render_error'])
        if r.get('report_note'):
            lines.append('- report_note: %s' % r['report_note'])
        lines.append('- status: %s / receipt: %s / agent: %s / transcript: %s'
                     % (r['status'], r['receipt_state'], r['agent_state'], r['transcript_read_mode']))
        if r.get('cli'):
            c = r['cli']
            lines.append('- cli: pid=%s probe=%s %s session=%s rc=%s ours=%s'
                         % (c['pid'], c['probe'], c['session_mode'],
                            c['session_id'] or '-', c['rc'], c['ours']))
            lines.append('- cli-note: %s' % (c['summary'] or '-'))
            if c.get('pause'):
                lines.append('- cli-pause: %s' % c['pause'])
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


def record_round_error(root, exc):
    """把一轮的异常如实记到私有日志里。**不吞掉、也不让它停掉守护。**"""
    try:
        (root / 'logs').mkdir(parents=True, exist_ok=True, mode=0o700)
        line = json.dumps({'at': now(), 'type': type(exc).__name__,
                           'error': one_line(exc, 400),
                           'traceback': traceback.format_exc()[-4000:]}, ensure_ascii=False)
        path = root / 'logs' / 'watch-errors.jsonl'
        with path.open('a', encoding='utf-8') as fh:
            fh.write(line + '\n')
        os.chmod(path, 0o600)
    except OSError:
        pass


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
    errors = 0

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
            except Exception as exc:                                 # noqa: BLE001
                # 最后一道网：任何没预料到的输入（畸形报告、不可渲染的元数据……）
                # 只能毁掉这一轮，**不能**让守护整个退出、更不能丢队列。
                # 注意 queue.json 的写入在 try 内且在出错点之后，所以这里不会写回半份队列。
                errors += 1
                round_note = 'round error: %s: %s' % (type(exc).__name__, one_line(exc, 160))
                record_round_error(root, exc)
            info = read(root / 'watch.json', {}) or {}
            info.update(heartbeat=now(), last_round=round_note, skipped_rounds=skipped,
                        error_rounds=errors)
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

COMMON_FIELDS = ('task_id', 'owner', 'objective', 'allowed_paths', 'baseline_sha',
                 'dependencies', 'acceptance', 'workdir', 'branch', 'prompt_file')
# Cockpit 通道还要会话身份；grok-cli 通道要的是 cli 声明（见 cli_spec）。
COCKPIT_FIELDS = ('device_id', 'session_id', 'session_cwd')
REQUIRED_FIELDS = COMMON_FIELDS + COCKPIT_FIELDS


def cmd_submit(queue, job_file):
    job = read(job_file)
    if job is None:
        raise ValueError('job file is not readable JSON')
    need = COMMON_FIELDS + (() if is_cli(job) else COCKPIT_FIELDS)
    for field in need:
        if field not in job:
            raise ValueError('missing task field: ' + field)
    if job.get('transport') not in (None, 'cockpit', CLI_TRANSPORT):
        raise ValueError('unknown transport: ' + str(job.get('transport')))
    if job['owner'] not in ('claude', 'grok') or not re.fullmatch(r'[A-Z0-9_]+', job['task_id']):
        raise ValueError('owner/task_id rejected')
    if job['task_id'] in queue['jobs']:
        raise ValueError('task already exists; use a new revision ID')
    if not Path(job['prompt_file']).is_file():
        raise ValueError('prompt_file does not exist')
    if is_cli(job):
        spec = cli_spec(job)
        # 同一个会话 + 同一份提示词，只要还在跑 / 还没验收，就**不再派第二遍**。
        # `--resume` 只是接着聊，它不会恢复代码快照，也不该被当成"重跑一次"。
        psha = sha(Path(job['prompt_file']).read_bytes())
        for other in queue['jobs'].values():
            if not is_cli(other) or other['status'] in ('done', 'rejected'):
                continue
            if (other.get('cli_session_id') or (other.get('cli') or {}).get('session_id')) \
                    == spec.get('session_id') and other.get('prompt_sha') == psha:
                raise ValueError('the same prompt is already live on that CLI session (%s); '
                                 'resume continues a conversation, it does not re-run a task'
                                 % other['task_id'])
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
