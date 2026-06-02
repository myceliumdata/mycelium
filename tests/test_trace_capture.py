"""Tests for LangSmith trace id capture in run_query."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from agents.core_identity import reset_core_identity
from graphs.core import (
    capture_langsmith_trace_id,
    get_last_invocation_trace_id,
    reset_core_graph,
    run_query,
)
from models.state import PersonQuery
from storage.core import reset_storage


def test_capture_returns_none_without_run_tree() -> None:
    with patch("langsmith.run_helpers.get_current_run_tree", return_value=None):
        assert capture_langsmith_trace_id() is None


def test_capture_returns_trace_id_from_run_tree() -> None:
    run_tree = MagicMock()
    run_tree.trace_id = "trace-123"
    with patch("langsmith.run_helpers.get_current_run_tree", return_value=run_tree):
        assert capture_langsmith_trace_id() == "trace-123"


def test_run_query_clears_trace_id_when_tracing_disabled(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    reset_storage()
    reset_core_identity()
    reset_core_graph()
    seed = tmp_path / "seed.json"
    seed.write_text(
        json.dumps(
            {
                "people": [
                    {"id": "person-test", "name": "Test User", "employer": "Test Co"},
                ],
            },
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("MYCELIUM_DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("MYCELIUM_SEED_PATH", str(seed))
    monkeypatch.setenv("MYCELIUM_CHECKPOINT_PATH", str(tmp_path / "cp.sqlite"))
    monkeypatch.delenv("LANGCHAIN_TRACING_V2", raising=False)

    from storage.core import get_storage

    get_storage()
    response = run_query(
        PersonQuery(person_key="person-test"),
        thread_id="trace-test-thread",
    )

    assert get_last_invocation_trace_id() is None
    assert response.thread_id == "trace-test-thread"
    assert response.trace_id is None
    reset_storage()
    reset_core_identity()
    reset_core_graph()


def test_run_query_sets_trace_id_on_response_when_captured(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    reset_storage()
    reset_core_identity()
    reset_core_graph()
    seed = tmp_path / "seed.json"
    seed.write_text(
        json.dumps(
            {
                "people": [
                    {"id": "person-test", "name": "Test User", "employer": "Test Co"},
                ],
            },
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("MYCELIUM_DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("MYCELIUM_SEED_PATH", str(seed))
    monkeypatch.setenv("MYCELIUM_CHECKPOINT_PATH", str(tmp_path / "cp.sqlite"))
    monkeypatch.setenv("LANGCHAIN_TRACING_V2", "true")

    from storage.core import get_storage

    get_storage()

    with (
        patch("graphs.core._langsmith_tracing_enabled", return_value=True),
        patch("graphs.core.capture_langsmith_trace_id", return_value="trace-abc"),
    ):
        response = run_query(
            PersonQuery(person_key="person-test"),
            thread_id="traced-thread",
        )

    assert response.thread_id == "traced-thread"
    assert response.trace_id == "trace-abc"
    reset_storage()
    reset_core_identity()
    reset_core_graph()
