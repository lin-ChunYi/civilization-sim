#!/usr/bin/env python3
"""Thin, local Cockpit dispatch queue. Uses existing authenticated sessions only."""
import argparse
import datetime as dt
import fcntl
import json
import os
from pathlib import Path
import re
import sys
import time
import uuid


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def atomic(path, value):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    tmp = path.with_name('.' + path.name + '.' + str(uuid.uuid4()) + '.tmp')
    with tmp.open('x', encoding='utf-8') as fh:
        os.chmod(tmp, 0o600)
        json.dump(value, fh, ensure_ascii=False, indent=2)
        fh.write('\n')
        fh.flush()
        os.fsync(fh.fileno())
    tmp.replace(path)


def read(path, default=None):
    return json.loads(path.read_text()) if path.exists() else default


def session(snapshot, job):
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


def assistant_text(path, offset, owner):
    if not path.exists():
        return ''
    if path.stat().st_size < offset:
        raise ValueError('transcript replaced or truncated; inspect before rebinding')
    with path.open('rb') as fh:
        fh.seek(offset)
        lines = fh.read().decode('utf-8', 'replace').splitlines()
    chunks = []
    for line in lines:
        try:
            item = json.loads(line)
        except ValueError:
            continue  # incomplete final record is not evidence
        if owner == 'claude' and item.get('type') == 'assistant':
            for content in item.get('message', {}).get('content', []):
                if isinstance(content, dict) and content.get('type') == 'text':
                    chunks.append(content.get('text', '') + '\n')
        elif owner == 'grok':
            update = item.get('params', {}).get('update', {})
            if update.get('sessionUpdate') == 'agent_message_chunk':
                chunks.append(update.get('content', {}).get('text', ''))
    return ''.join(chunks)


def collect(job, root, hub, snapshot):
    if job['status'] not in ('running', 'blocked') or not job.get('corr_id'):
        return
    corr = job['corr_id']
    result = hub / 'outbox' / (corr + '.result.json')
    err = hub / 'outbox' / (corr + '.err')
    if result.exists():
        receipt = read(result)
        job['receipt'] = receipt
        atomic(root / 'logs' / (job['task_id'] + '.receipt.json'), receipt)
        if receipt.get('ok') is False:
            job.update(status='blocked', blocking_reason='Cockpit delivery rejected; do not retry unknown delivery automatically')
            return
    elif err.exists():
        job.update(status='blocked', blocking_reason='Cockpit error receipt; inspect local outbox before retry')
        return
    elif time.time() - job['started_epoch'] > 120:
        job.update(status='blocked', blocking_reason='No durable receipt yet; outcome unknown, no automatic resend')
    try:
        current = session(snapshot, job)
        job['agent_state'] = current.get('state')
        job['pending_count'] = len(current.get('pending') or [])
        text = assistant_text(Path(job['transcript']), job['transcript_offset'], job['owner'])
        if text:
            log = root / 'logs' / (job['task_id'] + '.assistant.txt')
            log.write_text(text, encoding='utf-8')
            os.chmod(log, 0o600)
            job['output_log'] = str(log)
            job['last_output'] = text[-1200:]
        # Only assistant output after this dispatch counts. JSON must be one line.
        matches = re.findall(re.escape('CIV_RESULT_' + job['task_id']) + r'\s+(\{[^\n]*\})', text)
        if matches:
            report = json.loads(matches[-1])
            job['report'] = report
            if current.get('state') in ('waiting', 'idle'):
                job['status'] = 'blocked' if report.get('status') == 'blocked' else 'review'
                job['finished_at'] = now()
                job['blocking_reason'] = report.get('blocking_reason', '')
        elif job.get('pending_count'):
            job['attention'] = 'Agent has a permission/question item; inspect transcript, do not blanket approve'
    except (ValueError, OSError) as exc:
        job['attention'] = str(exc)


def dispatch(job, root, hub, snapshot, queue):
    current = session(snapshot, job)
    if current.get('state') not in ('waiting', 'idle') or current.get('pending'):
        raise ValueError('target is not at an idle turn boundary')
    if not current.get('claude_pid'):
        raise ValueError('existing session has no live PID; do not guess a resume command')
    path = hub / 'transcript' / job['device_id'] / (job['session_id'] + '.jsonl')
    if not path.exists():
        raise ValueError('transcript missing; request history before dispatch')
    corr = str(uuid.uuid4()).upper()
    envelope = {'corr_id': corr, 'device_id': job['device_id'], 'session_id': job['session_id'],
                'op': 'reply_inject', 'data': {'text': Path(job['prompt_file']).read_text()}}
    job.update(status='running', corr_id=corr, started_at=now(), started_epoch=time.time(),
               transcript=str(path), transcript_offset=path.stat().st_size,
               registered_pid=current['claude_pid'], owns_session=False)
    # Persist the claim before publishing. A crash must never cause a duplicate dispatch.
    atomic(root / 'queue.json', queue)
    atomic(root / 'logs' / (job['task_id'] + '.command.json'), envelope)
    atomic(hub / 'outbox' / (corr + '.json'), envelope)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--state-dir', type=Path, default=Path(__file__).resolve().parents[1] / '.dispatch')
    ap.add_argument('--hub-dir', type=Path, default=Path.home() / '.cockpit' / 'hub')
    sub = ap.add_subparsers(dest='command', required=True)
    sub.add_parser('submit').add_argument('job_file', type=Path)
    for name in ('tick', 'status', 'pause', 'resume'):
        sub.add_parser(name)
    done = sub.add_parser('accept')
    done.add_argument('task_id')
    done.add_argument('--evidence', required=True)
    args = ap.parse_args()
    root, hub = args.state_dir.resolve(), args.hub_dir.resolve()
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    with (root / 'controller.lock').open('a+') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise SystemExit('Another controller operation holds the project lock')
        queue = read(root / 'queue.json', {'paused': False, 'jobs': {}})
        if args.command == 'submit':
            job = read(args.job_file)
            for field in ('task_id', 'owner', 'objective', 'allowed_paths', 'baseline_sha', 'dependencies',
                          'acceptance', 'workdir', 'branch', 'device_id', 'session_id', 'session_cwd', 'prompt_file'):
                if field not in job:
                    raise ValueError('missing task field: ' + field)
            if job['owner'] not in ('claude', 'grok') or not re.fullmatch(r'[A-Z0-9_]+', job['task_id']):
                raise ValueError('owner/task_id rejected')
            if job['task_id'] in queue['jobs']:
                raise ValueError('task already exists; use a new revision ID')
            job.update(status='pending', created_at=now())
            queue['jobs'][job['task_id']] = job
        elif args.command == 'pause':
            queue['paused'] = True  # drains existing turns; never kills borrowed sessions
        elif args.command == 'resume':
            queue['paused'] = False
        elif args.command == 'accept':
            job = queue['jobs'][args.task_id]
            if job['status'] != 'review':
                raise ValueError('only an independently reviewed task can be accepted')
            if not Path(args.evidence).is_file():
                raise ValueError('acceptance evidence file does not exist')
            job.update(status='done', accepted_at=now(), acceptance_evidence=str(Path(args.evidence).resolve()))
        else:
            snapshot_path = hub / 'snapshot.json'
            snapshot = read(snapshot_path, {})
            for job in queue['jobs'].values():
                collect(job, root, hub, snapshot)
            if args.command == 'tick' and not queue['paused']:
                if time.time() - snapshot_path.stat().st_mtime > 60:
                    raise ValueError('Cockpit snapshot is stale; no dispatch')
                active = {j['owner'] for j in queue['jobs'].values() if j['status'] in ('running', 'blocked')}
                for job in queue['jobs'].values():
                    if job['status'] != 'pending' or job['owner'] in active:
                        continue
                    if any(queue['jobs'].get(dep, {}).get('status') != 'done' for dep in job['dependencies']):
                        continue
                    try:
                        dispatch(job, root, hub, snapshot, queue)
                        active.add(job['owner'])
                    except (ValueError, OSError) as exc:
                        job['blocking_reason'] = str(exc)
        queue['updated_at'] = now()
        atomic(root / 'queue.json', queue)
        print(json.dumps({'paused': queue['paused'], 'jobs': [{k: j.get(k) for k in
              ('task_id', 'owner', 'status', 'agent_state', 'corr_id', 'blocking_reason', 'attention', 'report')}
              for j in queue['jobs'].values()]}, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
