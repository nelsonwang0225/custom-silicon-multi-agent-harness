"""Internal read transport seam. Domain methods never expose a raw URL interface."""

from dataclasses import dataclass
import re
import time
from typing import Protocol
from uuid import uuid4

import httpx
from pydantic import JsonValue

from .config import ClientConfig
from .errors import EnterpriseAPIError, ErrorInfo


@dataclass(frozen=True)
class ReadResponse:
    status: int
    body: JsonValue
    attempts: int = 1
    request_id: str | None = None
    correlation_id: str | None = None
    server_correlation_id: str | None = None


class ReadTransport(Protocol):
    def get(self, path: str, params: dict[str, str]) -> ReadResponse: ...
    def close(self) -> None: ...


RETRY_STATUSES = frozenset({502, 503, 504})


class HttpxReadTransport:
    """GET-only adapter with fixed reader headers and a maximum of three attempts."""

    def __init__(self, config: ClientConfig, *, http_client: httpx.Client | None = None,
                 correlation_id: str | None = None):
        # Trusted adapters can correlate several GETs with one calling operation.
        # Never accept free-form headers or an externally supplied credential here.
        if correlation_id is not None and not re.fullmatch(r"corr-[a-f0-9]{32}", correlation_id):
            raise EnterpriseAPIError(ErrorInfo("input", "INVALID_CORRELATION_ID"))
        self._correlation_id = correlation_id
        self._config = config
        self._timeout = httpx.Timeout(connect=config.connect_timeout, read=config.read_timeout,
                                      write=config.connect_timeout, pool=config.connect_timeout)
        self._owns_client = http_client is None
        self._http = http_client if http_client is not None else httpx.Client(
            trust_env=False, follow_redirects=False, timeout=self._timeout,
        )

    def get(self, path: str, params: dict[str, str]) -> ReadResponse:
        if not re.fullmatch(r"/api/v1/[A-Za-z0-9_/-]+", path) or "//" in path:
            raise EnterpriseAPIError(ErrorInfo("input", "INVALID_PATH"))
        correlation = self._correlation_id or "corr-" + uuid4().hex
        for attempt in range(1, self._config.max_retries + 2):
            retry = False
            try:
                request = self._http.build_request(
                    "GET", self._config.base_url + path, params=params, timeout=self._timeout,
                    headers={"Authorization": "Bearer " + self._config.reader_identity,
                             "Accept": "application/json", "X-Correlation-ID": correlation},
                )
                response = self._http.send(request, follow_redirects=False)
                retry = response.status_code in RETRY_STATUSES
                if not retry or attempt > self._config.max_retries:
                    try:
                        body = response.json()
                    except (ValueError, UnicodeError):
                        body = None
                    request_id = response.headers.get("x-request-id", "")
                    echoed = response.headers.get("x-correlation-id", "")
                    return ReadResponse(response.status_code, body, attempt,
                                        request_id if re.fullmatch(r"request-[a-f0-9]{32}", request_id) else None,
                                        correlation,
                                        echoed if re.fullmatch(r"corr-[a-f0-9]{32}", echoed) else None)
            except (httpx.TimeoutException, httpx.NetworkError, httpx.RemoteProtocolError) as exc:
                kind = "timeout" if isinstance(exc, httpx.TimeoutException) else "connection"
                if attempt > self._config.max_retries:
                    raise EnterpriseAPIError(ErrorInfo(kind, "READ_TIMEOUT" if kind == "timeout" else "READ_CONNECTION_FAILED",
                                                       retryable=True, attempts=attempt, correlation_id=correlation)) from None
                retry = True
            except httpx.HTTPError:
                raise EnterpriseAPIError(ErrorInfo("connection", "READ_TRANSPORT_FAILED", attempts=attempt,
                                                   correlation_id=correlation)) from None
            if retry:
                time.sleep(self._config.retry_backoff * 2 ** (attempt - 1))
        raise AssertionError("Unreachable retry state")

    def close(self) -> None:
        if self._owns_client:
            self._http.close()
