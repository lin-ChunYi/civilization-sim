#!/usr/bin/env python3
"""ops/dispatch.py 的定向 fixture 测试。

全部在**临时目录**里造一个假 hub（outbox / transcript / snapshot），
不碰本机任何真实会话、真实 outbox、真实 Cockpit。每条都是有鉴别力的：
把对应的防护去掉就会红。

用法：python3 ops/test_dispatch.py ; echo $?
"""
import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import dispatch as D  # noqa: E402

DISPATCH = str(Path(__file__).resolve().parent / 'dispatch.py')
DEV, SES, CWD = 'dev-1', 'ses-1', '/tmp/project'
MARKER = D.MARKER_PREFIX + 'T1'


def snapshot(state='waiting', pending=None, owner='claude', online=True):
    return {'devices': [{'device_id': DEV, 'online': online, 'controllable': True,
                         'sessions': [{'session_id': SES, 'source': owner, 'cwd': CWD,
                                       'state': state, 'pending': pending or [],
                                       'claude_pid': 4242}]}]}


def claude_rec(role, text):
    if role == 'assistant':
        return {'type': 'assistant', 'message': {'content': [{'type': 'text', 'text': text}]}}
    return {'type': 'user', 'message': {'content': [{'type': 'text', 'text': text}]}}


def grok_rec(role, text):
    kind = 'agent_message_chunk' if role == 'assistant' else 'user_message_chunk'
    return {'params': {'update': {'sessionUpdate': kind, 'content': {'text': text}}}}


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix='dispatch-test-'))
        self.root = self.tmp / 'state'
        self.hub = self.tmp / 'hub'
        (self.hub / 'outbox').mkdir(parents=True)
        self.tpath = self.hub / 'transcript' / DEV / (SES + '.jsonl')
        self.tpath.parent.mkdir(parents=True)
        self.tpath.write_text('', encoding='utf-8')
        self.prompt = self.tmp / 'prompt.txt'
        # 提示词里**故意**带上标记模板：这正是最容易被误判成完成的东西
        self.prompt.write_text('请做 T1。完成后单行回复 ' + MARKER + ' {"status":"done"}\n',
                               encoding='utf-8')
        self.write_snapshot(snapshot())
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def write_snapshot(self, snap):
        (self.hub / 'snapshot.json').write_text(json.dumps(snap), encoding='utf-8')
        os.utime(self.hub / 'snapshot.json', None)

    def append(self, records):
        with self.tpath.open('a', encoding='utf-8') as fh:
            for rec in records:
                fh.write(json.dumps(rec, ensure_ascii=False) + '\n')

    def job(self, owner='claude', task='T1'):
        return {'task_id': task, 'owner': owner, 'objective': 'o', 'allowed_paths': ['ops/'],
                'baseline_sha': 'abc', 'dependencies': [], 'acceptance': 'a',
                'workdir': CWD, 'branch': 'main', 'device_id': DEV, 'session_id': SES,
                'session_cwd': CWD, 'prompt_file': str(self.prompt)}

    def run_cli(self, *args, expect=0):
        proc = subprocess.run([sys.executable, DISPATCH, '--state-dir', str(self.root),
                               '--hub-dir', str(self.hub)] + list(args),
                              capture_output=True, text=True)
        self.assertEqual(proc.returncode, expect,
                         'cmd=%s rc=%s out=%s err=%s' % (args, proc.returncode,
                                                         proc.stdout[-400:], proc.stderr[-400:]))
        return proc

    def submit_and_dispatch(self, owner='claude'):
        jf = self.tmp / 'job.json'
        jf.write_text(json.dumps(self.job(owner)), encoding='utf-8')
        self.run_cli('submit', str(jf))
        self.run_cli('tick')
        queue = D.read(self.root / 'queue.json')
        return queue['jobs']['T1']

    def injected_text(self, task='T1'):
        """真实投递出去的文本（带 [dispatch TASK CORR8] 前缀），从命令日志里取。"""
        return D.read(self.root / 'logs' / (task + '.command.json'))['data']['text']

    def cockpit_normalized(self, text):
        """Cockpit 的 composeInjection 会把 CR/LF/Tab 折成空格
        （cockpit-cloud-hub/internal/inject/attachment.go:94）。转录里的用户记录长这样。"""
        return ' '.join(text.replace('\r', ' ').replace('\n', ' ').replace('\t', ' ').split())

    def envelopes(self):
        return sorted(p for p in (self.hub / 'outbox').glob('*.json')
                      if not p.name.endswith('.result.json'))

    def queue(self):
        return D.read(self.root / 'queue.json')


class TestMarkerEvidence(Base):
    def test_R1_prompt_marker_is_not_completion(self):
        """派工提示词本身带着标记模板；它是**用户**记录，绝不能算完成。"""
        job = self.submit_and_dispatch()
        self.assertEqual(job['status'], 'running')
        self.append([claude_rec('user', self.prompt.read_text())])
        self.run_cli('tick')
        j = self.queue()['jobs']['T1']
        self.assertEqual(j['status'], 'running', '用户提示词里的标记被当成了完成')
        self.assertIsNone(j.get('report'))

    def test_R2_only_output_after_this_dispatch_counts(self):
        """派工之前就存在的同名标记（上一轮遗留）不能算这次的完成。"""
        self.append([claude_rec('assistant', MARKER + ' {"status":"done","commit":"OLD"}')])
        job = self.submit_and_dispatch()
        self.run_cli('tick')
        j = self.queue()['jobs']['T1']
        self.assertEqual(j['status'], 'running', '派工之前的旧标记被算成了本次完成')
        self.append([claude_rec('assistant', MARKER + ' {"status":"done","commit":"NEW"}')])
        self.run_cli('tick')
        j = self.queue()['jobs']['T1']
        self.assertEqual(j['status'], 'review')
        self.assertEqual(j['report']['commit'], 'NEW')

    def test_R3_two_real_chunk_formats(self):
        """Claude 是整块 text；Grok 的同一句话会被拆成多条 chunk，必须拼回来。"""
        self.submit_and_dispatch()
        self.append([claude_rec('assistant', 'thinking...'),
                     claude_rec('assistant', MARKER + ' {"status":"done","commit":"C"}')])
        self.run_cli('tick')
        self.assertEqual(self.queue()['jobs']['T1']['report']['commit'], 'C')

        # 换一个 grok 会话，标记被拆成三段
        self.setUp()
        self.write_snapshot(snapshot(owner='grok'))
        self.submit_and_dispatch(owner='grok')
        self.append([grok_rec('assistant', MARKER + ' {"sta'),
                     grok_rec('assistant', 'tus":"done","comm'),
                     grok_rec('assistant', 'it":"G"}\n')])
        self.run_cli('tick')
        j = self.queue()['jobs']['T1']
        self.assertEqual(j['status'], 'review', '拆分的 chunk 没有被拼回来')
        self.assertEqual(j['report']['commit'], 'G')


class TestTranscriptTruncation(Base):
    def test_R4_rebinds_after_tail_rewrite(self):
        """request_transcript(tail_bytes) 会把本机文件截短重写，旧 offset 立刻失效。"""
        self.append([claude_rec('assistant', 'x' * 2000)])
        job = self.submit_and_dispatch()
        old_offset = job['transcript_offset']
        self.assertGreater(old_offset, 1000)
        # 模拟物化：只留尾部（**真实注入文本、已被 Cockpit 归一化** + 助手回答）
        self.tpath.write_text('\n'.join([
            json.dumps(claude_rec('user', self.cockpit_normalized(self.injected_text())),
                       ensure_ascii=False),
            json.dumps(claude_rec('assistant', MARKER + ' {"status":"done","commit":"R"}'),
                       ensure_ascii=False)]) + '\n', encoding='utf-8')
        self.assertLess(self.tpath.stat().st_size, old_offset)
        self.run_cli('tick')
        j = self.queue()['jobs']['T1']
        self.assertEqual(j['transcript_read_mode'], 'rebound', '截短后没有重新绑定')
        self.assertEqual(j['status'], 'review')
        self.assertEqual(j['report']['commit'], 'R')

    def test_R4b_unanchorable_transcript_is_unknown_not_done(self):
        """尾部太短、连提示词都没了：宁可报 unknown，也不拿孤零零的标记当完成。"""
        self.append([claude_rec('assistant', 'y' * 2000)])
        self.submit_and_dispatch()
        self.tpath.write_text(json.dumps(
            claude_rec('assistant', MARKER + ' {"status":"done","commit":"ORPHAN"}'),
            ensure_ascii=False) + '\n', encoding='utf-8')
        self.run_cli('tick')
        j = self.queue()['jobs']['T1']
        self.assertEqual(j['transcript_read_mode'], 'rebind-failed')
        self.assertNotEqual(j['status'], 'review', '无法锚定时把孤立标记当成了完成')
        self.assertIn('truncated', j.get('attention', ''))


class TestInjectionAnchor(Base):
    def test_R4c_grok_user_prompt_split_into_chunks(self):
        """Grok 会把用户提示词拆成多条 user chunk，拼起来才找得到投递前缀。"""
        self.write_snapshot(snapshot(owner='grok'))
        self.append([grok_rec('assistant', 'z' * 2000)])      # 先有历史，offset 才非 0
        self.submit_and_dispatch(owner='grok')
        text = self.cockpit_normalized(self.injected_text())
        tag = self.queue()['jobs']['T1']['inject_tag']
        # **把唯一 tag 本身切断**（"[dispa" / "tch T1 ..."）—— 在完整 tag 之后切是不承重的：
        # 那样即使中间多塞一个空格也照样找得到。
        cut = 6
        self.assertNotIn(tag, text[:cut])
        self.assertNotIn(tag, text[cut:2 * cut])
        self.tpath.write_text('\n'.join([
            json.dumps(grok_rec('user', text[:cut]), ensure_ascii=False),
            json.dumps(grok_rec('user', text[cut:2 * cut]), ensure_ascii=False),
            json.dumps(grok_rec('user', text[2 * cut:]), ensure_ascii=False),
            json.dumps(grok_rec('assistant', MARKER + ' {"status":"done","commit":"SPLIT"}'),
                       ensure_ascii=False)]) + '\n', encoding='utf-8')
        self.run_cli('tick')
        j = self.queue()['jobs']['T1']
        self.assertEqual(j['transcript_read_mode'], 'rebound', '拆成多条的用户提示词没能重绑定')
        self.assertEqual(j['report']['commit'], 'SPLIT')

    def test_R4d_old_dispatch_tag_is_not_reused(self):
        """上一轮派工的前缀不能给这一轮当锚点：每次投递的 [dispatch ...] 都不一样。"""
        self.append([claude_rec('assistant', 'w' * 2000)])    # 先有历史，offset 才非 0
        self.submit_and_dispatch()
        old_tag = self.queue()['jobs']['T1']['inject_tag']
        self.tpath.write_text('\n'.join([
            json.dumps(claude_rec('user', self.cockpit_normalized(old_tag + ' 旧的一轮')),
                       ensure_ascii=False),
            json.dumps(claude_rec('assistant', MARKER + ' {"status":"done","commit":"OLD"}'),
                       ensure_ascii=False)]) + '\n', encoding='utf-8')
        self.run_cli('tick')          # 这一轮的 tag 就是 old_tag，所以应当认
        self.assertEqual(self.queue()['jobs']['T1']['report']['commit'], 'OLD')
        # 换一个 corr（模拟新一轮派工）后，旧 tag 不再是锚点
        q = self.queue(); q['jobs']['T1']['inject_tag'] = '[dispatch T1 FFFFFFFF]'
        q['jobs']['T1']['status'] = 'running'; q['jobs']['T1'].pop('report', None)
        D.atomic(self.root / 'queue.json', q)
        self.run_cli('tick')
        j = self.queue()['jobs']['T1']
        self.assertEqual(j['transcript_read_mode'], 'rebind-failed', '旧 tag 被当成了本轮锚点')
        self.assertNotEqual(j['status'], 'review')


class TestReceipts(Base):
    def test_R5_receipt_states_are_distinguished(self):
        job = self.submit_and_dispatch()
        corr = job['corr_id']
        out = self.hub / 'outbox'
        self.assertEqual(self.queue()['jobs']['T1']['receipt_state'], 'queued')

        (out / (corr + '.ack.json')).write_text('{"ack":true}', encoding='utf-8')
        self.run_cli('tick')
        self.assertEqual(self.queue()['jobs']['T1']['receipt_state'], 'bridge_ack')

        (out / (corr + '.result.json')).write_text('{"ok":true}', encoding='utf-8')
        self.run_cli('tick')
        j = self.queue()['jobs']['T1']
        self.assertEqual(j['receipt_state'], 'durable_ok')
        self.assertEqual(j['status'], 'running', 'durable_ok 被误当成任务完成')

        (out / (corr + '.result.json')).write_text('{"ok":false,"error":"nope"}', encoding='utf-8')
        self.run_cli('tick')
        j = self.queue()['jobs']['T1']
        self.assertEqual(j['receipt_state'], 'failed')
        self.assertEqual(j['status'], 'blocked')

        (out / (corr + '.result.json')).write_text('{"ok":false,"error":"usage limit reached"}',
                                                   encoding='utf-8')
        self.run_cli('tick')
        self.assertEqual(self.queue()['jobs']['T1']['receipt_state'], 'quota_blocked')

    def test_R5b_no_receipt_becomes_unknown_not_failure(self):
        job = self.submit_and_dispatch()
        (self.hub / 'outbox' / (job['corr_id'] + '.json')).unlink()   # 桥接取走了信封
        q = self.queue()
        q['jobs']['T1']['started_epoch'] = time.time() - D.UNKNOWN_AFTER_SEC - 5
        D.atomic(self.root / 'queue.json', q)
        self.run_cli('tick')
        j = self.queue()['jobs']['T1']
        self.assertEqual(j['receipt_state'], 'unknown')
        self.assertIn('no auto-resend', j['blocking_reason'])


class TestStallAndUnreadable(Base):
    def test_R12_prompt_stalled_is_unknown_not_failure(self):
        """agent_prompt_stalled：文字和回车都送到了，只是没见画面推进 —— 绝不是"没执行"。"""
        job = self.submit_and_dispatch()
        (self.hub / 'outbox' / (job['corr_id'] + '.result.json')).write_text(
            '{"ok":false,"error":"agent_prompt_stalled"}', encoding='utf-8')
        self.run_cli('tick')
        j = self.queue()['jobs']['T1']
        self.assertEqual(j['receipt_state'], 'unknown', 'stalled 被误判成 failed')
        self.assertFalse(j['receipt_safe_requeue'])
        self.run_cli('requeue', 'T1', expect=1)          # 免确认重排 = 重复派工，必须拦住
        self.run_cli('requeue', 'T1', '--acknowledge-duplicate-risk')

    def test_R13_half_written_receipt_is_unknown(self):
        """回执写了一半（JSON 解析不了）不是失败，是未知。"""
        job = self.submit_and_dispatch()
        (self.hub / 'outbox' / (job['corr_id'] + '.result.json')).write_text(
            '{"ok":tr', encoding='utf-8')
        self.run_cli('tick')
        j = self.queue()['jobs']['T1']
        self.assertEqual(j['receipt_state'], 'unknown', '半写回执被误判成 failed')
        self.assertIn('unreadable', j['receipt_detail'])
        self.run_cli('requeue', 'T1', expect=1)

    def test_R14_overdue_reaches_unknown_even_with_ack_or_envelope(self):
        """outbox 里还留着 .ack 或旧信封，也必须能按时判 unknown，不能永远停在 queued。"""
        for leftover in ('.ack.json', '.json'):
            self.setUp()
            job = self.submit_and_dispatch()
            corr = job['corr_id']
            if leftover == '.ack.json':
                (self.hub / 'outbox' / (corr + '.ack.json')).write_text('{"ack":1}',
                                                                       encoding='utf-8')
            q = self.queue()
            q['jobs']['T1']['started_epoch'] = time.time() - D.UNKNOWN_AFTER_SEC - 5
            D.atomic(self.root / 'queue.json', q)
            self.run_cli('tick')
            j = self.queue()['jobs']['T1']
            self.assertEqual(j['receipt_state'], 'unknown',
                             '留着 %s 就永远到不了 unknown' % leftover)

    def test_R20_only_provably_undelivered_failure_is_safe_to_requeue(self):
        job = self.submit_and_dispatch()
        out = self.hub / 'outbox' / (job['corr_id'] + '.result.json')
        out.write_text('{"ok":false,"error":"session not found"}', encoding='utf-8')
        self.run_cli('tick')
        j = self.queue()['jobs']['T1']
        self.assertEqual(j['receipt_state'], 'failed')
        self.assertTrue(j['receipt_safe_requeue'], '确证未送达的失败应当可以直接重排')
        self.run_cli('requeue', 'T1')                    # 无需承认风险
        # 原因不明的失败 -> 不给免确认
        self.setUp()
        job = self.submit_and_dispatch()
        (self.hub / 'outbox' / (job['corr_id'] + '.result.json')).write_text(
            '{"ok":false,"error":"something odd happened"}', encoding='utf-8')
        self.run_cli('tick')
        self.assertFalse(self.queue()['jobs']['T1']['receipt_safe_requeue'])
        self.run_cli('requeue', 'T1', expect=1)


class TestNoDuplicateDispatch(Base):
    def test_R6_never_resends(self):
        job = self.submit_and_dispatch()
        first = self.envelopes()
        self.assertEqual(len(first), 1)
        for _ in range(3):
            self.run_cli('tick')
        self.assertEqual(self.envelopes(), first, '重复 tick 造成了重复派发')

        # 模拟"桥接取走了信封、但始终没有落地回执"，再模拟重启：绝不能自动重投
        first[0].unlink()
        q = self.queue()
        q['jobs']['T1']['started_epoch'] = time.time() - D.UNKNOWN_AFTER_SEC - 5
        D.atomic(self.root / 'queue.json', q)
        self.run_cli('tick')
        self.run_cli('tick')                      # 相当于重启后再跑两轮
        self.assertEqual(self.envelopes(), [], '结果未知的任务被自动重发了')
        self.assertEqual(self.queue()['jobs']['T1']['receipt_state'], 'unknown')

        # 未知状态下重排必须显式承认重复投递风险
        self.run_cli('requeue', 'T1', expect=1)
        self.run_cli('requeue', 'T1', '--acknowledge-duplicate-risk')
        self.assertEqual(self.queue()['jobs']['T1']['status'], 'pending')


class TestPauseAndLocks(Base):
    def test_R7_second_watcher_is_refused(self):
        self.run_cli('tick')
        lock = (self.root / 'watch.lock').open('a+')
        import fcntl
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        proc = subprocess.run([sys.executable, DISPATCH, '--state-dir', str(self.root),
                               '--hub-dir', str(self.hub), 'watch', '--once'],
                              capture_output=True, text=True)
        lock.close()
        self.assertNotEqual(proc.returncode, 0, '第二个 watcher 没有被锁挡住')
        self.assertIn('watch lock', proc.stderr + proc.stdout)

    def test_R8_pause_blocks_dispatch_and_notifies_once(self):
        self.submit_and_dispatch()
        before = len(self.envelopes())
        self.run_cli('pause')
        envs = self.envelopes()
        self.assertEqual(len(envs), before + 1, '暂停没有发出协作式通知')
        texts = [json.loads(p.read_text())['data']['text'] for p in envs]
        self.assertTrue(any('下一个安全点' in t for t in texts))
        self.run_cli('pause')
        self.run_cli('tick')
        self.assertEqual(len(self.envelopes()), before + 1, '暂停通知被重复发送')

        # 暂停期间不得派出新任务
        jf = self.tmp / 'job2.json'
        j2 = self.job(task='T2'); j2['owner'] = 'grok'
        jf.write_text(json.dumps(j2), encoding='utf-8')
        self.run_cli('submit', str(jf))
        self.run_cli('tick')
        self.assertEqual(self.queue()['jobs']['T2']['status'], 'pending', '暂停时仍然派出了新任务')
        self.run_cli('resume')
        self.assertFalse(self.queue()['paused'])


class TestWatcherSafety(Base):
    def test_R15_stop_refuses_unverified_pid(self):
        """PID 被复用时绝不能发信号：构造一个无关进程占住记录里的 pid。"""
        victim = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(30)'])
        self.addCleanup(victim.kill)
        self.run_cli('tick')
        D.atomic(self.root / 'watch.json', {'pid': victim.pid, 'token': 'stale-token',
                                            'started_at': D.now(), 'state_dir': str(self.root)})
        out = json.loads(self.run_cli('stop').stdout)
        self.assertFalse(out['stopped'])
        self.assertFalse(out['signalled'], '对身份不明的 pid 发了信号')
        self.assertIn('PID reuse', out['reason'])
        time.sleep(0.3)
        self.assertIsNone(victim.poll(), '无关进程被误杀了')

    def test_R16_watcher_survives_lock_contention(self):
        """status/submit/pause 正常占锁时，守护要么等、要么跳过这一轮，**都得继续活着**。"""
        import fcntl
        # (a) 正常争用：守护等一会儿就拿到锁，必须活着并继续收轮
        self.run_cli('start', '--interval', '1')
        self.addCleanup(lambda: self.run_cli('stop'))
        pid = D.read(self.root / 'watch.json')['pid']
        with (self.root / 'controller.lock').open('a+') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            time.sleep(3)
            os.kill(int(pid), 0)                      # 占锁期间没被"锁"死
        before = (D.read(self.root / 'watch.json', {}) or {}).get('heartbeat')
        deadline = time.time() + 10
        while time.time() < deadline:
            info = D.read(self.root / 'watch.json', {}) or {}
            if info.get('heartbeat') != before and info.get('last_round') == 'ok':
                break
            time.sleep(0.3)
        self.assertTrue(D.watcher_alive(self.root), '守护被一次正常占锁弄退出了')
        self.assertEqual((D.read(self.root / 'watch.json') or {}).get('last_round'), 'ok',
                         '让开锁之后守护没有恢复收轮')

        # (b) 等不到锁：必须记一轮 skipped 并正常退出（而不是 SystemExit 把守护打死）
        self.run_cli('stop')
        with (self.root / 'controller.lock').open('a+') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            proc = subprocess.run([sys.executable, DISPATCH, '--state-dir', str(self.root),
                                   '--hub-dir', str(self.hub), 'watch', '--once',
                                   '--lock-wait', '1'], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0,
                         '拿不到锁时守护直接退出了：%s' % (proc.stderr[-300:]))
        info = D.read(self.root / 'watch.json', {}) or {}
        self.assertGreaterEqual(info.get('skipped_rounds', 0), 1, '没有记录被跳过的轮次')
        self.assertIn('skipped', info.get('last_round', ''))


class TestQueueIntegrity(Base):
    def test_R17_corrupt_queue_is_preserved_not_overwritten(self):
        self.submit_and_dispatch()
        original = (self.root / 'queue.json').read_text(encoding='utf-8')
        (self.root / 'queue.json').write_text(original[:len(original) // 2], encoding='utf-8')
        broken = (self.root / 'queue.json').read_text(encoding='utf-8')
        out = self.run_cli('status', expect=2)
        self.assertIn('unreadable', out.stdout)
        self.assertEqual((self.root / 'queue.json').read_text(encoding='utf-8'), broken,
                         '损坏的队列被空状态覆盖了')
        self.assertTrue(list(self.root.glob('queue.corrupt.*.json')), '没有保留原件')
        self.run_cli('tick', expect=2)        # 派发也必须被拦住


class TestReworkLoop(Base):
    def test_R18_review_blocks_next_task_but_allows_controlled_rework(self):
        self.submit_and_dispatch()
        self.append([claude_rec('assistant', MARKER + ' {"status":"done","commit":"V1"}')])
        self.run_cli('tick')
        self.assertEqual(self.queue()['jobs']['T1']['status'], 'review')

        # 普通的下一个任务：仍然要等 accept，不能越过验收
        nxt = self.job(task='T2'); jf = self.tmp / 'j2.json'
        jf.write_text(json.dumps(nxt), encoding='utf-8'); self.run_cli('submit', str(jf))
        self.run_cli('tick')
        self.assertEqual(self.queue()['jobs']['T2']['status'], 'pending',
                         '没验收就把下一个任务派出去了')

        # 返工任务：明确 rework_of 指向那条 review，才放行
        rw = self.job(task='T1_R1'); rw['rework_of'] = 'T1'
        jf2 = self.tmp / 'j3.json'; jf2.write_text(json.dumps(rw), encoding='utf-8')
        self.run_cli('submit', str(jf2))
        self.run_cli('tick')
        self.assertEqual(self.queue()['jobs']['T1_R1']['status'], 'running',
                         '合法的返工闭环被拦住了')

    def test_R18c_only_one_rework_per_tick(self):
        """两条都指向同一个 review 的返工任务同时 pending 时，**一个 tick 只能派一份**。
        否则同一个会话会在同一轮里收到两份活。"""
        self.submit_and_dispatch()
        self.append([claude_rec('assistant', MARKER + ' {"status":"done"}')])
        self.run_cli('tick')
        self.assertEqual(self.queue()['jobs']['T1']['status'], 'review')
        before = len(self.envelopes())
        for name in ('T1_R1', 'T1_R2'):
            rw = self.job(task=name); rw['rework_of'] = 'T1'
            jf = self.tmp / (name + '.json')
            jf.write_text(json.dumps(rw), encoding='utf-8')
            self.run_cli('submit', str(jf))
        self.run_cli('tick')
        jobs = self.queue()['jobs']
        running = [t for t in ('T1_R1', 'T1_R2') if jobs[t]['status'] == 'running']
        self.assertEqual(len(running), 1, '同一个 tick 派出了两份返工：%s' % running)
        self.assertEqual(len(self.envelopes()), before + 1, '同一轮投了两个信封')
        # 下一轮也不能补派：owner 已经被刚派出的那条占住
        self.run_cli('tick')
        self.assertEqual(len(self.envelopes()), before + 1)

    def test_R18d_running_job_holds_the_owner(self):
        """同 owner 已经有任务在跑时，指向 review 的返工也不能插队。"""
        self.submit_and_dispatch()                       # T1 running
        q = self.queue()
        q['jobs']['OLD'] = dict(q['jobs']['T1'], task_id='OLD', status='review',
                                corr_id=None, created_at='2020-01-01')
        D.atomic(self.root / 'queue.json', q)
        rw = self.job(task='OLD_R1'); rw['rework_of'] = 'OLD'
        jf = self.tmp / 'rw.json'; jf.write_text(json.dumps(rw), encoding='utf-8')
        self.run_cli('submit', str(jf))
        before = len(self.envelopes())
        self.run_cli('tick')
        self.assertEqual(self.queue()['jobs']['OLD_R1']['status'], 'pending',
                         '已有 running 的 owner 被返工任务插队了')
        self.assertEqual(len(self.envelopes()), before)

    def test_R18b_reject_frees_the_owner(self):
        self.submit_and_dispatch()
        self.append([claude_rec('assistant', MARKER + ' {"status":"done"}')])
        self.run_cli('tick')
        self.run_cli('reject', 'T1', '--reason', 'independent review found a defect')
        j = self.queue()['jobs']['T1']
        self.assertEqual(j['status'], 'rejected')
        self.assertIn('defect', j['reject_reason'])
        nxt = self.job(task='T2'); jf = self.tmp / 'j2.json'
        jf.write_text(json.dumps(nxt), encoding='utf-8'); self.run_cli('submit', str(jf))
        self.run_cli('tick')
        self.assertEqual(self.queue()['jobs']['T2']['status'], 'running',
                         'reject 之后 owner 没有被释放')


class TestWatcherLifecycle(Base):
    def test_R9_start_stop_is_clean(self):
        out = self.run_cli('start', '--interval', '1')
        info = json.loads(out.stdout)
        self.assertTrue(info['alive'], '守护没有起来')
        pid = D.read(self.root / 'watch.json')['pid']
        deadline = time.time() + 10
        while time.time() < deadline and not (self.root / 'STATUS.json').exists():
            time.sleep(0.2)
        self.assertTrue((self.root / 'STATUS.json').exists(), '守护没有产出 STATUS')
        stop = json.loads(self.run_cli('stop').stdout)
        self.assertTrue(stop['stopped'], '停止失败：%s' % stop)
        time.sleep(0.3)
        with self.assertRaises(OSError):
            os.kill(int(pid), 0)
        self.assertIsNotNone(D.read(self.root / 'watch.json').get('stopped_at'))
        self.assertFalse((self.root / 'stop.request').exists())
        # 停完之后没有第二个控制器在派单
        again = json.loads(self.run_cli('stop').stdout)
        self.assertFalse(again['stopped'])


class TestAcceptanceAndStatus(Base):
    def test_R10_self_report_never_reaches_done(self):
        self.submit_and_dispatch()
        self.append([claude_rec('assistant', MARKER + ' {"status":"done","commit":"ABC123"}')])
        self.run_cli('tick')
        self.assertEqual(self.queue()['jobs']['T1']['status'], 'review',
                         '自报完成直接变成了 done')
        self.run_cli('accept', 'T1', '--evidence', str(self.tmp / 'missing.txt'), expect=1)
        ev = self.tmp / 'evidence.txt'; ev.write_text('codex verified', encoding='utf-8')
        self.run_cli('accept', 'T1', '--evidence', str(ev))
        j = self.queue()['jobs']['T1']
        self.assertEqual(j['status'], 'done')
        self.assertTrue(j['acceptance_evidence'].endswith('evidence.txt'))

    def test_R19_status_keeps_all_screenshots(self):
        """Grok 实际会报 screenshots[]（复数）；只读单数会漏掉已有截图。"""
        self.submit_and_dispatch()
        self.append([claude_rec('assistant', MARKER + ' {"status":"done",'
                                             '"screenshots":["a.png","b.png"]}')])
        self.run_cli('tick')
        md = (self.root / 'STATUS.md').read_text(encoding='utf-8')
        js = json.loads((self.root / 'STATUS.json').read_text(encoding='utf-8'))
        self.assertIn('a.png', md)
        self.assertIn('b.png', md, 'screenshots[] 被漏掉了')
        self.assertEqual(js['jobs'][0]['screenshots'], ['a.png', 'b.png'])

    def test_R11_status_is_redacted(self):
        self.submit_and_dispatch()
        self.append([claude_rec('assistant', 'secret working notes\n'
                                             + MARKER + ' {"status":"done","commit":"ABC123",'
                                                        '"tests":["pytest -> exit=0"]}')])
        self.run_cli('tick')
        md = (self.root / 'STATUS.md').read_text(encoding='utf-8')
        js = json.loads((self.root / 'STATUS.json').read_text(encoding='utf-8'))
        self.assertIn('ABC123', md)
        self.assertIn('pytest -> exit=0', md)
        self.assertNotIn('secret working notes', md, 'STATUS 泄露了转录正文')
        self.assertNotIn('请做 T1', md, 'STATUS 泄露了提示词')
        self.assertNotIn('secret working notes', json.dumps(js, ensure_ascii=False))
        self.assertIn('review', json.dumps(js, ensure_ascii=False))
        # 完整内容只留在 0600 的私有日志里
        log = self.root / 'logs' / 'T1.assistant.txt'
        self.assertIn('secret working notes', log.read_text(encoding='utf-8'))
        self.assertEqual(oct(log.stat().st_mode)[-3:], '600')


# ---------------------------------------------------------------- 自报报告的类型边界
# C04 的由来：C03_HISTORY 的真实报告把约定里是列表的 tests 写成了对象，
# 旧的 render_status 在 `tests[:6]` 上直接炸掉，本机 watch 整个退出（07:06 UTC）。
# 这里用**那份真实报告的结构**做 fixture。
C03_REPORT = {
    "status": "done", "branch": "main",
    "commit": "41683564a5e0273b66687b5b933a7f5af629157f",
    "tests": {
        "observer": "160 PASS / 0 FAIL / 1 UNCOVERED of 161",
        "ops": "27 PASS",
        "new_groups": ["O28 natural preset", "O29 isolated constructed"],
        "uncovered": "O28m 自然预置内无群体消失，前提缺失；路径由 O29b/c 覆盖",
    },
    "handoff": "docs/OBS-01-HANDOFF-HISTORY.md", "blocking_reason": "",
}
SES2 = 'ses-2'


def two_sessions():
    snap = snapshot()
    snap['devices'][0]['sessions'].append(
        {'session_id': SES2, 'source': 'grok', 'cwd': CWD, 'state': 'waiting',
         'pending': [], 'claude_pid': 4343})
    return snap


class TestReportTypeBoundary(Base):
    """自报报告是 agent 写的**数据**，不是约定好的结构，更不是指令。
    显示层必须对任何类型都给得出结果，且一条畸形报告不能连累其他任务或守护本身。"""

    def marker(self, payload, task='T1'):
        return D.MARKER_PREFIX + task + ' ' + json.dumps(payload, ensure_ascii=False)

    def test_R21_dict_tests_does_not_kill_status(self):
        """真实 C03 报告：tests 是对象。旧实现在这里抛异常（3.12 是 KeyError，
        更早的版本是 TypeError: unhashable type: slice），两种都会打死 watch。"""
        self.submit_and_dispatch()
        self.append([claude_rec('assistant', self.marker(C03_REPORT))])
        self.run_cli('tick')                       # 旧实现在这一步非零退出
        j = self.queue()['jobs']['T1']
        self.assertEqual(j['status'], 'review', '自报完成被直接当成 done')
        self.assertEqual(j['report'], C03_REPORT, '原始 report 被改动了')
        js = json.loads((self.root / 'STATUS.json').read_text(encoding='utf-8'))
        row = js['jobs'][0]
        self.assertTrue(row['tests'], 'tests 是对象时摘要变成了空')
        joined = ' | '.join(row['tests'])
        self.assertIn('160 PASS / 0 FAIL / 1 UNCOVERED of 161', joined)
        self.assertIn('27 PASS', joined)
        self.assertIn('UNCOVERED', joined, '把 1 项 UNCOVERED 抹掉了')
        md = (self.root / 'STATUS.md').read_text(encoding='utf-8')
        self.assertIn('UNCOVERED', md)
        self.assertIn('stop at "review"', js['acceptance'])
        self.assertTrue(row['self_reported'])

    def test_R21b_odd_types_are_all_renderable(self):
        """tests / screenshots 等可选汇总字段写成字符串、数字、null、嵌套对象都不能炸。"""
        cases = [
            ('string', {"status": "done", "tests": "python3 x.py -> exit=0"}),
            ('int', {"status": "done", "tests": 27}),
            ('float', {"status": "done", "tests": 1.5}),
            ('bool', {"status": "done", "tests": True}),
            ('null', {"status": "done", "tests": None}),
            ('empty-list', {"status": "done", "tests": []}),
            ('empty-dict', {"status": "done", "tests": {}}),
            ('nested', {"status": "done", "tests": [{"cmd": "a", "exit": 0}, None, 3]}),
            ('deep', {"status": "done", "tests": {"a": {"b": {"c": [1, 2, 3]}}}}),
            ('bad-optional', {"status": "done", "commit": {"sha": "X"}, "branch": ["main"],
                              "screenshots": {"ui": "a.png"}, "blocking_reason": {"why": "z"}}),
            ('screenshot-int', {"status": "done", "screenshots": 5}),
            ('no-marker-fields', {"status": "done"}),
        ]
        for name, payload in cases:
            with self.subTest(case=name):
                tmp = Path(tempfile.mkdtemp(prefix='rt-'))
                self.addCleanup(shutil.rmtree, tmp, True)
                queue = {'jobs': {'X': {'task_id': 'X', 'owner': 'claude', 'status': 'review',
                                        'created_at': '2026-01-01', 'report': payload,
                                        'dependencies': []}}}
                summary = D.render_status(queue, tmp, self.hub)      # 不许抛
                row = summary['jobs'][0]
                self.assertIsInstance(row['tests'], list)
                self.assertIsInstance(row['screenshots'], list)
                for item in row['tests'] + row['screenshots']:
                    self.assertIsInstance(item, str)
                    self.assertNotIn('\n', item)
                self.assertIsInstance(row['commit'], str)
                self.assertIsInstance(row['branch'], str)
                json.dumps(summary)                                  # STATUS.json 必须可序列化
                self.assertEqual(queue['jobs']['X']['report'], payload, '原始报告被显示层改了')

    def test_R21c_non_object_report_is_not_treated_as_fields(self):
        """队列里的 report 不是对象时（手改过、或将来换了格式），显示层不能对它调 .get()。"""
        for payload in ('done', ['a', 'b'], 7, True):
            with self.subTest(report=payload):
                tmp = Path(tempfile.mkdtemp(prefix='rt2-'))
                self.addCleanup(shutil.rmtree, tmp, True)
                queue = {'jobs': {'X': {'task_id': 'X', 'owner': 'claude', 'status': 'review',
                                        'created_at': '2026-01-01', 'report': payload,
                                        'dependencies': []}}}
                summary = D.render_status(queue, tmp, self.hub)
                row = summary['jobs'][0]
                self.assertIn('report is not an object', row.get('report_note', ''))
                self.assertEqual(row['tests'], [])
                self.assertEqual(queue['jobs']['X']['report'], payload)

    def test_R21d_unrenderable_job_does_not_hide_the_others(self):
        """一条任务的元数据根本渲染不出来时，只标这一条出错，其余照常显示。"""
        tmp = Path(tempfile.mkdtemp(prefix='rt3-'))
        self.addCleanup(shutil.rmtree, tmp, True)

        class Hostile(dict):
            def get(self, *a, **k):
                raise RuntimeError('metadata blew up')

        bad = Hostile(task_id='BAD', owner='grok', status='review', created_at='2026-01-01')
        good = {'task_id': 'GOOD', 'owner': 'claude', 'status': 'review',
                'created_at': '2026-01-02', 'report': C03_REPORT, 'dependencies': []}
        summary = D.render_status({'jobs': {'BAD': bad, 'GOOD': good}}, tmp, self.hub)
        ids = [r['task_id'] for r in summary['jobs']]
        self.assertIn('GOOD', ids, '一条坏任务把其他任务的摘要也吞掉了')
        broken = [r for r in summary['jobs'] if r.get('render_error')]
        self.assertEqual(len(broken), 1)
        self.assertIn('RuntimeError', broken[0]['render_error'])
        ok_row = [r for r in summary['jobs'] if r['task_id'] == 'GOOD'][0]
        self.assertIn('UNCOVERED', ' | '.join(ok_row['tests']))
        md = (tmp / 'STATUS.md').read_text(encoding='utf-8')
        self.assertIn('render_error', md)

    def test_R21e_collect_failure_is_recorded_per_task(self):
        """一条任务收取时抛异常：只记在它自己身上，其他任务照收，队列不丢。"""
        self.write_snapshot(two_sessions())
        self.submit_and_dispatch()
        q = self.queue()
        (self.hub / 'transcript' / DEV / (SES2 + '.jsonl')).write_text('', encoding='utf-8')
        q['jobs']['T2'] = dict(q['jobs']['T1'], task_id='T2', owner='grok',
                               session_id=SES2, status='running', created_at='2020-01-01')
        D.atomic(self.root / 'queue.json', q)
        real = D.collect

        def boom(job, *a, **k):
            if job['task_id'] == 'T2':
                raise RuntimeError('transcript metadata blew up')
            return real(job, *a, **k)

        D.collect = boom
        self.addCleanup(setattr, D, 'collect', real)
        queue, _ = D.tick_once(self.root, self.hub, self.queue(), allow_dispatch=False)
        self.assertIn('RuntimeError', queue['jobs']['T2']['collect_error'])
        self.assertNotIn('collect_error', queue['jobs']['T1'],
                         '一条任务出错波及了其他任务')
        self.assertEqual(queue['jobs']['T2']['status'], 'running',
                         '收取失败被当成了某种结论')
        self.assertEqual(set(queue['jobs']), {'T1', 'T2'}, '队列条目丢了')

    def test_R21f_watch_survives_dict_tests_and_keeps_working(self):
        """真守护子进程：收到 tests 是对象的完成报告后**仍然活着**，
        继续处理其他任务，而且那条只停在 review。"""
        self.write_snapshot(two_sessions())
        t2path = self.hub / 'transcript' / DEV / (SES2 + '.jsonl')
        t2path.write_text('', encoding='utf-8')           # 第二个会话也要有转录文件
        self.submit_and_dispatch()                        # T1 claude running
        self.run_cli('start', '--interval', '1')
        self.addCleanup(lambda: self.run_cli('stop'))
        pid = int(D.read(self.root / 'watch.json')['pid'])
        self.append([claude_rec('assistant', self.marker(C03_REPORT))])

        deadline = time.time() + 20
        while time.time() < deadline:
            if self.queue()['jobs']['T1']['status'] == 'review':
                break
            time.sleep(0.3)
        self.assertEqual(self.queue()['jobs']['T1']['status'], 'review',
                         '守护没有收到这条报告（或已经死了）')

        os.kill(pid, 0)                                   # 旧实现在这里已经退出了
        self.assertTrue(D.watcher_alive(self.root), '守护被一份 tests 是对象的报告打死了')

        # 还能继续干活：给另一个 owner 提一条新任务，守护应当照常派出去
        nxt = self.job(owner='grok', task='T2')
        nxt['session_id'] = SES2
        jf = self.tmp / 'j2.json'
        jf.write_text(json.dumps(nxt), encoding='utf-8')
        self.run_cli('submit', str(jf))
        deadline = time.time() + 20
        while time.time() < deadline:
            if self.queue()['jobs']['T2']['status'] == 'running':
                break
            time.sleep(0.3)
        self.assertEqual(self.queue()['jobs']['T2']['status'], 'running',
                         '守护活着但不再处理新任务')
        self.assertTrue(D.watcher_alive(self.root))

        info = D.read(self.root / 'watch.json', {}) or {}
        self.assertEqual(info.get('error_rounds', 0), 0,
                         'last_round=%s' % info.get('last_round'))
        j = self.queue()['jobs']['T1']
        self.assertEqual(j['status'], 'review', '自报报告被自动 accept 成 done 了')
        self.assertEqual(j['report'], C03_REPORT)
        self.assertIn('UNCOVERED', json.dumps(j['report'], ensure_ascii=False))
        md = (self.root / 'STATUS.md').read_text(encoding='utf-8')
        self.assertIn('UNCOVERED', md, 'STATUS 把那 1 项 UNCOVERED 抹掉了')

    def test_R21g_round_error_does_not_kill_watch_or_queue(self):
        """兜底网：一轮里出了完全没预料到的异常，守护要记错误并继续，
        **而且不能把队列写成空的**。"""
        self.submit_and_dispatch()
        before = (self.root / 'queue.json').read_text(encoding='utf-8')
        sitter = self.tmp / 'sitter.py'
        sitter.write_text(
            'import sys, json\n'
            'sys.path.insert(0, %r)\n'
            'import dispatch as D\n'
            'rounds = {"n": 0}\n'
            'real = D.tick_once\n'
            'def boom(*a, **k):\n'
            '    rounds["n"] += 1\n'
            '    if rounds["n"] == 1:\n'
            '        raise RuntimeError("unexpected metadata")\n'
            '    return real(*a, **k)\n'
            'D.tick_once = boom\n'
            'sys.exit(D.cmd_watch(D.Path(%r), D.Path(%r), 1))\n'
            % (str(Path(DISPATCH).parent), str(self.root), str(self.hub)),
            encoding='utf-8')
        proc = subprocess.Popen([sys.executable, str(sitter)],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        self.addCleanup(proc.kill)
        deadline = time.time() + 20
        seen_error = False
        while time.time() < deadline:
            info = D.read(self.root / 'watch.json', {}) or {}
            if info.get('error_rounds', 0) >= 1:
                seen_error = True
            if seen_error and info.get('last_round') == 'ok':
                break
            time.sleep(0.3)
        self.assertTrue(seen_error, '出错的那一轮没有被记下来')
        self.assertIsNone(proc.poll(), '守护因为一轮异常整个退出了')
        info = D.read(self.root / 'watch.json', {}) or {}
        self.assertEqual(info.get('last_round'), 'ok', '出错之后没能恢复收轮')
        self.assertEqual(json.loads((self.root / 'queue.json').read_text(encoding='utf-8'))['jobs']
                         .keys(), json.loads(before)['jobs'].keys(), '队列条目被那一轮弄丢了')
        log = (self.root / 'logs' / 'watch-errors.jsonl').read_text(encoding='utf-8')
        self.assertIn('RuntimeError', log)
        self.assertIn('unexpected metadata', log)
        self.assertEqual(oct((self.root / 'logs' / 'watch-errors.jsonl').stat().st_mode)[-3:], '600')
        proc.terminate()
        proc.wait(timeout=10)

    def test_R21h_corrupt_queue_still_preserved_under_the_new_net(self):
        """加了兜底网之后，坏队列仍然按老规矩：保留原件、拦住派发、不降级为空。"""
        self.submit_and_dispatch()
        original = (self.root / 'queue.json').read_text(encoding='utf-8')
        (self.root / 'queue.json').write_text(original[:len(original) // 2], encoding='utf-8')
        broken = (self.root / 'queue.json').read_text(encoding='utf-8')
        proc = subprocess.run([sys.executable, DISPATCH, '--state-dir', str(self.root),
                               '--hub-dir', str(self.hub), 'watch', '--once',
                               '--lock-wait', '1'], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stderr[-300:])
        self.assertEqual((self.root / 'queue.json').read_text(encoding='utf-8'), broken,
                         '坏队列被覆盖了')
        blocked = json.loads((self.root / 'BLOCKED.json').read_text(encoding='utf-8'))
        self.assertIn('unreadable', blocked['reason'])
        info = D.read(self.root / 'watch.json', {}) or {}
        self.assertIn('unreadable', info.get('last_round', ''))
        self.assertEqual(info.get('error_rounds', 0), 0,
                         '坏队列被当成了兜底网里的意外异常')
        self.assertEqual(len(self.envelopes()), 1, '坏队列期间派发了新任务')


if __name__ == '__main__':
    unittest.main(verbosity=2)
