"""One live Responses request, with metadata-only output and no automatic retries."""

from __future__ import annotations

import contextlib
import argparse
import io
import json
import logging
import os
from pathlib import Path
import re
import stat
import time

import openai
from dotenv import dotenv_values

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODEL = "gpt-6-astra"
PROMPT = "Reply with exactly: API connection successful"
EXPECTED_OUTPUT = "API connection successful"
API_BASE_URL = "https://api.openai.com/v1"


class LocalConfigurationError(Exception):
    """Configuration failure with a fixed, non-sensitive category."""


def load_local_key(env_file: Path) -> str:
    """Read only this file; do not source shell code or expand environment values."""
    try:
        fd = os.open(env_file, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        with os.fdopen(fd, "r", encoding="utf-8") as handle:
            info = os.fstat(handle.fileno())
            if (
                not stat.S_ISREG(info.st_mode)
                or stat.S_IMODE(info.st_mode) != 0o600
                or info.st_uid != os.getuid()
                or info.st_nlink != 1
                or info.st_size > 65536
            ):
                raise LocalConfigurationError("unsafe_env_file")
            values = dotenv_values(stream=handle, interpolate=False)
    except (OSError, UnicodeError):
        raise LocalConfigurationError("env_file_unavailable") from None
    key = values.get("OPENAI_API_KEY")
    if not key or not re.fullmatch(r"sk-[A-Za-z0-9_-]{20,1024}", key):
        raise LocalConfigurationError("key_missing_or_invalid_format")
    return key


def _token_count(value: object) -> int | None:
    return value if type(value) is int and value >= 0 else None


def check_connection(env_file: Path | None = None) -> dict:
    """Run explicitly, never at import. Return only allowlisted, safe metadata.

    This standalone synchronous check temporarily suppresses diagnostics. It is
    not intended to run inside the business server or a multithreaded process.
    """
    report = {
        "model": MODEL,
        "response_status": "not_requested",
        "http_status": None,
        "request_latency_ms": None,
        "usage": None,
        "authentication_succeeded": None,
        "output_matches_expected": None,
        "requests_attempted": 0,
        "success": False,
    }
    previous_logging_disable = logging.root.manager.disable
    started = None
    # SDK error messages and debug output may contain request/response details.
    # Never forward them to stdout, stderr, a file, or an exception traceback.
    logging.disable(logging.CRITICAL)
    try:
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            key = load_local_key(env_file if env_file is not None else PROJECT_ROOT / ".env.local")
            if os.environ.get("OPENAI_CUSTOM_HEADERS"):
                raise LocalConfigurationError("custom_headers_not_supported")
            with openai.OpenAI(
                api_key=key,
                base_url=API_BASE_URL,
                max_retries=0,
                timeout=60.0,
                http_client=openai.DefaultHttpxClient(trust_env=False, follow_redirects=False),
            ) as client:
                started = time.perf_counter()
                report["requests_attempted"] = 1
                raw = client.responses.with_raw_response.create(
                    model=MODEL,
                    input=PROMPT,
                    reasoning={"effort": "low"},
                    max_output_tokens=128,
                    store=False,
                )
                report["request_latency_ms"] = round((time.perf_counter() - started) * 1000, 2)
                report["http_status"] = raw.status_code
                report["authentication_succeeded"] = 200 <= raw.status_code < 300
                response = raw.parse()
                report["response_status"] = response.status if response.status in {
                    "completed", "failed", "in_progress", "cancelled", "queued", "incomplete"
                } else "unexpected_status"
                # Accept only the requested model or its dated snapshot name.
                if not isinstance(response.model, str) or not re.fullmatch(
                    r"gpt-6-astra(?:-\d{4}-\d{2}-\d{2})?", response.model
                ):
                    report["error_category"] = "unexpected_response_model"
                    return report
                report["model"] = response.model
                report["output_matches_expected"] = response.output_text == EXPECTED_OUTPUT
                if response.usage is not None:
                    usage = response.usage
                    report["usage"] = {
                        "input_tokens": _token_count(usage.input_tokens),
                        "output_tokens": _token_count(usage.output_tokens),
                        "total_tokens": _token_count(usage.total_tokens),
                        "cached_input_tokens": _token_count(getattr(usage.input_tokens_details, "cached_tokens", None)),
                        "reasoning_tokens": _token_count(getattr(usage.output_tokens_details, "reasoning_tokens", None)),
                    }
                report["success"] = (
                    report["authentication_succeeded"]
                    and report["response_status"] == "completed"
                    and report["output_matches_expected"]
                )
    except LocalConfigurationError as exc:
        report["response_status"] = "local_configuration_error"
        report["error_category"] = exc.args[0]
    except openai.APIStatusError as exc:
        report["response_status"] = "http_error"
        report["http_status"] = exc.status_code
        report["authentication_succeeded"] = False if exc.status_code == 401 else None
        known_codes = {
            "invalid_api_key", "insufficient_quota", "model_not_found",
            "rate_limit_exceeded", "permission_denied", "unsupported_parameter",
            "invalid_value", "invalid_request_error",
        }
        report["error_category"] = exc.code if isinstance(exc.code, str) and exc.code in known_codes else "api_error"
    except openai.APITimeoutError:
        report["response_status"] = "timeout"
        report["error_category"] = "request_timeout"
    except openai.APIConnectionError:
        report["response_status"] = "connection_error"
        report["error_category"] = "network_or_tls_error"
    except Exception:
        report["response_status"] = "local_error"
        report["error_category"] = "unexpected_client_error"
    finally:
        if started is not None and report["request_latency_ms"] is None:
            report["request_latency_ms"] = round((time.perf_counter() - started) * 1000, 2)
        logging.disable(previous_logging_disable)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Make one live OpenAI Responses connection check; print only safe metadata.")
    parser.parse_args()
    report = check_connection()
    print(json.dumps(report, indent=2))
    return 0 if report["success"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
