"""Tests for LangSmith trace id capture in run_query."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from agents.context import reset_context_builder
from agents.factory.agent_factory import reset_agent_factory
from agents.registry import reset_agent_registry
from agents.entity_registry import reset_entity_registry
from graphs.core import (
    capture_langsmith_trace_id,
    get_last_invocation_trace_id,
    reset_core_graph,
    run_query,
)
from models.state import EntityQuery
from storage.core import reset_storage


def test_capture_returns_none_without_run_tree() -> None:
    with patch("langsmith.run_helpers.get_current_run_tree", return_value=None):
        assert capture_langsmith_trace_id() is None


def test_capture_returns_trace_id_from_run_tree() -> None:
    run_tree = MagicMock()
    run_tree.trace_id = "trace-123"
    with patch("langsmith.run_helpers.get_current_run_tree", return_value=run_tree):
        assert capture_langsmith_trace_id() == "trace-123"


@pytest.mark.full
def test_run_query_clears_trace_id_when_tracing_disabled(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    reset_storage()
    reset_entity_registry()
    reset_context_builder()
    reset_agent_registry()
    reset_agent_factory()
    reset_core_graph()
    seed = tmp_path / "seed.json"
    seed.write_text(
        json.dumps(
            {
                "rows": [
                    {"name": "Test User", "employer": "Test Co"},
                ],
            },
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("MYCELIUM_DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("MYCELIUM_SEED_PATH", str(seed))
    monkeypatch.setenv("MYCELIUM_CHECKPOINT_PATH", str(tmp_path / "cp.sqlite"))
    monkeypatch.delenv("LANGCHAIN_TRACING_V2", raising=False)
    monkeypatch.delenv("LANGSMITH_API_KEY", raising=False)
    monkeypatch.delenv("MYCELIUM_USE_SYNC_CHECKPOINTER", raising=False)

    from storage.core import get_storage

    get_storage()
    reset_entity_registry()
    response = run_query(
        EntityQuery(lookup={"name": "Test User", "employer": "Test Co"}),
        thread_id="trace-test-thread",
    )

    assert get_last_invocation_trace_id() is None
    assert response.thread_id == "trace-test-thread"
    assert response.trace_id is None


@pytest.mark.full
def test_run_query_sets_trace_id_on_response_when_captured(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    reset_storage()
    reset_entity_registry()
    reset_context_builder()
    reset_agent_registry()
    reset_agent_factory()
    reset_core_graph()
    seed = tmp_path / "seed.json"
    seed.write_text(
        json.dumps(
            {
                "rows": [
                    {"name": "Test User", "employer": "Test Co"},
                ],
            },
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("MYCELIUM_DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("MYCELIUM_SEED_PATH", str(seed))
    monkeypatch.setenv("MYCELIUM_CHECKPOINT_PATH", str(tmp_path / "cp.sqlite"))
    monkeypatch.setenv(
        "MYCELIUM_AGENT_REGISTRY_PATH",
        str(tmp_path / "agent_registry.json"),
    )
    monkeypatch.setenv("MYCELIUM_SPECIALISTS_DIR", str(tmp_path / "specialists"))
    monkeypatch.setenv("MYCELIUM_AGENT_DATA_DIR", str(tmp_path / "agent_data"))
    monkeypatch.setenv("LANGCHAIN_TRACING_V2", "true")
    monkeypatch.setenv("MYCELIUM_USE_SYNC_CHECKPOINTER", "1")

    from storage.core import get_storage

    get_storage()
    reset_entity_registry()

    def _set_trace_after_invoke(
        graph: object,
        initial: object,
        config: dict[str, Any],
        *,
        sync: bool,
    ) -> object:
        import graphs.core as gc

        if sync:
            result = graph.invoke(initial, config=config)  # type: ignore[union-attr]
        else:
            import asyncio

            async def _run() -> object:
                return await graph.ainvoke(initial, config=config)  # type: ignore[union-attr]

            result = asyncio.run(_run())
        gc._last_invocation_trace_id = "trace-abc"
        return result

    def _mock_async_invoke(
        graph: object,
        initial: object,
        config: dict[str, Any],
    ) -> object:
        return _set_trace_after_invoke(graph, initial, config, sync=True)

    def _mock_sync_invoke(
        graph: object,
        initial: object,
        config: dict[str, Any],
    ) -> object:
        return _set_trace_after_invoke(graph, initial, config, sync=True)

    with (
        patch("graphs.core._invoke_core_graph", _mock_async_invoke),
        patch("graphs.core._invoke_sync_graph", _mock_sync_invoke),
    ):
        response = run_query(
            EntityQuery(lookup={"name": "Test User", "employer": "Test Co"}),
            thread_id="traced-thread",
        )

    assert response.thread_id == "traced-thread"
    assert response.trace_id == "trace-abc"
    assert get_last_invocation_trace_id() == "trace-abc"
