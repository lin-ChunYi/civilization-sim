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
        cut = len(text) // 3
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


if __name__ == '__main__':
    unittest.main(verbosity=2)
