"""Pytest configuration and session-wide cleanup for Mycelium.

Ensures that global singletons (storage, core graph/checkpointer, identity)
are reset after the test session. This prevents aiosqlite worker threads
and other resources from keeping the pytest process alive after the last
test has completed and printed its output.
"""
from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from agents.entity_registry import reset_entity_registry
from agents.classification import reset_category_tree
from agents.context import reset_context_builder
from agents.factory.agent_factory import reset_agent_factory
from agents.registry import reset_agent_registry
from graphs.core import reset_core_graph
from storage.core import reset_storage

EXAMPLE_CRM = Path(__file__).resolve().parent.parent / "examples" / "networks" / "crm"
EXAMPLE_CRM_RUNTIME_ARTIFACTS = (
    "categories.json",
    "checkpoints.sqlite",
    "mycelium.db",
    "agent_registry.json",
)

_LEGACY_ENTITY_KEY_TEST_MODULES = frozenset({
    "test_agent_factory",
    "test_entity_boundary",
    "test_entity_growth",
    "test_entity_key_suggestions",
    "test_entity_metering",
    "test_entity_registry_bind",
    "test_entity_research_gate",
    "test_entity_unknown_mvr",
    "test_entity_validation",
    "test_network_integration",
    "test_query_messages",
    "test_query_provenance",
    "test_query_response_outcomes",
    "test_specialist_entity_vocab",
    "test_specialist_research_integration",
    "test_specialist_sync_research",
    "test_supervisor_routing",
})


def pytest_ignore_collect(collection_path: Path, config: pytest.Config) -> bool | None:
    """Do not collect legacy entity_key test modules (slice 1540 migration)."""
    if collection_path.suffix == ".py":
        stem = collection_path.stem
        if stem in _LEGACY_ENTITY_KEY_TEST_MODULES:
            return True
    return None


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """Defer legacy entity_key graph tests to slice 1540."""
    for item in items:
        module_name = item.module.__name__.rsplit(".", maxsplit=1)[-1]
        if module_name in _LEGACY_ENTITY_KEY_TEST_MODULES:
            item.add_marker(
                pytest.mark.skip(
                    reason="1540: migrate entity_key tests to id/lookup protocol",
                ),
            )


def clean_example_crm_runtime_artifacts() -> None:
    """Remove stray runtime files under the committed CRM example network."""
    for name in EXAMPLE_CRM_RUNTIME_ARTIFACTS:
        path = EXAMPLE_CRM / name
        if path.exists():
            path.unlink()
    agents_dir = EXAMPLE_CRM / "agents"
    if agents_dir.is_dir():
        shutil.rmtree(agents_dir)


@pytest.fixture(scope="session", autouse=True)
def _example_crm_runtime_hygiene() -> None:
    """Keep committed example/networks/crm free of runtime DB/cache files."""
    clean_example_crm_runtime_artifacts()
    yield
    clean_example_crm_runtime_artifacts()


@pytest.fixture(scope="session", autouse=True)
def _final_cleanup():
    """Run after all tests to guarantee clean shutdown of resources."""
    yield
    # Defensive cleanup (swallow errors) so that even if close fails for some
    # reason (closed loop, etc.), the pytest process can still exit promptly.
    for reset_func in (
        reset_core_graph,
        reset_storage,
        reset_entity_registry,
        reset_context_builder,
        reset_category_tree,
        reset_agent_registry,
        reset_agent_factory,
    ):
        try:
            reset_func()
        except Exception:
            pass
