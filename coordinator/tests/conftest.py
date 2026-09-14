import pytest
from agents import set_tracing_disabled

@pytest.fixture(autouse=True)
def no_paid_traces():
    set_tracing_disabled(True)
    yield
