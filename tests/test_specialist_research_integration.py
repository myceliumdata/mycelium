"""Integration tests for Phase 1 sync specialist research via run_query (slice 1300/1400)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest

from agents.classification import reset_category_tree
from agents.context import reset_context_builder
from agents.entity_registry import reset_entity_registry
from graphs.core import reset_core_graph
from models.state import QueryResponse
from network_helpers import import_seed_for_test
from registry_helpers import resolve_and_deliver
from storage.core import CoreStorage, get_storage, reset_storage
from tools.research import ResearchRunResult
from versioned_storage_fixtures import versioned_found, versioned_na


def _assert_single_person_assembled(
    response: QueryResponse,
    *,
    person_name: str = "Test User",
    min_contributions: int = 1,
) -> dict[str, Any]:
    """Stable assertions for assembled non-core query outcomes (avoid brittle debug substrings)."""
    assert len(response.results) == 1
    row = response.results[0]
    assert row.get("id")
    assert response.message.startswith("Found record for ")
    assert (person_name in response.message) or ("d_" in response.message)
    assert "assembled" in response.debug
    assert f"contributions={min_contributions}" in response.debug
    return row


@pytest.fixture
def research_integration_env(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> CoreStorage:
    """Isolated DB/seed/registry for end-to-end run_query with contact research."""
    reset_storage()
    reset_entity_registry()
    reset_context_builder()
    reset_core_graph()
    reset_category_tree()

    from agents.factory.agent_factory import reset_agent_factory
    from agents.registry import reset_agent_registry

    db = tmp_path / "test.db"
    seed = tmp_path / "seed.json"
    seed.write_text(
        json.dumps(
            {
                "people": [
                    {"name": "Test User", "employer": "Test Co"},
                ],
            },
        ),
        encoding="utf-8",
    )
    categories_dst = tmp_path / "categories.json"
    monkeypatch.setenv("MYCELIUM_DB_PATH", str(db))
    monkeypatch.setenv("MYCELIUM_SEED_PATH", str(seed))
    monkeypatch.setenv("MYCELIUM_ENTITIES_PATH", str(tmp_path / "entities.json"))
    monkeypatch.setenv("MYCELIUM_CHECKPOINT_PATH", str(tmp_path / "cp.sqlite"))
    monkeypatch.setenv("MYCELIUM_CATEGORIES_PATH", str(categories_dst))
    reset_category_tree()
    from agents.classification import get_category_tree

    get_category_tree()
    monkeypatch.setenv(
        "MYCELIUM_AGENT_REGISTRY_PATH",
        str(tmp_path / "agent_registry.json"),
    )
    monkeypatch.setenv("MYCELIUM_SPECIALISTS_DIR", str(tmp_path / "specialists"))
    monkeypatch.setenv("MYCELIUM_AGENT_DATA_DIR", str(tmp_path / "agent_data"))
    monkeypatch.setenv("MYCELIUM_USE_SYNC_CHECKPOINTER", "1")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)

    reset_agent_registry()
    reset_agent_factory()
    storage = get_storage()
    import_seed_for_test(seed)

    yield storage

    reset_storage()
    reset_entity_registry()
    reset_context_builder()
    reset_core_graph()
    reset_category_tree()
    reset_agent_registry()
    reset_agent_factory()


@pytest.mark.smoke
def test_run_query_email_returns_found_in_same_response_when_research_mocked(
    research_integration_env: CoreStorage,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Single run_query with --attributes email: mocked research returns found in one response.

    Proves contact + email through supervisor → specialists → assemble (not pending forever).
    """
    _ = research_integration_env
    captured: dict[str, Any] = {}

    def _fake_run_field_research(
        *,
        category: str,
        specialist_name: str,
        person_id: str,
        target_fields: list[str],
        context: dict[str, Any],
        llm: Any | None = None,
    ) -> ResearchRunResult:
        _ = category, specialist_name, context, llm
        captured["person_id"] = person_id
        captured["target_fields"] = list(target_fields)
        assert "email" in target_fields
        from agents.specialists.base import SpecialistStorage

        storage = SpecialistStorage(category=category)
        data = storage.load()
        rec = data.setdefault("records", {}).setdefault(person_id, {})
        now = datetime.now(timezone.utc).isoformat()
        rec["email"] = versioned_found(
            at=now,
            value="test.user@example.com",
            confidence=0.92,
            sources=["https://example.com/contact"],
        )
        storage.save(data)
        return ResearchRunResult(fields_updated=["email"], tool_calls_count=1)

    monkeypatch.setattr("tools.research.is_research_available", lambda: True)
    monkeypatch.setattr("tools.research.run_field_research", _fake_run_field_research)

    _step1, response = resolve_and_deliver(
        lookup={"name": "Test User", "employer": "Test Co"},
        requested_attributes=["email"],
    )

    row = _assert_single_person_assembled(response)
    assert row["email"] == "test.user@example.com"
    assert "test.user@" not in response.message
    assert "not currently available" not in response.message
    assert "may be in the future" not in response.message
    assert "found=['email']" in response.debug
    assert captured.get("person_id") == row["id"]


@pytest.mark.smoke
def test_run_query_email_na_in_same_response_when_research_mocked(
    research_integration_env: CoreStorage,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Mocked research marks email N/A: same run_query exposes N/A in results, not as found.

    assemble_response merges specialist contrib; public results show email as N/A and the
    message does not claim the attribute was discovered.
    """
    _ = research_integration_env

    def _fake_run_field_research(
        *,
        category: str,
        specialist_name: str,
        person_id: str,
        target_fields: list[str],
        context: dict[str, Any],
        llm: Any | None = None,
    ) -> ResearchRunResult:
        _ = category, specialist_name, context, llm, target_fields
        now = datetime.now(timezone.utc).isoformat()
        from agents.specialists.base import SpecialistStorage

        storage = SpecialistStorage(category=category)
        data = storage.load()
        rec = data.setdefault("records", {}).setdefault(person_id, {})
        rec["email"] = versioned_na(
            at=now,
            reason="No public email found for this person",
        )
        storage.save(data)
        return ResearchRunResult(fields_updated=["email"], tool_calls_count=1)

    monkeypatch.setattr("tools.research.is_research_available", lambda: True)
    monkeypatch.setattr("tools.research.run_field_research", _fake_run_field_research)

    _step1, response = resolve_and_deliver(
        lookup={"name": "Test User", "employer": "Test Co"},
        requested_attributes=["email"],
    )

    row = _assert_single_person_assembled(response)
    assert row.get("email") == "N/A"
    assert "test.user@" not in response.message
    assert "not currently available" not in response.message
    assert "not found for this record" in response.message
    assert "unavailable=['email']" in response.debug


@pytest.mark.smoke
def test_run_query_email_pending_when_research_unavailable_no_crash(
    research_integration_env: CoreStorage,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Without API keys, research is skipped; email stays pending and query completes."""
    _ = research_integration_env
    monkeypatch.setattr("tools.research.is_research_available", lambda: False)

    _step1, response = resolve_and_deliver(
        lookup={"name": "Test User", "employer": "Test Co"},
        requested_attributes=["email"],
    )

    row = _assert_single_person_assembled(response)
    assert "email" not in row
    assert "Classified email as contact" in response.message
    assert (
        "researching" in response.message.lower()
        or "setting up a contact specialist" in response.message.lower()
    )
