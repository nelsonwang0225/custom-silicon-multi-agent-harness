"""Development-only subprocess harness; never imported by the MCP service."""

from contextlib import contextmanager
import os
from pathlib import Path
import socket
import signal
import subprocess
import time

import httpx

PROJECT = Path(__file__).resolve().parents[1]
BACKEND_PYTHON = PROJECT / ".venv/bin/python"
MCP_PYTHON = PROJECT / "mcp_server/.venv/bin/python"


def process_env():
    # No inherited keys, credentials, proxies or dotenv files in either child.
    return {"PATH": os.defpath, "PYTHONPATH": str(PROJECT / "src"),
            "PYTHONUNBUFFERED": "1", "DEMO_MODE": "true"}


def free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


@contextmanager
def running(command, url, log_path, *, readiness="/health"):
    with log_path.open("w") as log:
        process = subprocess.Popen([str(x) for x in command], cwd=PROJECT, env=process_env(),
                                   stdin=subprocess.DEVNULL, stdout=log, stderr=log)
        try:
            deadline = time.monotonic() + 20
            with httpx.Client(trust_env=False, timeout=0.5) as http:
                while time.monotonic() < deadline:
                    if process.poll() is not None:
                        raise RuntimeError("Isolated service exited before readiness")
                    try:
                        if http.get(url + readiness).status_code == 200:
                            break
                    except httpx.HTTPError:
                        pass
                    time.sleep(0.05)
                else:
                    raise RuntimeError("Isolated service readiness deadline exceeded")
            yield process
        finally:
            if process.poll() is None:
                # Exercise the documented Ctrl-C shutdown path. Uvicorn
                # re-raises SIGTERM after graceful shutdown on current releases.
                process.send_signal(signal.SIGINT)
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
                raise RuntimeError("Isolated service did not shut down cleanly") from None


@contextmanager
def backend(storage, *, standard=False, quality=False, delivery=False):
    storage.mkdir(parents=True, exist_ok=True)
    url = f"http://127.0.0.1:{free_port()}"
    command = [BACKEND_PYTHON, PROJECT / "mcp_server/backend_fixture.py", "--storage", storage,
               "--port", url.rsplit(":", 1)[1]]
    if standard: command.append("--standard")
    if quality: command.append("--quality")
    if delivery: command.append("--delivery")
    with running(command, url, storage / "backend.log") as process:
        yield url, process


@contextmanager
def mcp_server(storage, backend_url, *, program_id="PRG-A17", customer_id="CUST-FML01", portfolio=False):
    port = free_port()
    url = f"http://127.0.0.1:{port}"
    command = [MCP_PYTHON, "-m", "stratos_mcp", "--port", port, "--backend-url", backend_url,
               "--program-id", program_id, "--customer-id", customer_id]
    if portfolio:
        command += ["--reader-identity", "demo-portfolio-reader-local-only"]
    with running(command, url, storage / f"mcp-{port}.log") as process:
        yield url, process


def fingerprint(storage):
    result = subprocess.run([str(BACKEND_PYTHON), str(PROJECT / "mcp_server/backend_fixture.py"),
                             "--storage", str(storage), "--fingerprint"],
                            cwd=PROJECT, env=process_env(), capture_output=True, text=True, timeout=10, check=True)
    value = result.stdout.strip()
    assert len(value) == 64 and all(c in "0123456789abcdef" for c in value)
    return value
