"""Smoke tests for synchronous specialist research wiring (slice 1200)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest

from agents.factory.agent_factory import get_agent_factory, reset_agent_factory
from agents.registry import get_agent_registry, reset_agent_registry
from models.state import MyceliumGraphState, EntityQuery
from tools.research import ResearchRunResult


def _setup_contact_specialist(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[Any, Path]:
    reg_path = tmp_path / "reg.json"
    specialists_dir = tmp_path / "specialists"
    data_dir = tmp_path / "agent_data"
    monkeypatch.setenv("MYCELIUM_AGENT_REGISTRY_PATH", str(reg_path))
    monkeypatch.setenv("MYCELIUM_SPECIALISTS_DIR", str(specialists_dir))
    monkeypatch.setenv("MYCELIUM_AGENT_DATA_DIR", str(data_dir))
    reset_agent_registry()
    reset_agent_factory()
    factory = get_agent_factory()
    factory.create_specialist(
        "contact",
        "contact_specialist",
        "Direct contact info",
        examples=["email", "phone"],
        auto_commit=False,
    )
    registry = get_agent_registry()
    fn = registry.get_agent_fn("contact_specialist")
    storage_path = data_dir / "contact" / "storage.json"
    return fn, storage_path


@pytest.mark.smoke
def test_contact_email_sync_research_persists_found_not_pending(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Contact + email: mocked run_field_research writes found; contrib is not stuck pending."""
    fn, storage_path = _setup_contact_specialist(tmp_path, monkeypatch)
    test_id = "test-person-uuid-1200"

    def _fake_run_field_research(
        *,
        category: str,
        specialist_name: str,
        person_id: str,
        target_fields: list[str],
        context: dict[str, Any],
        storage: Any,
        llm: Any | None = None,
    ) -> ResearchRunResult:
        _ = category, specialist_name, context, llm
        assert person_id == test_id
        assert "email" in target_fields
        data = storage.load()
        rec = data.setdefault("records", {}).setdefault(person_id, {})
        now = datetime.now(timezone.utc).isoformat()
        rec["email"] = {
            "status": "found",
            "value": "jane@example.com",
            "confidence": 0.9,
            "sources": ["https://example.com/jane"],
            "researched_at": now,
        }
        storage.save(data)
        return ResearchRunResult(fields_updated=["email"], tool_calls_count=1)

    monkeypatch.setattr("tools.research.is_research_available", lambda: True)
    monkeypatch.setattr("tools.research.run_field_research", _fake_run_field_research)

    state = MyceliumGraphState(
        query=EntityQuery(entity_key="Jane Doe", requested_attributes=["email"]),
        current_id=test_id,
        context={
            "seed": {"id": test_id, "name": "Jane Doe", "employer": "Acme"},
            "specialists": {},
        },
        target_fields=["email"],
    )
    result = fn(state)

    contrib = result["specialist_contrib"]
    assert contrib["status"] == "found"
    assert contrib["values"]["email"] == "jane@example.com"
    assert "not currently available" not in result["response"].message

    stored = json.loads(storage_path.read_text(encoding="utf-8"))
    assert stored["records"][test_id]["email"]["status"] == "found"
    assert stored["records"][test_id]["email"]["value"] == "jane@example.com"


@pytest.mark.smoke
def test_contact_pre_marks_pending_before_research_runs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Empty cache miss: storage has pending + started_at before research completes."""
    fn, storage_path = _setup_contact_specialist(tmp_path, monkeypatch)
    test_id = "test-person-uuid-1400-premark"
    seen_pending_before_complete = False

    def _fake_run_field_research(
        *,
        category: str,
        specialist_name: str,
        person_id: str,
        target_fields: list[str],
        context: dict[str, Any],
        storage: Any,
        llm: Any | None = None,
    ) -> ResearchRunResult:
        nonlocal seen_pending_before_complete
        _ = category, specialist_name, context, llm
        data = storage.load()
        entry = data["records"][person_id]["email"]
        seen_pending_before_complete = (
            entry.get("status") == "pending" and bool(entry.get("started_at"))
        )
        now = datetime.now(timezone.utc).isoformat()
        data["records"][person_id]["email"] = {
            "status": "found",
            "value": "pre@example.com",
            "confidence": 0.9,
            "sources": ["https://example.com"],
            "researched_at": now,
        }
        storage.save(data)
        return ResearchRunResult(fields_updated=["email"], tool_calls_count=0)

    monkeypatch.setattr("tools.research.is_research_available", lambda: True)
    monkeypatch.setattr("tools.research.run_field_research", _fake_run_field_research)

    state = MyceliumGraphState(
        query=EntityQuery(entity_key="Jane", requested_attributes=["email"]),
        current_id=test_id,
        context={"seed": {"id": test_id, "name": "Jane", "employer": "Co"}},
        target_fields=["email"],
    )
    fn(state)
    assert seen_pending_before_complete
    stored = json.loads(storage_path.read_text(encoding="utf-8"))
    assert stored["records"][test_id]["email"]["status"] == "found"


@pytest.mark.smoke
def test_contact_retries_pending_with_last_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """pending + last_error is re-researched on the next specialist invoke."""
    fn, storage_path = _setup_contact_specialist(tmp_path, monkeypatch)
    test_id = "test-person-uuid-1400-retry"
    call_count = 0

    def _fake_run_field_research(
        *,
        category: str,
        specialist_name: str,
        person_id: str,
        target_fields: list[str],
        context: dict[str, Any],
        storage: Any,
        llm: Any | None = None,
    ) -> ResearchRunResult:
        nonlocal call_count
        _ = category, specialist_name, context, llm, person_id
        call_count += 1
        assert target_fields == ["email"]
        now = datetime.now(timezone.utc).isoformat()
        data = storage.load()
        data["records"][test_id]["email"] = {
            "status": "found",
            "value": "retry@example.com",
            "confidence": 0.9,
            "sources": ["https://example.com"],
            "researched_at": now,
        }
        storage.save(data)
        return ResearchRunResult(fields_updated=["email"])

    monkeypatch.setattr("tools.research.is_research_available", lambda: True)
    monkeypatch.setattr("tools.research.run_field_research", _fake_run_field_research)

    storage_path.write_text(
        json.dumps(
            {
                "records": {
                    test_id: {
                        "email": {
                            "status": "pending",
                            "started_at": "2020-01-01T00:00:00+00:00",
                            "last_error": "previous failure",
                        },
                    },
                },
            },
        ),
        encoding="utf-8",
    )

    state = MyceliumGraphState(
        query=EntityQuery(entity_key="Jane", requested_attributes=["email"]),
        current_id=test_id,
        context={"seed": {"id": test_id, "name": "Jane", "employer": "Co"}},
        target_fields=["email"],
    )
    result = fn(state)

    assert call_count == 1
    assert result["specialist_contrib"]["values"]["email"] == "retry@example.com"
    assert any("research id=" in line for line in result["audit_log"])


@pytest.mark.smoke
def test_contact_mixed_found_and_na_message(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """One found + one N/A: message names both; does not say all unavailable."""
    fn, storage_path = _setup_contact_specialist(tmp_path, monkeypatch)
    test_id = "test-person-uuid-1400-mixed"
    now = datetime.now(timezone.utc).isoformat()

    storage_path.write_text(
        json.dumps(
            {
                "records": {
                    test_id: {
                        "email": {
                            "status": "found",
                            "value": "mix@example.com",
                            "confidence": 0.9,
                            "sources": ["https://example.com"],
                            "researched_at": now,
                        },
                        "phone": {
                            "status": "na",
                            "reason": "No public phone listed",
                            "researched_at": now,
                        },
                    },
                },
            },
        ),
        encoding="utf-8",
    )

    research_called = False

    def _no_research(**kwargs: Any) -> ResearchRunResult:
        nonlocal research_called
        research_called = True
        _ = kwargs
        return ResearchRunResult()

    monkeypatch.setattr("tools.research.is_research_available", lambda: True)
    monkeypatch.setattr("tools.research.run_field_research", _no_research)

    state = MyceliumGraphState(
        query=EntityQuery(
            entity_key="Jane",
            requested_attributes=["email", "phone"],
        ),
        current_id=test_id,
        context={"seed": {"id": test_id, "name": "Jane", "employer": "Co"}},
        target_fields=["email", "phone"],
    )
    result = fn(state)

    assert not research_called
    contrib = result["specialist_contrib"]
    assert contrib["status"] == "mixed"
    assert contrib["values"]["email"] == "mix@example.com"
    assert contrib["values"]["phone"] == "N/A"
    msg = result["response"].message
    assert "Found record for Jane" in msg
    assert "mix@example.com" not in msg
    assert "not currently available" not in msg
    assert "(via contact_specialist)" not in msg


@pytest.mark.smoke
def test_regenerated_contact_specialist_has_no_threading(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Regenerated specialist modules must not use daemon-thread stubs."""
    _setup_contact_specialist(tmp_path, monkeypatch)
    py_path = tmp_path / "specialists" / "contact_specialist.py"
    text = py_path.read_text(encoding="utf-8")
    assert "threading" not in text
    assert "_stub_background_research" not in text
    assert "_run_field_research" in text
    assert "run_field_research" in text
