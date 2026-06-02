"""Pytest configuration and session-wide cleanup for Mycelium.

Ensures that global singletons (storage, core graph/checkpointer, identity)
are reset after the test session. This prevents aiosqlite worker threads
and other resources from keeping the pytest process alive after the last
test has completed and printed its output.
"""
import pytest

from agents.core_identity import reset_core_identity
from graphs.core import reset_core_graph
from storage.core import reset_storage


@pytest.fixture(scope="session", autouse=True)
def _final_cleanup():
    """Run after all tests to guarantee clean shutdown of resources."""
    yield
    # Defensive cleanup (swallow errors) so that even if close fails for some
    # reason (closed loop, etc.), the pytest process can still exit promptly.
    for reset_func in (reset_core_graph, reset_storage, reset_core_identity):
        try:
            reset_func()
        except Exception:
            pass
