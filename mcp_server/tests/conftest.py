from pathlib import Path

import pytest

from mcp_server.testing import backend


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="session")
def live_backend(tmp_path_factory):
    storage = Path(tmp_path_factory.mktemp("backend"))
    with backend(storage) as (url, process):
        yield url
    assert process.returncode == 0
