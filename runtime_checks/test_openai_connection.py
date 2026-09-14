"""Offline tests: fake credentials and MockTransport; never read .env.local."""

import json
import logging

import httpx
import pytest

from runtime_checks import openai_connection as check

FAKE_KEY = "sk-" + "synthetic_offline_only_" * 3


@pytest.fixture
def env_file(tmp_path):
    path = tmp_path / ".env.local"
    path.write_text(f"OPENAI_API_KEY='{FAKE_KEY}'\n")
    path.chmod(0o600)
    return path


@pytest.fixture(autouse=True)
def isolate_sdk(monkeypatch):
    # Any accidental default transport is blocked even if the real key is set.
    def deny_network(*args, **kwargs):
        raise AssertionError("Offline test attempted network access")
    monkeypatch.setattr(httpx.HTTPTransport, "handle_request", deny_network)
    for name in ("OPENAI_API_KEY", "OPENAI_CUSTOM_HEADERS", "OPENAI_ORG_ID", "OPENAI_PROJECT_ID"):
        monkeypatch.delenv(name, raising=False)


def mock_response(monkeypatch, handler):
    monkeypatch.setattr(
        check.openai, "DefaultHttpxClient",
        lambda **kwargs: httpx.Client(transport=httpx.MockTransport(handler), **kwargs),
    )


def success_body(*, status="completed", text=check.EXPECTED_OUTPUT):
    return {
        "id": "resp_offline_test", "object": "response", "created_at": 0,
        "model": check.MODEL, "status": status,
        "output": [{"id": "msg_offline_test", "type": "message", "role": "assistant",
                    "status": "completed", "content": [{"type": "output_text", "text": text, "annotations": []}]}],
        "usage": {"input_tokens": 10, "output_tokens": 5, "total_tokens": 15,
                  "input_tokens_details": {"cached_tokens": 0},
                  "output_tokens_details": {"reasoning_tokens": 0}},
    }


def test_single_request_and_metadata_only(env_file, monkeypatch, capsys):
    requests = []
    monkeypatch.setenv("OPENAI_API_KEY", "unrelated_environment_value")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://example.invalid/v1")
    def handler(request):
        requests.append(request)
        assert str(request.url) == "https://api.openai.com/v1/responses"
        assert request.method == "POST"
        assert request.headers["authorization"] == f"Bearer {FAKE_KEY}"
        assert json.loads(request.content) == {
            "model": check.MODEL, "input": check.PROMPT,
            "reasoning": {"effort": "low"}, "max_output_tokens": 128, "store": False,
        }
        logging.getLogger("openai").critical(FAKE_KEY)
        return httpx.Response(200, json=success_body())
    mock_response(monkeypatch, handler)
    report = check.check_connection(env_file)
    assert len(requests) == 1
    assert report["success"] is True
    assert report["authentication_succeeded"] is True
    assert report["usage"]["total_tokens"] == 15
    assert report["request_latency_ms"] >= 0
    captured = capsys.readouterr()
    assert not captured.out and not captured.err
    assert FAKE_KEY not in json.dumps(report)
    assert check.EXPECTED_OUTPUT not in json.dumps(report)


@pytest.mark.parametrize("status,code", [(401, "invalid_api_key"), (429, "insufficient_quota"), (500, "server_error")])
def test_errors_do_not_retry_or_expose_bodies(env_file, monkeypatch, capsys, status, code):
    requests = []
    def handler(request):
        requests.append(request)
        return httpx.Response(status, json={"error": {"message": FAKE_KEY, "code": code, "type": "api_error"}})
    mock_response(monkeypatch, handler)
    report = check.check_connection(env_file)
    assert len(requests) == report["requests_attempted"] == 1
    assert report["success"] is False
    assert report["http_status"] == status
    assert report["authentication_succeeded"] is (False if status == 401 else None)
    assert FAKE_KEY not in json.dumps(report)
    captured = capsys.readouterr()
    assert not captured.out and not captured.err


@pytest.mark.parametrize("status,text", [("incomplete", check.EXPECTED_OUTPUT), ("completed", "unexpected reply")])
def test_incomplete_or_unexpected_output_is_not_success(env_file, monkeypatch, status, text):
    mock_response(monkeypatch, lambda request: httpx.Response(200, json=success_body(status=status, text=text)))
    report = check.check_connection(env_file)
    assert report["success"] is False
    assert report["authentication_succeeded"] is True


@pytest.mark.parametrize("condition", ["missing", "permissions", "symlink", "interpolation"])
def test_invalid_local_config_never_sends(env_file, monkeypatch, condition):
    monkeypatch.setenv("OPENAI_API_KEY", FAKE_KEY)
    if condition == "missing":
        env_file.unlink()
    elif condition == "permissions":
        env_file.chmod(0o644)
    elif condition == "symlink":
        original = env_file.with_name("saved.env")
        env_file.rename(original)
        env_file.symlink_to(original)
    else:
        env_file.write_text("OPENAI_API_KEY=${OPENAI_API_KEY}\n")
    report = check.check_connection(env_file)
    assert report["response_status"] == "local_configuration_error"
    assert report["requests_attempted"] == 0
    assert report["success"] is False


def test_timeout_is_safe_and_not_retried(env_file, monkeypatch):
    requests = []
    def handler(request):
        requests.append(request)
        raise httpx.ReadTimeout(FAKE_KEY, request=request)
    mock_response(monkeypatch, handler)
    report = check.check_connection(env_file)
    assert len(requests) == 1
    assert report["response_status"] == "timeout"
    assert report["authentication_succeeded"] is None
    assert FAKE_KEY not in json.dumps(report)
