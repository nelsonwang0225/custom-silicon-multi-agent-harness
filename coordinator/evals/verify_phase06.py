"""SCRIPTED MOCK-SYSTEM INTEGRATION TEST — NO AI; ENGINEER IDENTITY SIMULATED.

Creates new isolated cache storage and crosses real localhost HTTP boundaries.
Exercises existing CLI in separate processes, source restart, review and replay.
Never resets or modifies a working demo. Run with the backend environment.
"""
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
from uuid import uuid4

import httpx
from mock_enterprise.app import create_app
from mock_enterprise.config import Settings
from mock_enterprise.seed import initialize

ROOT = Path(__file__).resolve().parents[2]
NOTICE = 'SCRIPTED MOCK-SYSTEM INTEGRATION TEST — NO AI INFERENCE; ENGINEER IDENTITY IS SIMULATED.'


def main():
    if len(sys.argv) > 1 and sys.argv[1] == '--serve':
        import uvicorn
        directory = Path(sys.argv[2])
        uvicorn.run(create_app(Settings(directory / 'enterprise.sqlite3', directory, True)),
                    host='127.0.0.1', port=int(sys.argv[3]), access_log=False, log_level='warning')
        return
    print(NOTICE)
    artifacts = ROOT / '.cache/phase06' / ('http-' + uuid4().hex)
    artifacts.mkdir(parents=True)
    settings = Settings(artifacts / 'enterprise.sqlite3', artifacts, True)
    initialize(settings)
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0)); port = sock.getsockname()[1]
    url = f'http://127.0.0.1:{port}'
    metadata = artifacts / 'activity'
    env = {**os.environ, 'PYTHONPATH': str(ROOT / 'src'), 'DEMO_MODE': 'true'}
    env.pop('OPENAI_API_KEY', None)
    python = str(ROOT / 'coordinator/.venv/bin/python')
    cli = [python, '-m', 'program_coordinator', '--metadata-dir', str(metadata), '--source-url', url]
    server = None
    log = (artifacts / 'server.log').open('w')

    def start():
        process = subprocess.Popen([sys.executable, str(Path(__file__).resolve()), '--serve', str(artifacts), str(port)],
            cwd=ROOT, env=env, stdout=log, stderr=log)
        try:
            with httpx.Client(trust_env=False, timeout=.5) as http:
                for _ in range(100):
                    if process.poll() is not None: raise RuntimeError('Source exited')
                    try:
                        if http.get(url + '/health').status_code == 200: return process
                    except httpx.HTTPError: pass
                    time.sleep(.05)
            raise RuntimeError('Readiness timeout')
        except BaseException:
            process.terminate(); process.wait(timeout=10); raise

    def command(name, args, expected=0):
        result = subprocess.run(args, cwd=ROOT, env=env, capture_output=True, text=True, timeout=60)
        (artifacts / (name + '.json')).write_text(result.stdout)
        if result.returncode != expected:
            raise RuntimeError(f'{name} exited {result.returncode}; inspect {artifacts / (name + ".json")}')
        return json.loads(result.stdout)

    try:
        server = start()
        analysis = command('analysis', [python, str(ROOT / 'coordinator/evals/phase06_offline_analysis.py'), '--metadata-dir', str(metadata)])
        proposal = command('proposal', cli + ['--phase06', 'prepare', '--run-id', analysis['run_id'], '--preparation-id', 'http_preparation'])
        ref = proposal['reference']
        exact = ['--run-id', ref['run_id'], '--case-id', ref['case_id'], '--proposal-id', ref['proposal_id'],
                 '--proposal-version', str(ref['proposal_version']), '--proposal-digest', ref['proposal_digest']]
        denied = command('no-approval', cli + ['--phase06', 'resume'] + exact, expected=2)
        assert denied['error_code'] == 'APPROVAL_REQUIRED'
        command('review', cli + ['--phase06', 'review', '--decision', 'approve', '--comment', 'Scripted simulated engineer approval.'] + exact)
        server.terminate(); server.wait(timeout=10); server = start()
        execution = command('execution', cli + ['--phase06', 'resume'] + exact)
        assert execution['status'] == 'completed_execution'
        prepared_replay = command('preparation-replay', cli + ['--phase06', 'prepare', '--run-id', analysis['run_id'],
                                 '--preparation-id', 'http_preparation'])
        assert prepared_replay['status'] == 'completed_execution' and prepared_replay['reference'] == ref
        command('replay', cli + ['--phase06', 'resume'] + exact)
        final = command('inspection', cli + ['--phase06', 'inspect'] + exact)
        assert len(final['attempts']) == 2 and all(v['outcome'] == 'matched' for v in final['verification'])
        assert final['execution']['case_status'] == 'in_validation'
        with httpx.Client(trust_env=False, headers={'Authorization': 'Bearer demo-reader-local-only'}) as http:
            jobs = http.get(url + '/api/v1/validation/jobs', params={'change_id': 'CR-017'}).json()['items']
            links = http.get(url + '/api/v1/programs/PRG-A17/implementation-links', params={'change_id': 'CR-017'}).json()['items']
            assert len(jobs) == len(links) == 1
        report = {'status': 'PASS', 'notice': NOTICE, 'analysis': analysis['mode'], 'paid_model_calls': 0,
                  'proposal_id': ref['proposal_id'], 'job_id': jobs[0]['id'], 'link_id': links[0]['id'],
                  'source_restart': True, 'cli_process_resume': True, 'attempts': len(final['attempts']),
                  'verification_records': len(final['verification']), 'case_closed': False, 'artifacts': str(artifacts)}
        (artifacts / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
        print(json.dumps(report, indent=2))
    finally:
        if server is not None and server.poll() is None:
            server.terminate(); server.wait(timeout=10)
        log.close()


if __name__ == '__main__': main()
