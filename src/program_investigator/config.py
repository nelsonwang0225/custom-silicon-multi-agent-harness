"""Trusted local configuration. No key values in configuration objects or reprs."""

import contextlib
import io
import os
from pathlib import Path
import re
import stat
from urllib.parse import urlsplit

from dotenv import dotenv_values
from pydantic import BaseModel, ConfigDict, Field, field_validator

MODEL = "gpt-6-astra"
PROJECT = Path(__file__).resolve().parents[2]


class InvestigatorError(Exception):
    """Only fixed, non-sensitive error codes may be supplied by this package."""


class InvestigatorConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", hide_input_in_errors=True)
    mcp_url: str = "http://127.0.0.1:9000/mcp"
    max_turns: int = Field(default=24, ge=1, le=30, strict=True)
    model_timeout_seconds: float = Field(default=180, gt=0, le=300)
    run_timeout_seconds: float = Field(default=900, gt=0, le=1200)

    @field_validator("mcp_url")
    @classmethod
    def local_mcp_only(cls, value: str) -> str:
        try:
            url = urlsplit(value)
            valid = (url.scheme == "http" and url.hostname in {"127.0.0.1", "localhost", "::1"}
                     and url.username is None and url.password is None and url.path == "/mcp"
                     and "?" not in value and "#" not in value and 0 < (url.port or 80) < 65536
                     and not any(ord(c) <= 32 for c in value))
        except ValueError:
            valid = False
        if not valid:
            raise ValueError("Expected a credential-free loopback HTTP /mcp endpoint")
        return value.replace("//localhost", "//127.0.0.1")


def load_key(path: Path) -> str:
    """Read only the authorized owner-only regular file, without interpolation/logs."""
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        with os.fdopen(fd, encoding="utf-8") as handle:
            info = os.fstat(handle.fileno())
            if (not stat.S_ISREG(info.st_mode) or stat.S_IMODE(info.st_mode) != 0o600
                    or info.st_uid != os.getuid() or info.st_nlink != 1 or info.st_size > 65536):
                raise InvestigatorError("unsafe_env_file")
            with contextlib.redirect_stderr(io.StringIO()):
                values = dotenv_values(stream=handle, interpolate=False)
    except (OSError, UnicodeError):
        raise InvestigatorError("env_file_unavailable") from None
    key = values.get("OPENAI_API_KEY")
    if not key or not re.fullmatch(r"sk-[A-Za-z0-9_-]{20,1024}", key):
        raise InvestigatorError("key_missing_or_invalid_format")
    if os.environ.get("OPENAI_CUSTOM_HEADERS"):
        raise InvestigatorError("custom_headers_not_supported")
    return key
