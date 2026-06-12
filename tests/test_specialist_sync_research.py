"""Smoke tests for synchronous specialist research wiring (slice 1200)."""

from __future__ import annotations

import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest

from agents.factory.agent_factory import get_agent_factory, reset_agent_factory
from agents.registry import get_agent_registry, reset_agent_registry
from models.state import MyceliumGraphState, EntityQuery
from agents.specialist_fields import current_status, current_value, current_version
from tools.research import ResearchRunResult
from versioned_storage_fixtures import versioned_found, versioned_na, versioned_pending


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
        rec["email"] = versioned_found(
            at=now,
            value="jane@example.com",
            confidence=0.9,
            sources=["https://example.com/jane"],
        )
        storage.save(data)
        return ResearchRunResult(fields_updated=["email"], tool_calls_count=1)

    monkeypatch.setattr("tools.research.is_research_available", lambda: True)
    monkeypatch.setattr("tools.research.run_field_research", _fake_run_field_research)

    state = MyceliumGraphState(
        query=EntityQuery(entity_key="Jane Doe", requested_attributes=["email"]),
        current_id=test_id,
        context={
            "entity_id": test_id,
            "bind": {"name": "Jane Doe", "employer": "Acme"},
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
    email_entry = stored["records"][test_id]["email"]
    assert current_status(email_entry) == "found"
    assert current_value(email_entry) == "jane@example.com"


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
        version = current_version(entry)
        seen_pending_before_complete = (
            current_status(entry) == "pending"
            and bool((version or {}).get("started_at"))
        )
        now = datetime.now(timezone.utc).isoformat()
        data["records"][person_id]["email"] = versioned_found(
            at=now,
            value="pre@example.com",
            confidence=0.9,
            sources=["https://example.com"],
        )
        storage.save(data)
        return ResearchRunResult(fields_updated=["email"], tool_calls_count=0)

    monkeypatch.setattr("tools.research.is_research_available", lambda: True)
    monkeypatch.setattr("tools.research.run_field_research", _fake_run_field_research)

    state = MyceliumGraphState(
        query=EntityQuery(entity_key="Jane", requested_attributes=["email"]),
        current_id=test_id,
        context={"entity_id": test_id, "bind": {"name": "Jane", "employer": "Co"}, "specialists": {}},
        target_fields=["email"],
    )
    fn(state)
    assert seen_pending_before_complete
    stored = json.loads(storage_path.read_text(encoding="utf-8"))
    assert current_status(stored["records"][test_id]["email"]) == "found"


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
        data["records"][test_id]["email"] = versioned_found(
            at=now,
            value="retry@example.com",
            confidence=0.9,
            sources=["https://example.com"],
        )
        storage.save(data)
        return ResearchRunResult(fields_updated=["email"])

    monkeypatch.setattr("tools.research.is_research_available", lambda: True)
    monkeypatch.setattr("tools.research.run_field_research", _fake_run_field_research)

    storage_path.write_text(
        json.dumps(
            {
                "records": {
                    test_id: {
                        "email": versioned_pending(
                            started_at="2020-01-01T00:00:00+00:00",
                            last_error="previous failure",
                        ),
                    },
                },
            },
        ),
        encoding="utf-8",
    )

    state = MyceliumGraphState(
        query=EntityQuery(entity_key="Jane", requested_attributes=["email"]),
        current_id=test_id,
        context={"entity_id": test_id, "bind": {"name": "Jane", "employer": "Co"}, "specialists": {}},
        target_fields=["email"],
    )
    result = fn(state)

    assert call_count == 1
    assert result["specialist_contrib"]["values"]["email"] == "retry@example.com"
    assert any("research id=" in line for line in result["audit_log"])


@pytest.mark.smoke
def test_contact_retries_pending_without_last_error_when_no_age_gate(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """pending without last_error is re-researched when retry age gate is 0 (default)."""
    fn, storage_path = _setup_contact_specialist(tmp_path, monkeypatch)
    monkeypatch.delenv("MYCELIUM_RESEARCH_RETRY_PENDING_MIN_AGE_SEC", raising=False)
    monkeypatch.delenv("MYCELIUM_RESEARCH_RETRY_PENDING_SEC", raising=False)
    test_id = "test-person-uuid-pending-no-error"
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
        now = datetime.now(timezone.utc).isoformat()
        data = storage.load()
        data["records"][test_id]["email"] = versioned_found(
            at=now,
            value="retry@example.com",
            confidence=0.9,
            sources=["https://example.com"],
        )
        storage.save(data)
        return ResearchRunResult(fields_updated=["email"])

    monkeypatch.setattr("tools.research.is_research_available", lambda: True)
    monkeypatch.setattr("tools.research.run_field_research", _fake_run_field_research)

    storage_path.write_text(
        json.dumps(
            {
                "records": {
                    test_id: {
                        "email": versioned_pending(
                            started_at="2026-06-09T07:31:20.937912+00:00",
                        ),
                    },
                },
            },
        ),
        encoding="utf-8",
    )

    state = MyceliumGraphState(
        query=EntityQuery(entity_key="Jane", requested_attributes=["email"]),
        current_id=test_id,
        context={"entity_id": test_id, "bind": {"name": "Jane", "employer": "Co"}, "specialists": {}},
        target_fields=["email"],
    )
    result = fn(state)

    assert call_count == 1
    assert result["specialist_contrib"]["values"]["email"] == "retry@example.com"


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
                        "email": versioned_found(
                            at=now,
                            value="mix@example.com",
                            confidence=0.9,
                            sources=["https://example.com"],
                        ),
                        "phone": versioned_na(
                            at=now,
                            reason="No public phone listed",
                        ),
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
        context={"entity_id": test_id, "bind": {"name": "Jane", "employer": "Co"}, "specialists": {}},
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
def test_research_context_includes_peers_excludes_own_category(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _fn, _storage_path = _setup_contact_specialist(tmp_path, monkeypatch)
    py_path = tmp_path / "specialists" / "contact_specialist.py"
    spec = importlib.util.spec_from_file_location("dyn_contact_specialist", py_path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    storage = mod.get_specialist_storage()
    entity_id = "uuid-peer-context"
    ctx = {
        "bind": {"name": "Jane"},
        "specialists": {
            "contact": {
                entity_id: {
                    "email": versioned_found(
                        at="2026-06-09T00:00:00+00:00",
                        value="jane@example.com",
                    ),
                },
            },
            "professional": {
                entity_id: {
                    "title": versioned_found(
                        at="2026-06-09T00:00:00+00:00",
                        value="CEO",
                        category="professional",
                        specialist_name="professional_specialist",
                    ),
                },
            },
        },
    }
    out = mod._research_context(ctx, entity_id, storage)
    peers = out.get("specialists", {})
    assert "professional" in peers
    assert "contact" not in peers
    assert current_value(peers["professional"]["title"]) == "CEO"


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
