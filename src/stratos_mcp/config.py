"""Trusted process settings; none of these are MCP tool arguments."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from enterprise_api import ClientConfig


class ServerConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", hide_input_in_errors=True)
    enterprise: ClientConfig
    host: Literal["127.0.0.1", "localhost", "::1"] = "127.0.0.1"
    port: int = Field(default=9000, strict=True, ge=1, le=65535)

    @property
    def bind_host(self) -> str:
        # Do not depend on DNS resolution to keep the listener local.
        return "127.0.0.1" if self.host == "localhost" else self.host

    @property
    def origin(self) -> str:
        host = "[::1]" if self.bind_host == "::1" else self.bind_host
        return f"http://{host}:{self.port}"
