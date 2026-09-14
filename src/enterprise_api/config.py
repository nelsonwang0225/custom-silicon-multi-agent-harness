"""Explicit local connection settings and immutable customer/program scope."""

import ipaddress
from typing import Annotated, Literal
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, field_validator

RecordID = Annotated[str, Field(strict=True, min_length=1, max_length=100, pattern=r"^[A-Za-z0-9_-]+$")]
ReaderIdentity = Literal["demo-reader-local-only", "demo-portfolio-reader-local-only"]


class Scope(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", hide_input_in_errors=True)
    program_id: RecordID
    customer_id: RecordID


class ClientConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", hide_input_in_errors=True)
    scope: Scope
    base_url: str = "http://127.0.0.1:8000"
    reader_identity: ReaderIdentity = "demo-reader-local-only"
    connect_timeout: float = Field(default=2.0, gt=0, le=30, allow_inf_nan=False)
    read_timeout: float = Field(default=10.0, gt=0, le=60, allow_inf_nan=False)
    max_retries: int = Field(default=2, strict=True, ge=0, le=2)
    retry_backoff: float = Field(default=0.1, ge=0, le=0.5, allow_inf_nan=False)

    @field_validator("base_url")
    @classmethod
    def local_origin_only(cls, value: str) -> str:
        try:
            url = urlsplit(value)
            local = url.hostname == "localhost" or ipaddress.ip_address(url.hostname or "").is_loopback
            valid = (not any(ord(char) <= 32 for char in value) and "?" not in value and "#" not in value
                     and url.scheme in {"http", "https"} and local and url.username is None
                     and url.password is None and url.path in {"", "/"}
                     and not url.query and not url.fragment and (url.port is None or 0 < url.port < 65536))
        except ValueError:
            valid = False
        if not valid:
            raise ValueError("Backend must be a loopback HTTP(S) origin without credentials, query or path")
        return value.rstrip("/")
