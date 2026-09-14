"""Regression for the owned browser-test supervisor, never the working API."""
import os
import signal
import socket
import subprocess
import sys
import time

import httpx

from mock_enterprise.config import PROJECT


def test_ui_supervisor_group_shutdown_does_not_reenter_wait():
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        port = sock.getsockname()[1]
    process = subprocess.Popen(
        [sys.executable, str(PROJECT / 'scripts/serve_ui_test.py'), str(port)],
        cwd=PROJECT, start_new_session=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    )
    try:
        deadline = time.monotonic() + 10
        with httpx.Client(timeout=0.3) as client:
            while True:
                try:
                    response = client.get(f'http://127.0.0.1:{port}/health')
                    if response.status_code == 200:
                        break
                except httpx.TransportError:
                    pass
                assert process.poll() is None, 'Owned test API exited before readiness'
                assert time.monotonic() < deadline, 'Owned test API did not become ready'
                time.sleep(0.05)
        os.killpg(process.pid, signal.SIGTERM)
        stdout, stderr = process.communicate(timeout=4)
        assert process.returncode == 0, stderr
        assert 'Traceback' not in stderr
        assert 'SCRIPTED BROWSER INTEGRATION TEST' in stdout
        assert 'ui-e2e-' in stdout
    finally:
        # Only the dedicated process group created by this test can be stopped.
        if process.poll() is None:
            os.killpg(process.pid, signal.SIGKILL)
            process.communicate(timeout=4)
