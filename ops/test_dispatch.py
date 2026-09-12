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


# ---------------------------------------------------------------- grok-cli 通道
FAKE_CLI = r"""#!/usr/bin/env python3
# 测试用的假 CLI：只按提示词里的指令往 stdout 写几行 JSON，不联网、不调任何模型。
import json, sys, time

args = sys.argv[1:]


def val(flag):
    return args[args.index(flag) + 1] if flag in args else None


def emit(obj):
    sys.stdout.write(json.dumps(obj, ensure_ascii=False) + "\n")
    sys.stdout.flush()


prompt = open(val("--prompt-file"), encoding="utf-8").read()
emit({"type": "system", "argv": args, "session_id": val("--resume") or "new-session-9"})
if "SLEEP" in prompt:
    time.sleep(120)
if "CANCELLED" in prompt:
    emit({"type": "result", "stopReason": "cancelled",
          "cancellationCategory": "PermissionCancelled", "isError": False})
    sys.exit(0)
if "QUOTA" in prompt:
    emit({"type": "result", "error": "usage limit reached for this window"})
    sys.exit(0)
if "HALF" in prompt:
    sys.stdout.write('{"type":"assistant","text":"CIV_RESU')     # 故意写半条
    sys.stdout.flush()
    sys.exit(0)
if "TWOMARK" in prompt:
    emit({"type": "assistant", "text": "CIV_RESULT_G9 {\"status\":\"done\",\"a\":1}"})
    emit({"type": "assistant", "text": "CIV_RESULT_G9 {\"status\":\"done\",\"a\":2}"})
    sys.exit(0)
if "NOMARK" in prompt:
    emit({"type": "assistant", "text": "干完了，但是忘了写结果行"})
    sys.exit(0)
if "QWORD" in prompt:
    # 正文里**提到**额度，但这一轮其实成功了 —— 不许被当成额度受限
    emit({"type": "assistant",
          "text": '\u672a\u89e6\u53d1\u989d\u5ea6\u9650\u5236\u3002'
                  'CIV_RESULT_G9 {"status":"done","commit":"QW","tests":["quota \u989d\u5ea6 ok"]}'})
    emit({"text": "done", "stopReason": "end_turn", "sessionId": "041d", "num_turns": 3})
    sys.exit(0)
if "HARDLIMIT" in prompt:
    emit({"type": "assistant", "text": "开始干活"})
    emit({"text": "", "stopReason": "error", "error": "usage limit reached for this window",
          "sessionId": "041d"})
    sys.exit(0)
if "CANCELMARK" in prompt:
    emit({"type": "assistant", "text": 'CIV_RESULT_G9 {"status":"done","commit":"EARLY"}'})
    emit({"text": "", "stopReason": "cancelled",
          "cancellationCategory": "PermissionCancelled", "sessionId": "041d"})
    sys.exit(0)
if "GENCANCEL" in prompt:
    emit({"type": "assistant", "text": 'CIV_RESULT_G9 {"status":"done","commit":"EARLY"}'})
    emit({"text": "", "stopReason": "cancelled", "sessionId": "041d"})
    sys.exit(0)
if "USERCANCEL" in prompt:
    emit({"text": "", "stopReason": "cancelled",
          "cancellationCategory": "UserCancelled", "sessionId": "041d"})
    sys.exit(0)
if "HISTERR" in prompt:
    # resume 的日志里带着**早先那一轮**的失败，这一轮正常完成
    emit({"type": "result", "stopReason": "cancelled",
          "cancellationCategory": "PermissionCancelled"})
    emit({"type": "assistant", "text": 'CIV_RESULT_G9 {"status":"done","commit":"LATER"}'})
    emit({"text": "ok", "stopReason": "end_turn", "sessionId": "041d"})
    sys.exit(0)
if "THOUGHT" in prompt:
    emit({"type": "assistant", "thought": "要不要取消？会不会 PermissionCancelled 或者额度不够",
          "text": 'CIV_RESULT_G9 {"status":"done","commit":"TH"}'})
    emit({"text": "ok", "stopReason": "end_turn", "sessionId": "041d"})
    sys.exit(0)
if "RCFAIL" in prompt:
    emit({"type": "assistant", "text": "起不来"})
    sys.exit(7)
if "DICTTESTS" in prompt:
    emit({"type": "assistant",
          "text": 'CIV_RESULT_G9 {"status":"done","tests":{"a":"1 PASS","b":"2 PASS"}}'})
    sys.exit(0)
emit({"type": "assistant", "text": 'CIV_RESULT_G9 {"status":"done","commit":"ABC"}'})
sys.exit(0)
"""


class CliBase(Base):
    """grok-cli 通道的公共装置：一个**假 CLI 脚本**，不碰真实 Grok 环境、
    不联网、不动任何正在跑的真实任务。"""

    def setUp(self):
        super().setUp()
        self.cli = self.tmp / 'fake-grok'
        self.cli.write_text(FAKE_CLI, encoding='utf-8')
        os.chmod(self.cli, 0o700)
        self.proj = self.tmp / 'proj'
        self.proj.mkdir()
        self.cli_prompt = self.tmp / 'g9.txt'

    def cli_job(self, directive, task='G9', **cli_extra):
        self.cli_prompt.write_text(
            '%s\n请做 %s，完成后单行 %s{...}\n' % (directive, task, D.MARKER_PREFIX + task),
            encoding='utf-8')
        spec = {'bin': str(self.cli), 'cwd': str(self.proj),
                'session_id': '041d93f0-5eae-4cff-90b8-f52785f14553',
                'output_format': 'json', 'permission_mode': 'acceptEdits',
                'allow': ['Bash(git status*)', 'Edit(observer/web/**)'],
                'deny': ['Bash(git push*)'], 'max_turns': 100,
                'extra_args': ['--no-subagents', '--disable-web-search']}
        spec.update(cli_extra)
        return {'task_id': task, 'owner': 'grok', 'transport': 'grok-cli',
                'objective': 'o', 'allowed_paths': ['observer/web/'], 'baseline_sha': 'abc',
                'dependencies': [], 'acceptance': 'a', 'workdir': str(self.proj),
                'branch': 'main', 'prompt_file': str(self.cli_prompt), 'cli': spec}

    def submit_cli(self, directive, task='G9', **cli_extra):
        jf = self.tmp / (task + '.json')
        jf.write_text(json.dumps(self.cli_job(directive, task, **cli_extra)), encoding='utf-8')
        self.run_cli('submit', str(jf))
        return task

    def tick_inproc(self):
        """在**本进程**里收一轮 —— 和长期守护一样能留住 Popen，因而拿得到退出码。
        一次性的 `tick` 子进程做不到这一点，那时退出码如实记 null。"""
        with D.op_lock(self.root):
            queue, problem = D.load_queue(self.root)
            self.assertFalse(problem, problem)
            queue, _ = D.tick_once(self.root, self.hub, queue)
            queue['updated_at'] = D.now()
            D.atomic(self.root / 'queue.json', queue)
            D.render_status(queue, self.root, self.hub)
        return self.queue()['jobs']

    def settle_inproc(self, task='G9', rounds=60):
        for _ in range(rounds):
            jobs = self.tick_inproc()
            if jobs[task]['status'] in ('review', 'blocked', 'rejected', 'done'):
                return jobs[task]
            time.sleep(0.2)
        return self.queue()['jobs'][task]

    def settle(self, task='G9', rounds=80):
        for _ in range(rounds):
            self.run_cli('tick')
            job = self.queue()['jobs'][task]
            if job['status'] in ('review', 'blocked', 'rejected', 'done'):
                return job
            time.sleep(0.2)
        return self.queue()['jobs'][task]

    def _kill(self, pid):
        if not pid:
            return
        try:
            os.kill(int(pid), signal.SIGKILL)
        except OSError:
            pass


class TestGrokCliTransport(CliBase):
    # ---------------- 命令与身份 ----------------
    def test_R22_explicit_argv_and_resume_are_recorded(self):
        self.submit_cli('NOMARK')
        self.run_cli('tick')
        job = self.queue()['jobs']['G9']
        argv = job['cli_argv']
        self.assertEqual(argv[0], str(self.cli))
        pairs = [argv[i:i + 2] for i in range(len(argv) - 1)]
        for pair in (['--cwd', str(self.proj)],
                     ['--resume', '041d93f0-5eae-4cff-90b8-f52785f14553'],
                     ['--output-format', 'json'],
                     ['--permission-mode', 'acceptEdits'],
                     ['--allow', 'Bash(git status*)'],
                     ['--allow', 'Edit(observer/web/**)'],
                     ['--deny', 'Bash(git push*)'],
                     ['--max-turns', '100']):
            self.assertIn(pair, pairs, '命令数组里缺 %s' % pair)
        self.assertIn('--no-subagents', argv)
        self.assertEqual(job['cli_session_mode'], 'resume', '续用会话被当成了新建')
        self.assertTrue(job['cli_token'] and job['cli_token'] in ' '.join(argv),
                        '出生身份 token 没有出现在命令行里，重启后认不回来')
        self.assertTrue(job['journal'] and job['journal_err'])
        self.assertEqual(oct(Path(job['journal']).stat().st_mode)[-3:], '600')
        cmd = D.read(self.root / 'logs' / 'G9.command.json')
        self.assertEqual(cmd['argv'], argv)

    def test_R22b_new_session_is_not_called_a_resume(self):
        self.submit_cli('NOMARK', session_id=None)
        self.run_cli('tick')
        job = self.queue()['jobs']['G9']
        self.assertEqual(job['cli_session_mode'], 'new')
        self.assertNotIn('--resume', job['cli_argv'])
        self.settle()
        self.assertEqual(self.queue()['jobs']['G9'].get('cli_session_id'), 'new-session-9',
                         '新建会话报出来的 session id 没有被记下来')

    def test_R22c_blanket_permission_modes_are_refused(self):
        jf = self.tmp / 'bad.json'
        jf.write_text(json.dumps(self.cli_job('NOMARK', permission_mode='bypassPermissions')),
                      encoding='utf-8')
        out = self.run_cli('submit', str(jf), expect=1)
        self.assertIn('blanket permission mode', out.stdout + out.stderr)

    # ---------------- 结局判定 ----------------
    def test_R22d_rc0_with_permission_cancelled_is_not_done(self):
        """真实踩过的坑：rc=0 但 stopReason=cancelled / PermissionCancelled。
        既不是完成，也不是"用户放弃了这场马拉松"。"""
        self.submit_cli('CANCELLED')
        job = self.settle_inproc()
        self.assertEqual(job['receipt_state'], 'permission_cancelled')
        self.assertEqual(job['status'], 'blocked')
        self.assertNotIn('report', job)
        self.assertIn('NOT a completed task', job['receipt_detail'])
        self.assertIn('NOT the user abandoning', job['receipt_detail'])
        self.assertEqual(job['cli_rc'], 0, 'rc 确实是 0，正是这条的要害')

    def test_R22e_rc0_without_marker_is_not_done(self):
        """一次性 tick 拿不到退出码（子进程已被 init 接管），判定只能靠日志 ——
        这正是"rc=0 不等于完成"的另一面：连 rc 都没有，也照样给得出准确状态。"""
        self.submit_cli('NOMARK')
        job = self.settle()
        self.assertIsNone(job['cli_rc'])
        self.assertIn('exit code unavailable', job['receipt_detail'])
        self.assertEqual(job['receipt_state'], 'cli_no_unique_result')
        self.assertEqual(job['status'], 'blocked')
        self.assertNotIn('report', job)

    def test_R22f_two_conflicting_markers_have_no_unique_result(self):
        self.submit_cli('TWOMARK')
        job = self.settle()
        self.assertEqual(job['receipt_state'], 'cli_no_unique_result')
        self.assertIn('conflicting', job['receipt_detail'])

    def test_R22g_half_written_journal_is_unknown_not_done(self):
        self.submit_cli('HALF')
        job = self.settle()
        self.assertEqual(job['receipt_state'], 'cli_exited_incomplete')
        self.assertEqual(job['status'], 'blocked')
        self.assertIn('no auto-relaunch', job['receipt_detail'])

    def test_R22h_quota_is_its_own_state_and_is_not_retried(self):
        self.submit_cli('QUOTA')
        job = self.settle()
        self.assertEqual(job['receipt_state'], 'quota_blocked')
        self.assertEqual(job['dispatch_count'], 1, '额度受限时又跑了一遍')

    def test_R22i_nonzero_rc_is_failed_not_done(self):
        self.submit_cli('RCFAIL')
        job = self.settle_inproc()
        self.assertEqual(job['receipt_state'], 'cli_failed')
        self.assertEqual(job['cli_rc'], 7)

    def test_R22j_self_report_only_reaches_review(self):
        self.submit_cli('MARK')
        job = self.settle()
        self.assertEqual(job['status'], 'review', '自报直接变成了 done')
        self.assertEqual(job['report']['commit'], 'ABC')
        self.assertIn('still needs accept', job['receipt_detail'])
        ev = self.tmp / 'ev.txt'
        ev.write_text('codex verified', encoding='utf-8')
        self.run_cli('accept', 'G9', '--evidence', str(ev))
        self.assertEqual(self.queue()['jobs']['G9']['status'], 'done')

    def test_R22k_report_types_do_not_break_the_summary(self):
        self.submit_cli('DICTTESTS')
        job = self.settle()
        self.assertEqual(job['status'], 'review')
        self.assertEqual(job['report']['tests'], {'a': '1 PASS', 'b': '2 PASS'})
        js = json.loads((self.root / 'STATUS.json').read_text(encoding='utf-8'))
        row = [r for r in js['jobs'] if r['task_id'] == 'G9'][0]
        self.assertIn('1 PASS', ' | '.join(row['tests']))
        self.assertEqual(row['transport'], 'grok-cli')
        md = (self.root / 'STATUS.md').read_text(encoding='utf-8')
        self.assertIn('- cli: pid=', md)
        self.assertLess(len(md), 8000, 'STATUS 变成了转录堆')

    # ---------------- 不重复派发 / 重启接管 ----------------
    def test_R22l_repeated_tick_never_launches_twice(self):
        self.submit_cli('SLEEP')
        for _ in range(4):
            self.run_cli('tick')
        job = self.queue()['jobs']['G9']
        self.assertEqual(job['dispatch_count'], 1, '重复 tick 又起了一个进程')
        self.assertEqual(len(list((self.root / 'prompts').glob('*.txt'))), 1)
        self.addCleanup(self._kill, job.get('cli_pid'))

    def test_R22m_restart_reclaims_by_token_instead_of_relaunching(self):
        self.submit_cli('SLEEP')
        self.run_cli('tick')
        job = self.queue()['jobs']['G9']
        real_pid = job['cli_pid']
        self.addCleanup(self._kill, real_pid)
        self.assertEqual(D.probe_cli(job), 'alive')
        # 模拟守护重启：进程内的 Popen 没了，队列里记的 pid 也被弄脏
        D._CLI_PROCS.clear()
        q = self.queue()
        q['jobs']['G9']['cli_pid'] = 999999
        q['jobs']['G9']['cli_birth'] = ''
        D.atomic(self.root / 'queue.json', q)
        self.run_cli('tick')
        job2 = self.queue()['jobs']['G9']
        self.assertEqual(job2['cli_pid'], real_pid, '重启后没按 token 把进程认回来')
        self.assertEqual(job2['dispatch_count'], 1, '重启后又跑了一遍')
        self.assertEqual(len(list((self.root / 'prompts').glob('*.txt'))), 1)

    def test_R22n_pid_reuse_is_gone_and_never_signalled(self):
        self.submit_cli('SLEEP')
        self.run_cli('tick')
        job = dict(self.queue()['jobs']['G9'])
        self.addCleanup(self._kill, job['cli_pid'])
        victim = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(30)'])
        self.addCleanup(victim.kill)
        job['cli_pid'] = victim.pid                 # 假装 pid 被复用了
        self.assertEqual(D.probe_cli(job), 'gone', 'pid 被复用却认成了自己的进程')
        sent = []
        real_kill = os.kill
        os.kill = lambda pid, sig: sent.append(sig) if sig else real_kill(pid, sig)
        try:
            D.cli_pause(dict(job, status='running',
                             cli=dict(job['cli'], graceful_cancel=True)), self.root)
        finally:
            os.kill = real_kill
        self.assertEqual(sent, [], '对身份对不上的 pid 发了信号')
        time.sleep(0.2)
        self.assertIsNone(victim.poll(), '无关进程被误杀了')

    def test_R22o_owner_holds_one_live_cli_run(self):
        self.submit_cli('SLEEP', task='G9')
        self.run_cli('tick')
        first = self.queue()['jobs']['G9']
        self.addCleanup(self._kill, first.get('cli_pid'))
        self.submit_cli('MARK', task='G10')
        self.run_cli('tick')
        second = self.queue()['jobs']['G10']
        self.assertEqual(second['status'], 'pending', '同一个 owner 同时跑了两个 CLI 任务')
        self.assertIsNone(second.get('cli_pid'))

    def test_R22p_same_prompt_on_same_session_is_refused(self):
        self.submit_cli('SLEEP')
        dup_text = self.cli_prompt.read_text(encoding='utf-8')
        self.run_cli('tick')
        self.addCleanup(self._kill, self.queue()['jobs']['G9'].get('cli_pid'))
        job = self.cli_job('SLEEP', task='G11')
        job['prompt_file'] = str(self.cli_prompt)
        self.cli_prompt.write_text(dup_text, encoding='utf-8')   # 同一份字节
        jf = self.tmp / 'dup.json'
        jf.write_text(json.dumps(job), encoding='utf-8')
        out = self.run_cli('submit', str(jf), expect=1)
        self.assertIn('does not re-run a task', out.stdout + out.stderr)

    # ---------------- 暂停 ----------------
    def test_R22q_pause_never_injects_and_never_signals_by_default(self):
        self.submit_cli('SLEEP')
        self.run_cli('tick')
        job = self.queue()['jobs']['G9']
        self.addCleanup(self._kill, job.get('cli_pid'))
        before = len(list((self.hub / 'outbox').glob('*')))
        sent = []
        real_kill = os.kill
        os.kill = lambda pid, sig: sent.append(sig) if sig else real_kill(pid, sig)
        try:
            self.run_cli('pause')
            self.run_cli('tick')
        finally:
            os.kill = real_kill
        after = len(list((self.hub / 'outbox').glob('*')))
        self.assertEqual(after, before, 'headless CLI 的任务被 reply_inject 了')
        self.assertEqual(sent, [], '默认暂停就给 CLI 发了信号')
        paused = self.queue()['jobs']['G9']
        self.assertIn('NOT interrupted', paused['pause_note'])
        self.assertIn('no further rounds', paused['pause_note'])
        self.assertEqual(paused['status'], 'running', '暂停把没结束的任务判成别的了')

    def test_R22r_graceful_cancel_only_targets_our_verified_pid(self):
        self.submit_cli('SLEEP', graceful_cancel=True)
        self.run_cli('tick')
        job = self.queue()['jobs']['G9']
        pid = job['cli_pid']
        self.addCleanup(self._kill, pid)
        self.run_cli('pause')
        self.run_cli('tick')
        paused = self.queue()['jobs']['G9']
        self.assertEqual(paused.get('pause_signal'), 'SIGINT')
        self.assertIn('our own verified pid', paused['pause_note'])
        self.assertTrue(Path(paused['journal']).exists(), '暂停把日志弄丢了')
        # 接管观察的任务：即使开了 graceful_cancel 也一个信号都不发
        adopted = dict(job, task_id='G12', owns_process=False, pause_notice_sent=False,
                       cli=dict(job['cli'], graceful_cancel=True))
        sent = []
        real_kill = os.kill
        os.kill = lambda p_, sig: sent.append(sig) if sig else real_kill(p_, sig)
        try:
            D.cli_pause(adopted, self.root)
        finally:
            os.kill = real_kill
        self.assertEqual(sent, [], '对接管观察的进程发了信号')
        self.assertIn('NOT interrupted', adopted['pause_note'])

    def test_R22s_adopted_run_is_observed_never_signalled(self):
        holder = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(30)'])
        self.addCleanup(holder.kill)
        journal = self.tmp / 'foreign.jsonl'
        journal.write_text(json.dumps({'type': 'assistant', 'text': 'still working'}) + '\n',
                           encoding='utf-8')
        job = self.cli_job('MARK', task='G13')
        job['cli']['adopt'] = {'pid': holder.pid, 'journal': str(journal),
                               'session_id': '041d93f0-5eae-4cff-90b8-f52785f14553'}
        job['cli']['session_id'] = None
        jf = self.tmp / 'adopt.json'
        jf.write_text(json.dumps(job), encoding='utf-8')
        self.run_cli('submit', str(jf))
        self.run_cli('tick')
        row = self.queue()['jobs']['G13']
        self.assertEqual(row['receipt_state'], 'cli_observing')
        self.assertFalse(row['owns_process'])
        self.assertIsNone(row.get('cli_argv'), '接管观察的任务不该被启动')
        self.assertEqual(row['cli_session_mode'], 'adopted')
        time.sleep(0.2)
        self.assertIsNone(holder.poll(), '接管观察却把别人的进程弄死了')

    # ---------------- 原生终端回执 ----------------
    def test_R22t_native_terminal_unknown_prefix_is_unknown_not_failed(self):
        """真实回执：[delivery state=unknown retry=none] ... native terminal unsafe ...
        以前被归成 failed。它不是失败，是**不知道** —— 继续观察，绝不自动重发。"""
        job = self.submit_and_dispatch()          # Cockpit 通道，与 CLI 无关
        corr = job['corr_id']
        (self.hub / 'outbox' / (corr + '.result.json')).write_text(json.dumps(
            {'ok': False,
             'error': '[delivery state=unknown retry=none] native terminal unsafe; '
                      'no injection performed'}), encoding='utf-8')
        self.run_cli('tick')
        row = self.queue()['jobs']['T1']
        self.assertEqual(row['receipt_state'], 'unknown', '原生终端的未知回执被当成了失败')
        self.assertFalse(row['receipt_safe_requeue'], '未知却被标成可以安全重排')
        out = self.run_cli('requeue', 'T1', expect=1)
        self.assertIn('acknowledge', (out.stdout + out.stderr).lower())
        self.assertEqual(self.queue()['jobs']['T1']['dispatch_count'], 1, '未知的任务被重发了')


# ------------------------------- C06_R1：三处边界（独立复审在 59650b3 上实证）
class TestCliBoundaries(CliBase):
    """1) token 落盘、pid 还没写回来的崩溃窗口；
    2) 正文里提到"额度"被误判成额度受限；
    3) 当前这一轮的终态取消必须盖过此前出现过的标记。"""

    def mem_job(self, records, **extra):
        """直接拿原函数造场景 —— 这三条就是这么被复现出来的。"""
        jpath = self.tmp / ('mem-%d.jsonl' % len(list(self.tmp.glob('mem-*.jsonl'))))
        jpath.write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in records),
                         encoding='utf-8')
        job = {'task_id': 'G9', 'owner': 'grok', 'transport': 'grok-cli', 'status': 'running',
               'owns_process': True, 'cli_pid': None, 'cli_token': None, 'cli_rc': 0,
               'journal': str(jpath), 'dependencies': [], 'created_at': D.now()}
        job.update(extra)
        return job

    # ---------- 1. 崩溃窗口 ----------
    def test_R23_claim_without_pid_is_unknown_not_gone(self):
        job = self.mem_job([{'type': 'assistant',
                             'text': 'CIV_RESULT_G9 {"status":"done","commit":"X"}'}],
                           cli_token='ciltok-G9-deadbeef')
        real = D.find_by_token
        D.find_by_token = lambda t: 'unknown'
        try:
            D.collect_cli(job, self.root)
        finally:
            D.find_by_token = real
        self.assertEqual(job['cli_probe'], 'unknown', '没有 pid 被当成了进程已死')
        self.assertEqual(job['receipt_state'], 'unknown')
        self.assertEqual(job['status'], 'blocked')
        self.assertNotIn('report', job, '进程状态未知却认了自报结果')
        self.assertIn('not dead', job['receipt_detail'])
        self.assertTrue(D.cli_unresolved(job), '结局未定却被当成已有结论')

    def test_R23b_unresolved_cli_does_not_free_the_owner_for_rework(self):
        """进程**看不见**（pid 没了、日志也空）但结局未定时，最容易被当成"已有结论"
        而放行返工 —— 那个进程可能还活着，只是我们此刻看不见它。"""
        self.submit_cli('SLEEP')
        self.run_cli('tick')
        live = self.queue()['jobs']['G9']
        self.addCleanup(self._kill, live.get('cli_pid'))
        self._kill(live.get('cli_pid'))
        Path(live['journal']).write_text('', encoding='utf-8')
        q = self.queue()
        q['jobs']['G9'].update(status='blocked', cli_pid=None, cli_birth='',
                               receipt_state='cli_no_launch_record',
                               blocking_reason='outcome unknown')
        D.atomic(self.root / 'queue.json', q)
        rw = self.cli_job('MARK', task='G9_R1')
        rw['rework_of'] = 'G9'
        jf = self.tmp / 'rw.json'
        jf.write_text(json.dumps(rw), encoding='utf-8')
        self.run_cli('submit', str(jf))
        self.run_cli('tick')
        self.assertEqual(self.queue()['jobs']['G9_R1']['status'], 'pending',
                         '结局未定的 CLI 任务放行了同 owner 的返工')

    def test_R23c_unknown_recovers_on_a_later_tick(self):
        """ps 恢复正常之后，下一轮必须还能把它认回来 —— 不能永远卡在未知上。"""
        self.submit_cli('SLEEP')
        self.run_cli('tick')
        job = self.queue()['jobs']['G9']
        real_pid = job['cli_pid']
        self.addCleanup(self._kill, real_pid)
        q = self.queue()
        q['jobs']['G9'].update(cli_pid=None, cli_birth='', status='blocked',
                               receipt_state='unknown', blocking_reason='ps unavailable')
        D.atomic(self.root / 'queue.json', q)
        jobs = self.tick_inproc()                  # ps 正常了
        self.assertEqual(jobs['G9']['cli_pid'], real_pid, '下一轮没能重新认领')
        self.assertEqual(jobs['G9']['status'], 'running')
        self.assertEqual(jobs['G9']['dispatch_count'], 1, '重新认领时又跑了一遍')

    def test_R23d_no_launch_record_is_its_own_state(self):
        """没有 pid、进程表里没有、日志也是空的：**说不清有没有启动过**。
        这和"确实停了"不是一回事，不能靠没有 pid 推断死亡。"""
        empty = self.tmp / 'empty.jsonl'
        empty.write_text('', encoding='utf-8')
        job = self.mem_job([], cli_token='ciltok-G9-nothing')
        job['journal'] = str(empty)
        real = D.find_by_token
        D.find_by_token = lambda t: []
        try:
            D.collect_cli(job, self.root)
        finally:
            D.find_by_token = real
        self.assertEqual(job['receipt_state'], 'cli_no_launch_record')
        self.assertEqual(job['status'], 'blocked')
        self.assertIn('cannot tell whether the CLI ever started', job['receipt_detail'])
        self.assertTrue(D.cli_unresolved(job))

    def test_R23e_no_pid_but_journal_output_means_it_really_ran(self):
        job = self.mem_job([{'type': 'assistant',
                             'text': 'CIV_RESULT_G9 {"status":"done","commit":"R"}'},
                            {'text': 'ok', 'stopReason': 'end_turn'}],
                           cli_token='ciltok-G9-ran')
        real = D.find_by_token
        D.find_by_token = lambda t: []
        try:
            D.collect_cli(job, self.root)
        finally:
            D.find_by_token = real
        self.assertEqual(job['cli_probe'], 'gone')
        self.assertEqual(job['status'], 'review', '有日志、有终态、有唯一标记，却没进 review')

    # ---------- 2. "额度"是说话还是信号 ----------
    def test_R23f_prose_mentioning_quota_is_not_a_quota_block(self):
        self.submit_cli('QWORD')
        job = self.settle()
        self.assertEqual(job['receipt_state'], 'durable_ok',
                         '正文里提到额度就被判成了额度受限：%s' % job['receipt_detail'][:80])
        self.assertEqual(job['status'], 'review')
        self.assertEqual(job['report']['commit'], 'QW')

    def test_R23g_real_quota_in_the_terminal_record_still_blocks(self):
        self.submit_cli('HARDLIMIT')
        job = self.settle()
        self.assertEqual(job['receipt_state'], 'quota_blocked')
        self.assertEqual(job['status'], 'blocked')
        self.assertEqual(job['dispatch_count'], 1, '额度受限时又重派了')
        self.run_cli('tick')
        self.assertEqual(self.queue()['jobs']['G9']['dispatch_count'], 1)

    def test_R23h_private_thought_is_not_evidence_and_not_reported(self):
        self.submit_cli('THOUGHT')
        job = self.settle()
        self.assertEqual(job['status'], 'review',
                         '私有思考里的"取消/额度"被当成了信号：%s' % job['receipt_detail'][:80])
        self.assertEqual(job['report']['commit'], 'TH')
        self.assertNotIn('要不要取消', json.dumps(job.get('report'), ensure_ascii=False))

    # ---------- 3. 终态取消盖过此前的标记 ----------
    def test_R23i_permission_cancel_outranks_an_earlier_marker(self):
        self.submit_cli('CANCELMARK')
        job = self.settle()
        self.assertEqual(job['receipt_state'], 'permission_cancelled')
        self.assertEqual(job['status'], 'blocked')
        self.assertNotIn('report', job, '这一轮被取消了，早前的标记却被当成完成')
        self.assertIn('does NOT count as a completed task', job['receipt_detail'])
        self.assertEqual(job['cli_cancel_category'], 'PermissionCancelled')

    def test_R23j_generic_cancel_is_not_no_unique_result(self):
        self.submit_cli('GENCANCEL')
        job = self.settle()
        self.assertEqual(job['receipt_state'], 'cli_cancelled',
                         '只有 stopReason=cancelled 被误判成了"没有唯一结果"')
        self.assertEqual(job['cli_stop_reason'], 'cancelled')
        self.assertEqual(job['cli_cancel_category'], '')

    def test_R23k_user_cancel_is_distinguished_from_permission_cancel(self):
        self.submit_cli('USERCANCEL')
        job = self.settle()
        self.assertEqual(job['receipt_state'], 'cli_user_cancelled')
        self.assertIn('cancelled by a person', job['receipt_detail'])
        self.assertNotEqual(job['receipt_state'], 'permission_cancelled')

    def test_R23l_history_failure_does_not_poison_this_turn(self):
        """resume 的日志里带着早先那一轮的权限取消，这一轮正常完成 —— 结果就是完成。"""
        self.submit_cli('HISTERR')
        job = self.settle()
        self.assertEqual(job['status'], 'review',
                         '把历史里的失败带进了这一轮：%s' % job['receipt_detail'][:80])
        self.assertEqual(job['report']['commit'], 'LATER')
        self.assertEqual(job['cli_stop_reason'], 'end_turn')

    def test_R23m_acp_meta_cancellation_is_read(self):
        """原生 stream 的 ACP turn_completed 把 cancellationCategory 放在 _meta 里。"""
        job = self.mem_job([{'type': 'assistant',
                             'text': 'CIV_RESULT_G9 {"status":"done","commit":"E"}'},
                            {'type': 'turn_completed',
                             '_meta': {'cancellationCategory': 'PermissionCancelled'}}])
        D.collect_cli(job, self.root)
        self.assertEqual(job['receipt_state'], 'permission_cancelled')
        self.assertNotIn('report', job)


# ------------------------- C06_R2：身份核对（token 不构成身份，出生身份说了算）
class TestCliIdentity(CliBase):
    """独立复审在 59650b3 / 046bf1c 上实证过的漏洞：`probe_cli` 先看
    `token in line` 就返回 alive，绕过了已记录的 `cli_birth`。于是一个 11:30 才启动的
    `/bin/cat /tmp/<同一个 token>.stdout.jsonl` 被认成 10:00 启动的 Grok，
    `graceful_cancel` 还会向它发 SIGINT 并自称"已核验自己的进程"。

    这一组全部用**替身**核对身份与信号，只有明确标注的那条用本 suite 自己起的子进程；
    不碰任何真实 CLI、共享 leader 或借用窗口。
    """
    TOKEN = 'ciltok-G9-abc123'
    BIN = '/Users/ecool/.grok/bin/grok'
    PROMPT = '/tmp/ciltok-G9-abc123.txt'
    BIRTH = ('Fri Sep 12 10:00:00 2026 ' + BIN
             + ' --cwd /repo --resume 041d93f0 --prompt-file ' + PROMPT
             + ' --output-format json')

    def ident_job(self, **extra):
        job = {'task_id': 'G9', 'owner': 'grok', 'transport': 'grok-cli', 'status': 'running',
               'owns_process': True, 'cli_pid': 4242, 'cli_token': self.TOKEN,
               'cli_birth': self.BIRTH, 'cli_bin': self.BIN, 'cli_prompt_copy': self.PROMPT,
               'cli_argv': [self.BIN, '--cwd', '/repo', '--resume', '041d93f0',
                            '--prompt-file', self.PROMPT, '--output-format', 'json'],
               'cli': {'bin': self.BIN, 'graceful_cancel': True},
               'journal': str(self.tmp / 'none.jsonl'), 'dependencies': [],
               'created_at': D.now()}
        job.update(extra)
        return job

    def probe_and_pause(self, job, ps_line):
        """在替身下跑一次探测 + 一次暂停，记下**本来会发出去**的信号。真实信号一个不发。"""
        sent = []
        real_line, real_kill = D.proc_line, os.kill
        D.proc_line = lambda pid, _l=ps_line: _l
        os.kill = lambda pid, sig: sent.append((pid, sig))
        try:
            probe = D.probe_cli(job)
            D.cli_pause(job, self.root)
        finally:
            D.proc_line, os.kill = real_line, real_kill
        return probe, sent

    def test_R24_token_substring_cannot_override_birth_identity(self):
        """同一个 token 出现在命令行里，但那是另一条命令、另一个启动时刻。"""
        job = self.ident_job()
        line = 'Fri Sep 12 11:30:00 2026 /bin/cat /tmp/%s.stdout.jsonl' % self.TOKEN
        probe, sent = self.probe_and_pause(job, line)
        self.assertEqual(probe, 'gone', 'token 出现在命令行里就被认成自己的进程了')
        self.assertEqual(sent, [], '向一个不是自己的进程发了信号')
        self.assertIn('NO signal', job['pause_note'])
        self.assertEqual(job['cli_birth'], self.BIRTH, '出生身份被改写了')

    def test_R24b_same_command_different_start_time_is_pid_reuse(self):
        """命令行一模一样、启动时刻不同 —— 那就是 pid 被复用了。"""
        job = self.ident_job()
        line = self.BIRTH.replace('10:00:00', '11:30:00')
        probe, sent = self.probe_and_pause(job, line)
        self.assertEqual(probe, 'gone')
        self.assertEqual(sent, [])

    def test_R24c_same_start_time_different_command_is_not_ours(self):
        job = self.ident_job()
        line = 'Fri Sep 12 10:00:00 2026 /usr/bin/tail -f /tmp/%s.stdout.jsonl' % self.TOKEN
        probe, sent = self.probe_and_pause(job, line)
        self.assertEqual(probe, 'gone')
        self.assertEqual(sent, [])

    def test_R24d_exact_birth_identity_is_alive_and_gets_one_sigint(self):
        job = self.ident_job()
        probe, sent = self.probe_and_pause(job, self.BIRTH)
        self.assertEqual(probe, 'alive')
        self.assertEqual(sent, [(4242, signal.SIGINT)], '真的是自己的进程却没发 graceful cancel')
        self.assertIn('our own verified pid', job['pause_note'])
        job2 = self.ident_job(pause_notice_sent=True)
        _, again = self.probe_and_pause(job2, self.BIRTH)
        self.assertEqual(again, [], '暂停信号发了不止一次')

    def test_R24e_no_graceful_cancel_means_no_signal_at_all(self):
        job = self.ident_job(cli={'bin': self.BIN})
        probe, sent = self.probe_and_pause(job, self.BIRTH)
        self.assertEqual(probe, 'alive')
        self.assertEqual(sent, [], '没开 graceful_cancel 却发了信号')
        self.assertIn('NOT interrupted', job['pause_note'])

    def test_R24f_missing_birth_falls_back_to_command_structure(self):
        """出生身份没记下来时，只认**命令结构**：那个 CLI + 我们这次的提示词副本。"""
        job = self.ident_job(cli_birth='')
        ours = 'Fri Sep 12 11:00:00 2026 ' + self.BIN + ' --cwd /repo --prompt-file ' + self.PROMPT
        probe, sent = self.probe_and_pause(job, ours)
        self.assertEqual(probe, 'alive')
        self.assertEqual(sent, [(4242, signal.SIGINT)])
        # 解释器前缀（带 shebang 的脚本）不影响判定
        job2 = self.ident_job(cli_birth='')
        via = ('Fri Sep 12 11:00:00 2026 /usr/bin/python3 ' + self.BIN
               + ' --cwd /repo --prompt-file ' + self.PROMPT)
        self.assertEqual(self.probe_and_pause(job2, via)[0], 'alive')
        # 只是读同名日志的进程，两条都不满足
        job3 = self.ident_job(cli_birth='')
        decoy = 'Fri Sep 12 11:00:00 2026 /bin/cat /tmp/%s.stdout.jsonl' % self.TOKEN
        probe3, sent3 = self.probe_and_pause(job3, decoy)
        self.assertEqual(probe3, 'gone')
        self.assertEqual(sent3, [])

    def test_R24g_adopted_run_without_identity_is_unknown_not_alive(self):
        """接管观察、连出生身份都没记下来：证实不了就是 unknown，不当活也不当死，
        更不发信号。"""
        job = self.ident_job(cli_birth='', cli_argv=None, cli_prompt_copy='', cli_bin='',
                             owns_process=False, cli={'bin': '', 'graceful_cancel': True})
        probe, sent = self.probe_and_pause(job, 'Fri Sep 12 11:00:00 2026 /opt/grok --serve')
        self.assertEqual(probe, 'unknown')
        self.assertEqual(sent, [], '对接管观察的进程发了信号')

    def test_R24h_ps_unknown_never_signals(self):
        job = self.ident_job()
        probe, sent = self.probe_and_pause(job, 'unknown')
        self.assertEqual(probe, 'unknown')
        self.assertEqual(sent, [])
        self.assertIn('NO signal', job['pause_note'])

    def test_R24i_reclaim_refuses_a_log_reader_candidate(self):
        """token 只用来找候选。扫到的是 `cat`/`tail` 这类读同名文件的进程时，
        既不认领、也不因此获得"可以对它发信号"的资格。"""
        job = self.ident_job(cli_pid=None, cli_birth='')
        decoy_pid = 777001
        real = D.find_by_token
        D.find_by_token = lambda t: [(decoy_pid,
                                      '/bin/cat /tmp/%s.stdout.jsonl' % self.TOKEN),
                                     (777002, '/usr/bin/tail -f /tmp/%s.txt' % self.TOKEN)]
        try:
            probe, detail = D.resolve_cli(job)
        finally:
            D.find_by_token = real
        self.assertNotEqual(probe, 'alive')
        self.assertIsNone(job['cli_pid'], '把一个读日志的进程认领成了自己的 CLI')
        self.assertEqual(job['cli_birth'], '', '拿别的进程改写了出生身份')
        self.assertIn('NOT claimed', detail)
        self.assertTrue(D.cli_unresolved(dict(job, receipt_state=(
            'cli_no_launch_record' if probe == 'no_launch_record' else 'unknown'))))

    def test_R24j_reclaim_accepts_the_real_cli_candidate(self):
        job = self.ident_job(cli_pid=None, cli_birth='')
        real_find, real_line = D.find_by_token, D.proc_line
        D.find_by_token = lambda t: [
            (777001, '/bin/cat /tmp/%s.stdout.jsonl' % self.TOKEN),
            (4242, self.BIN + ' --cwd /repo --prompt-file ' + self.PROMPT)]
        D.proc_line = lambda pid: self.BIRTH if pid == 4242 else 'unknown'
        try:
            probe, detail = D.resolve_cli(job)
        finally:
            D.find_by_token, D.proc_line = real_find, real_line
        self.assertEqual(probe, 'alive')
        self.assertEqual(job['cli_pid'], 4242)
        self.assertEqual(job['cli_birth'], self.BIRTH, '认领时没把出生身份记下来')
        self.assertIn('identity', detail)      # 措辞无关：只要求认领时核过身份

    def test_R24k_reclaim_never_overwrites_a_recorded_birth(self):
        """已经记过出生身份时，认领路径不得拿另一个进程把它洗成自己的。"""
        job = self.ident_job(cli_pid=None)         # birth 已记录
        other = 'Fri Sep 12 11:30:00 2026 ' + self.BIN + ' --cwd /repo --prompt-file ' + self.PROMPT
        real_find, real_line = D.find_by_token, D.proc_line
        D.find_by_token = lambda t: [(9999, self.BIN + ' --cwd /repo --prompt-file ' + self.PROMPT)]
        D.proc_line = lambda pid: other
        try:
            D.cli_reclaim(job, self.root, {'jobs': {}})
        finally:
            D.find_by_token, D.proc_line = real_find, real_line
        self.assertEqual(job['cli_birth'], self.BIRTH, '出生身份被另一个进程改写了')
        self.assertIsNone(job['cli_pid'], '认领了一个出生身份对不上的进程')

    def test_R24l_real_child_identity_and_one_sigint(self):
        """唯一用真实子进程的一条：本 suite 自己起的假 CLI，核验身份后发**一次** SIGINT。"""
        self.submit_cli('SLEEP', graceful_cancel=True)
        self.run_cli('tick')
        job = self.queue()['jobs']['G9']
        pid = job['cli_pid']
        self.addCleanup(self._kill, pid)
        self.assertTrue(job['cli_birth'], '启动时没记下出生身份')
        self.assertEqual(D.probe_cli(job), 'alive')
        line = D.proc_line(pid)
        self.assertEqual(D.cli_identity(job, line), 'match')
        # 同一个 pid，但假装出生身份换了 -> 立刻变成"不是我们的"
        self.assertEqual(D.cli_identity(dict(job, cli_birth=job['cli_birth'] + ' X'), line),
                         'mismatch')
        self.run_cli('pause')
        self.run_cli('tick')
        paused = self.queue()['jobs']['G9']
        self.assertEqual(paused.get('pause_signal'), 'SIGINT')
        self.assertTrue(Path(paused['journal']).exists(), '暂停把日志弄丢了')


# ------------- C06_R3：候选只是"找到人"，确认要用**当前这一次**读到的身份
class TestCandidateConfirmation(CliBase):
    """两个认领入口（`resolve_cli` / `cli_reclaim`）各写了一份判定，都漏了同一条不变量：
    `ps -ax` 扫到候选时那是真 CLI，随后 `proc_line(pid)` 读到的已经是 `tail`/`cat`，
    代码却把**新读到的那一行**存进 `cli_birth` 并当成自有，`cli_pause` 于是向它发 SIGINT。

    本轮把候选确认收敛成一个共用的小函数 `claim_candidate()`，两个入口都走它。
    下面按"二次读取读到什么"逐一过，并且**两个入口跑同一份用例**。
    """
    TOKEN = 'ciltok-G9-abc123'
    BIN = '/Users/ecool/.grok/bin/grok'
    PROMPT = '/tmp/ciltok-G9-abc123.txt'
    CLI_CMD = BIN + ' --cwd /repo --resume 041d93f0 --prompt-file ' + PROMPT
    SCAN_LINE = 'Fri Sep 12 10:00:00 2026 ' + CLI_CMD
    TAIL_LINE = 'Fri Sep 12 11:30:00 2026 /usr/bin/tail -f /tmp/ciltok-G9-abc123.stdout.jsonl'

    def cand_job(self, **extra):
        journal = self.tmp / 'cand.jsonl'
        journal.write_text('', encoding='utf-8')
        job = {'task_id': 'G9', 'owner': 'grok', 'transport': 'grok-cli', 'status': 'running',
               'owns_process': True, 'cli_pid': None, 'cli_token': self.TOKEN,
               'cli_birth': '', 'cli_bin': self.BIN, 'cli_prompt_copy': self.PROMPT,
               'cli_argv': [self.BIN, '--cwd', '/repo', '--prompt-file', self.PROMPT],
               'cli': {'bin': self.BIN, 'graceful_cancel': True},
               'journal': str(journal), 'receipt_state': 'unknown',
               'dependencies': [], 'created_at': D.now()}
        job.update(extra)
        return job

    def run_entry(self, entry, second_read, **extra):
        """两个入口跑同一份用例：扫描时是真 CLI，二次读取由 second_read 决定。"""
        job = self.cand_job(**extra)
        if entry == 'reclaim':
            job['status'] = 'blocked'
        real_find, real_line = D.find_by_token, D.proc_line
        D.find_by_token = lambda t: [(7777, self.CLI_CMD)]
        D.proc_line = lambda pid, _s=second_read: _s
        try:
            if entry == 'resolve':
                out = D.resolve_cli(job)
            else:
                D.cli_reclaim(job, self.root, {'jobs': {}})
                out = (None, job.get('receipt_detail', ''))
        finally:
            D.find_by_token, D.proc_line = real_find, real_line
        return job, out

    def pause_signals(self, job, second_read):
        sent = []
        real_line, real_kill = D.proc_line, os.kill
        D.proc_line = lambda pid, _s=second_read: _s
        os.kill = lambda pid, sig: sent.append((pid, sig))
        try:
            D.cli_pause(dict(job, status='running', pause_notice_sent=False), self.root)
        finally:
            D.proc_line, os.kill = real_line, real_kill
        return sent

    def _assert_not_claimed(self, entry, second, label):
        job, (probe, detail) = self.run_entry(entry, second)
        self.assertIsNone(job['cli_pid'], '%s / %s：认领了一个已经不是自己的 pid' % (entry, label))
        self.assertEqual(job['cli_birth'], '',
                         '%s / %s：把二次读到的那一行写成了出生身份' % (entry, label))
        self.assertNotIn('tail', job['cli_birth'] or '')
        self.assertEqual(self.pause_signals(job, second), [],
                         '%s / %s：向一个没确认的进程发了信号' % (entry, label))
        if probe is not None:
            self.assertNotEqual(probe, 'alive', '%s / %s：候选失效却报 alive' % (entry, label))
        self.assertTrue(D.cli_unresolved(job), '%s / %s：结局未定却当成有结论' % (entry, label))

    def test_R25_candidate_became_a_log_reader(self):
        for entry in ('resolve', 'reclaim'):
            self._assert_not_claimed(entry, self.TAIL_LINE, '二读变成 tail')

    def test_R25b_candidate_disappeared_between_the_two_reads(self):
        for entry in ('resolve', 'reclaim'):
            self._assert_not_claimed(entry, None, '二读读不到')

    def test_R25c_candidate_unverifiable_on_the_second_read(self):
        for entry in ('resolve', 'reclaim'):
            self._assert_not_claimed(entry, 'unknown', '二读读不了')

    def test_R25d_candidate_still_the_same_cli_is_claimed(self):
        for entry in ('resolve', 'reclaim'):
            job, (probe, detail) = self.run_entry(entry, self.SCAN_LINE)
            self.assertEqual(job['cli_pid'], 7777, '%s：真的还是同一个 CLI 却没认领' % entry)
            self.assertEqual(job['cli_birth'], self.SCAN_LINE,
                             '%s：认领时没把核验过的那一行记成出生身份' % entry)
            self.assertIn('re-verifying', detail)
            if probe is not None:
                self.assertEqual(probe, 'alive')
            self.assertEqual(self.pause_signals(job, self.SCAN_LINE), [(7777, signal.SIGINT)],
                             '%s：确认过身份却不发 graceful cancel' % entry)

    def test_R25e_recorded_birth_is_never_laundered_by_either_entry(self):
        """已经记过出生身份时，两个入口都不许拿另一个进程把它洗成自己的。"""
        other = self.SCAN_LINE.replace('10:00:00', '11:30:00')
        for entry in ('resolve', 'reclaim'):
            job, _ = self.run_entry(entry, other, cli_birth=self.SCAN_LINE)
            self.assertEqual(job['cli_birth'], self.SCAN_LINE, '%s：出生身份被洗了' % entry)
            self.assertIsNone(job['cli_pid'], '%s：认领了出生身份对不上的进程' % entry)
            self.assertEqual(self.pause_signals(job, other), [])

    def test_R25f_only_claim_candidate_writes_identity(self):
        """认领路径上写 cli_pid / cli_birth 的地方只有一处 —— 免得再各补一份不一致的判定。
        （launch/adopt 的身份是当场产生的，不走这条路。）"""
        src = Path(D.__file__).read_text(encoding='utf-8')
        body = src[src.index('def claim_candidate'):src.index('def launch_cli')]
        self.assertIn("job['cli_pid'] = pid", body)
        rest = src.replace(body, '')
        for frag in ("job['cli_pid'] = pid", "job['cli_birth'] = line"):
            self.assertNotIn(frag, rest, '认领身份的写入又散到别处了：%s' % frag)

    def test_R25g_real_grok_argv_with_spaces_still_matches(self):
        """真实 argv 里 `--allow Bash(git status*)` / `Edit(observer/web/**)` 带空格，
        结构核对不能因此失手。"""
        prompt = '/Users/ecool/.civ/prompts/ciltok-G03_FIX-9f.txt'
        job = {'cli_bin': self.BIN, 'cli_prompt_copy': prompt, 'cli_argv': [self.BIN]}
        command = (self.BIN + ' --cwd /Users/ecool/Desktop/civilization/civilization-sim'
                   ' --resume 041d93f0-5eae-4cff-90b8-f52785f14553'
                   ' --prompt-file ' + prompt +
                   ' --output-format json --permission-mode acceptEdits'
                   ' --allow Bash(git status*) --allow Bash(git add observer/web/*)'
                   ' --allow Edit(/Users/ecool/Desktop/civilization/civilization-sim/observer/web/**)'
                   ' --allow Edit(observer/web/**) --deny Bash(git push*)'
                   ' --max-turns 100 --no-subagents --disable-web-search')
        self.assertTrue(D.cli_command_matches(job, command),
                        'allow 规则里的空格把结构核对弄失手了')
        _, only_cmd = D.split_ps_line('Fri Sep 12 10:00:00 2026 ' + command)
        self.assertTrue(D.cli_command_matches(job, only_cmd))
        self.assertFalse(D.cli_command_matches(job, '/usr/bin/tail -f ' + prompt))
        self.assertFalse(D.cli_command_matches(job, '/bin/cat ' + prompt))


# ---------------- C06_R4：真实输出格式（整份 pretty JSON / streaming-json 分片）
REAL_PRETTY = json.dumps({
    "text": ("只修 pending404 跳年：等待绑在原目标年，记录到齐前不进入 126/130。\n\n"
             "受控状态测试（**不是**后台真实 404）：旧 da22 在 850ms 内会请求 126 和 130。\n\n"
             'CIV_RESULT_G03_R3 {"status":"done","branch":"main",'
             '"commit":"659b7261211f00e0e7cd244b2155b189bed72b3a",'
             '"tests":["node --check observer/web/app.js",'
             '"node observer/web/g03-r3-pending-test.mjs pass=20 fail=0"],'
             '"screenshots":["observer/web/screenshots/g03/r3-aid-83.png"],'
             '"blocking_reason":""}'),
    "stopReason": "end_turn",
    "sessionId": "fixture-session",
    "requestId": "fixture-request",
    "thought": "PRIVATE_THOUGHT_MUST_NOT_LEAK",
}, ensure_ascii=False, indent=2)


class TestJournalFormats(CliBase):
    """主控实测：`--output-format json` 的 stdout 是**整份一个缩进 JSON 对象**，
    逐行 `json.loads` 一条都解析不出来，于是"确认结束 + rc0 + 真实 end_turn + 唯一标记"
    被判成 `cli_no_unique_result`。`streaming-json` 又是另一回事：正文按
    `{"type":"text","data":"片段"}` 逐片段来，中间插换行会把跨片段的标记拆坏，
    而且 `type=thought` 的正文在 `data` 里、工具入参也可能带着假标记。
    """

    def judge(self, body, task='G03_R3', name=None):
        jp = self.tmp / ((name or task) + '.json')
        jp.write_text(body, encoding='utf-8')
        job = {'task_id': task, 'owner': 'grok', 'transport': 'grok-cli', 'status': 'running',
               'owns_process': True, 'cli_pid': None, 'cli_token': None, 'cli_rc': 0,
               'journal': str(jp), 'dependencies': [], 'created_at': D.now()}
        D.collect_cli(job, self.root)
        return job

    def frag(self, pieces, extra=()):
        lines = [json.dumps({'type': 'text', 'data': p}, ensure_ascii=False) for p in pieces]
        lines += [json.dumps(x, ensure_ascii=False) for x in extra]
        return '\n'.join(lines) + '\n'

    def test_R26_real_pretty_json_object_is_a_completed_turn(self):
        job = self.judge(REAL_PRETTY)
        self.assertEqual(job['status'], 'review',
                         '真实 pretty JSON 被判成了：%s' % job['receipt_detail'][:90])
        self.assertEqual(job['receipt_state'], 'durable_ok')
        self.assertEqual(job['report']['commit'],
                         '659b7261211f00e0e7cd244b2155b189bed72b3a')
        self.assertEqual(job['cli_stop_reason'], 'end_turn')
        self.assertEqual(job['cli_session_id'], 'fixture-session')
        self.assertEqual(job['report']['tests'][0], 'node --check observer/web/app.js')

    def test_R26b_private_thought_never_reaches_status_or_report(self):
        job = self.judge(REAL_PRETTY, name='thought')
        self.assertNotIn('PRIVATE_THOUGHT', job.get('last_output') or '')
        self.assertNotIn('PRIVATE_THOUGHT', json.dumps(job.get('report'), ensure_ascii=False))
        row = D.status_row(job)
        self.assertNotIn('PRIVATE_THOUGHT', json.dumps(row, ensure_ascii=False))

    def test_R26c_truncated_pretty_json_stays_unknown(self):
        """半个对象**不猜完成**：既不是完整对象，也解析不出任何一行。"""
        job = self.judge(REAL_PRETTY[:len(REAL_PRETTY) // 2], name='trunc')
        self.assertEqual(job['receipt_state'], 'cli_exited_incomplete')
        self.assertEqual(job['status'], 'blocked')
        self.assertNotIn('report', job)
        # 连标记都写全了、只是对象没闭合 —— 仍然不算完成
        job2 = self.judge(REAL_PRETTY[:-2], name='trunc2')
        self.assertEqual(job2['receipt_state'], 'cli_exited_incomplete')

    def test_R26d_streaming_fragments_are_joined_verbatim(self):
        body = self.frag(['干完了。', 'CIV_RESU', 'LT_G9 {"sta', 'tus":"done",',
                          '"commit":"FRAG"}'])
        job = self.judge(body, task='G9', name='frag')
        self.assertEqual(job['status'], 'review',
                         '跨片段的标记被拆坏了：%s' % job['receipt_detail'][:90])
        self.assertEqual(job['report']['commit'], 'FRAG')
        self.assertIn('no terminal record was recognised', job['receipt_detail'],
                      '没有终态记录时应当如实说明判定只靠标记')

    def test_R26e_fake_marker_in_thought_does_not_count(self):
        body = self.frag(['正在想办法。'], extra=[
            {'type': 'thought',
             'data': 'CIV_RESULT_G9 {"status":"done","commit":"FROM_THOUGHT"}'}])
        job = self.judge(body, task='G9', name='thought-marker')
        self.assertEqual(job['receipt_state'], 'cli_no_unique_result',
                         '私有思考里的假标记被当成了结果')
        self.assertNotIn('report', job)
        self.assertNotIn('FROM_THOUGHT', job.get('last_output') or '')

    def test_R26f_marker_in_tool_input_does_not_count(self):
        body = self.frag(['开始调用工具。'], extra=[
            {'type': 'tool_call', 'name': 'Bash',
             'data': {'command': 'echo CIV_RESULT_G9 {"status":"done","commit":"FROM_TOOL"}'}},
            {'type': 'tool_call_update', 'status': 'completed'},
            {'type': 'available_commands', 'data': ['/help']},
            {'type': 'usage', 'data': {'input_tokens': 10}}])
        job = self.judge(body, task='G9', name='tool-marker')
        self.assertEqual(job['receipt_state'], 'cli_no_unique_result',
                         '工具入参里的标记被当成了结果')
        self.assertNotIn('FROM_TOOL', job.get('last_output') or '')

    def test_R26g_prose_quota_word_still_not_a_quota_block(self):
        body = self.frag(['未触发额度限制。', 'CIV_RESULT_G9 {"status":"done","commit":"QP"}'],
                         extra=[{'text': '', 'stopReason': 'end_turn', 'sessionId': 's1'}])
        job = self.judge(body, task='G9', name='quota-prose')
        self.assertEqual(job['status'], 'review')
        self.assertEqual(job['report']['commit'], 'QP')

    def test_R26h_real_terminal_cancel_still_outranks_the_marker(self):
        body = self.frag(['CIV_RESULT_G9 {"status":"done","commit":"EARLY"}'],
                         extra=[{'text': '', 'stopReason': 'cancelled',
                                 'cancellationCategory': 'PermissionCancelled',
                                 'sessionId': 's1'}])
        job = self.judge(body, task='G9', name='cancel-frag')
        self.assertEqual(job['receipt_state'], 'permission_cancelled')
        self.assertNotIn('report', job)
        pretty_cancel = json.dumps({'text': 'CIV_RESULT_G9 {"status":"done","commit":"E2"}',
                                    'stopReason': 'cancelled',
                                    'cancellationCategory': 'PermissionCancelled'},
                                   ensure_ascii=False, indent=1)
        job2 = self.judge(pretty_cancel, task='G9', name='cancel-pretty')
        self.assertEqual(job2['receipt_state'], 'permission_cancelled')
        self.assertNotIn('report', job2)

    def test_R26i_acp_chunks_and_ndjson_still_work(self):
        """已有的两种格式不能因为这次兼容而失效。"""
        acp = '\n'.join(json.dumps({'params': {'update': {
            'sessionUpdate': 'agent_message_chunk', 'content': {'text': t}}}},
            ensure_ascii=False) for t in ['CIV_RESULT_G9 {"sta', 'tus":"done","commit":"ACP"}'])
        acp += '\n' + json.dumps({'params': {'update': {
            'sessionUpdate': 'agent_thought_chunk',
            'content': {'text': 'CIV_RESULT_G9 {"status":"done","commit":"ACPTHOUGHT"}'}}}}) + '\n'
        job = self.judge(acp, task='G9', name='acp')
        self.assertEqual(job['report']['commit'], 'ACP')
        nd = json.dumps({'type': 'assistant',
                         'text': 'CIV_RESULT_G9 {"status":"done","commit":"ND"}'}) + '\n'
        job2 = self.judge(nd, task='G9', name='nd')
        self.assertEqual(job2['report']['commit'], 'ND')

    def test_R26j_parse_journal_reports_completeness_honestly(self):
        self.assertEqual(D.parse_journal('')[1], True)
        self.assertEqual(D.parse_journal(REAL_PRETTY)[1], True)
        self.assertEqual(D.parse_journal(REAL_PRETTY[:80])[1], False)
        self.assertEqual(D.parse_journal('{"a":1}\n{"b":2}\n')[1], True)
        self.assertEqual(D.parse_journal('{"a":1}\n{"b":')[1], False)
        self.assertEqual(len(D.parse_journal(REAL_PRETTY)[0]), 1)
        self.assertEqual(len(D.parse_journal('{"a":1}\n{"b":2}\n')[0]), 2)


if __name__ == '__main__':
    unittest.main(verbosity=2)
