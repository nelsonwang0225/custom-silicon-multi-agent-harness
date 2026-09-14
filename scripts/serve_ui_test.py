#!/usr/bin/env python3
"""Owned isolated browser-test backend. No reset of the working database."""
import os
import signal
import subprocess
import sys
from pathlib import Path
from uuid import uuid4

PROJECT = Path(__file__).resolve().parents[1]
port = int(sys.argv[1]) if len(sys.argv) > 1 else 18000
run_id = uuid4().hex
path = PROJECT / '.demo' / f'ui-e2e-{run_id}.sqlite3'
env = {**os.environ, 'DEMO_MODE': 'true', 'DEMO_DB': str(path)}
command = [sys.executable, '-m', 'mock_enterprise.cli']
subprocess.run(command + ['init-demo'], cwd=PROJECT, env=env, check=True)
print('SCRIPTED BROWSER INTEGRATION TEST — ISOLATED DB; NO AI; SIMULATED ENGINEER.', flush=True)
print(f'Isolated database: {path}', flush=True)
server = subprocess.Popen(command + ['serve', '--port', str(port)], cwd=PROJECT, env=env)
shutdown_requested = False
def stop(signum, frame):
    global shutdown_requested
    shutdown_requested = True
    # Playwright may signal both the shell group and this supervisor. Do not
    # re-enter wait/cleanup when a second shutdown signal arrives.
    signal.signal(signal.SIGTERM, signal.SIG_IGN)
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    if server.poll() is None:
        server.terminate()
    # Return to the original wait. Waiting again inside a signal handler can
    # deadlock on Popen's waitpid lock until the supervisor timeout expires.
signal.signal(signal.SIGTERM, stop)
signal.signal(signal.SIGINT, stop)
try:
    code = server.wait()
finally:
    if server.poll() is None:
        server.terminate()
        server.wait(timeout=10)
raise SystemExit(0 if shutdown_requested else code)
