"""Safe exception metadata excludes HTTP requests, bodies, headers and credentials."""

from dataclasses import asdict, dataclass
from typing import Literal

ErrorKind = Literal["input", "unauthenticated", "forbidden", "not_found", "conflict",
                    "validation", "server", "http", "timeout", "connection",
                    "invalid_response", "scope", "closed"]


@dataclass(frozen=True)
class ErrorInfo:
    kind: ErrorKind
    code: str
    http_status: int | None = None
    retryable: bool = False
    attempts: int = 0
    request_id: str | None = None
    correlation_id: str | None = None


class EnterpriseAPIError(Exception):
    def __init__(self, info: ErrorInfo):
        self.info = info
        super().__init__(f"Enterprise API {info.kind}: {info.code}")

    def to_dict(self) -> dict:
        """JSON-serializable error metadata for direct callers and a future MCP adapter."""
        return asdict(self.info)
