"""Reusable model-free client connection using the official MCP SDK."""

from contextlib import asynccontextmanager

import httpx2
from mcp import Client
from mcp.client.streamable_http import streamable_http_client


@asynccontextmanager
async def connect(url, *, headers=None, mode="auto"):
    async with httpx2.AsyncClient(trust_env=False, follow_redirects=False, timeout=120, headers=headers) as http:
        async with Client(streamable_http_client(url, http_client=http), mode=mode,
                          read_timeout_seconds=120, cache=None) as client:
            yield client
