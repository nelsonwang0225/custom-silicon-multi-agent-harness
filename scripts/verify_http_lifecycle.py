#!/usr/bin/env python3
"""Process lifecycle harness; all business interactions delegated to HTTP smoke."""
import json
import os
import socket
import subprocess
import sys
import time
from pathlib import Path
from uuid import uuid4

import httpx

PROJECT = Path(__file__).resolve().parents[1]


def main():
    run_id = uuid4().hex
    artifacts = PROJECT / '.cache/http-lifecycle' / run_id
    artifacts.mkdir(parents=True)
    env = {**os.environ, 'DEMO_MODE': 'true', 'DEMO_DB': str(PROJECT / '.demo' / ('verify-' + run_id + '.sqlite3')),
           'TMPDIR': str(PROJECT / '.cache/tmp'), 'PYTHONUNBUFFERED': '1'}
    receipt = artifacts / 'receipt.json'
    command = [sys.executable, '-m', 'mock_enterprise.cli']
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        port = sock.getsockname()[1]
    url = f'http://127.0.0.1:{port}'
    server = None
    log = (artifacts / 'server.log').open('w')

    def run(args):
        result = subprocess.run(args, cwd=PROJECT, env=env, text=True, capture_output=True)
        if result.stdout:
            print(result.stdout, end='')
        if result.returncode:
            # These subprocesses only use synthetic data and sanitized service errors.
            print(result.stderr, file=sys.stderr)
            raise RuntimeError('Verification command failed')

    def start():
        process = subprocess.Popen(command + ['serve', '--port', str(port)], cwd=PROJECT, env=env, stdout=log, stderr=log)
        try:
            with httpx.Client(timeout=0.5, trust_env=False) as client:
                for _ in range(100):
                    if process.poll() is not None:
                        raise RuntimeError('Server exited before readiness')
                    try:
                        if client.get(url + '/health').status_code == 200:
                            return process
                    except httpx.HTTPError:
                        pass
                    time.sleep(0.05)
            raise RuntimeError('Server readiness timed out')
        except Exception:
            process.terminate()
            process.wait(timeout=10)
            raise

    def stop(process):
        process.terminate()
        process.wait(timeout=10)

    def smoke(mode):
        run([sys.executable, 'scripts/smoke_http.py', '--base-url', url, '--mode', mode, '--receipt', str(receipt)])

    try:
        run(command + ['init-demo'])
        server = start()
        smoke('workflow')
        stop(server)
        server = None
        server = start()
        smoke('verify')
        stop(server)
        server = None
        for _ in range(2):
            run(command + ['reset-demo', '--yes'])
            server = start()
            smoke('baseline')
            stop(server)
            server = None
        report = dict(status='PASS', base_url=url, database=env['DEMO_DB'], receipt=str(receipt),
                      workflow='PASS', real_process_restart='PASS', deterministic_reset_runs=2,
                      server_running=False, synthetic=True)
        (artifacts / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
        print(json.dumps(report, indent=2))
    finally:
        if server is not None and server.poll() is None:
            stop(server)
        log.close()


if __name__ == '__main__':
    main()
