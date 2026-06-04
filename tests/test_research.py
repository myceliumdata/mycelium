"""Smoke tests for specialist research runner (mocked LLM/Tavily)."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

from agents.specialists.base import SpecialistStorage
from tools.research import (
    FieldProposal,
    ResearchProposal,
    ResearchRunResult,
    _persist_proposal,
    _validate_and_build_record,
    is_research_available,
    load_category_metadata,
    research_min_confidence,
    run_field_research,
)


@pytest.mark.smoke
def test_load_category_metadata_contact() -> None:
    meta = load_category_metadata("contact")
    assert "email" in meta.get("examples", [])
    assert meta.get("assigned_agent") == "contact_specialist"


@pytest.mark.smoke
def test_load_category_metadata_financial() -> None:
    meta = load_category_metadata("financial")
    assert meta.get("description")
    assert "net_worth" in meta.get("examples", [])
    assert meta.get("assigned_agent") == "financial_specialist"


@pytest.mark.smoke
def test_low_confidence_persists_na_record() -> None:
    record, err = _validate_and_build_record(
        FieldProposal(
            field="email",
            value="a@b.com",
            status="found",
            confidence=0.3,
            sources=["https://example.com"],
        ),
        allowed={"email"},
        min_confidence=0.6,
    )
    assert err is None
    assert record is not None
    assert record["status"] == "na"
    assert "reason" in record


@pytest.mark.smoke
def test_good_proposal_persists_found() -> None:
    record, err = _validate_and_build_record(
        FieldProposal(
            field="email",
            value="user@example.com",
            status="found",
            confidence=0.9,
            sources=["https://example.com/profile"],
        ),
        allowed={"email"},
        min_confidence=research_min_confidence(),
    )
    assert err is None
    assert record is not None
    assert record["status"] == "found"
    assert record["value"] == "user@example.com"
    assert record["sources"]


@pytest.mark.smoke
def test_rejects_field_not_in_target_fields() -> None:
    record, err = _validate_and_build_record(
        FieldProposal(
            field="phone",
            value="555",
            status="found",
            confidence=0.9,
            sources=["https://example.com"],
        ),
        allowed={"email"},
        min_confidence=0.6,
    )
    assert record is None
    assert err and "target_fields" in err


@pytest.mark.smoke
def test_is_research_available_requires_both_keys(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv("TAVILY_API_KEY", "tvly-test")
    assert is_research_available()
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    assert not is_research_available()


@pytest.mark.smoke
def test_run_field_research_unavailable_marks_pending(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)
    storage = SpecialistStorage(category="contact", base_dir=tmp_path / "agents")
    pid = "uuid-contact-1"
    result = run_field_research(
        category="contact",
        specialist_name="contact_specialist",
        person_id=pid,
        target_fields=["email"],
        context={"seed": {"name": "Ada", "employer": "Lab"}},
        storage=storage,
    )
    assert result.errors
    assert "unavailable" in result.errors[0].lower()
    data = storage.load()
    assert data["records"][pid]["email"]["status"] == "pending"
    assert "last_error" in data["records"][pid]["email"]


@pytest.mark.smoke
def test_run_field_research_mock_llm_persists_found(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv("TAVILY_API_KEY", "tvly-test")

    proposal = ResearchProposal(
        fields=[
            FieldProposal(
                field="email",
                value="ada@lab.com",
                status="found",
                confidence=0.85,
                sources=["https://example.com/ada"],
            ),
        ],
        notes="ok",
    )

    class FakeLLM:
        def bind_tools(self, tools: list[Any]) -> "FakeLLM":
            _ = tools
            return self

        def invoke(self, messages: list[Any]) -> MagicMock:
            _ = messages
            msg = MagicMock()
            msg.tool_calls = [
                {
                    "name": "web_search",
                    "id": "call-1",
                    "args": {"query": "Ada Lab email"},
                },
            ]
            return msg

        def with_structured_output(self, schema: type) -> "FakeLLM":
            _ = schema
            return self

    monkeypatch.setattr(
        "tools.research._run_llm_loop",
        lambda **kwargs: (proposal, 1, []),
    )

    storage = SpecialistStorage(category="contact", base_dir=tmp_path / "agents")
    pid = "uuid-ada"
    result = run_field_research(
        category="contact",
        specialist_name="contact_specialist",
        person_id=pid,
        target_fields=["email"],
        context={
            "seed": {"id": pid, "name": "Ada", "employer": "Lab"},
            "specialists": {},
        },
        storage=storage,
        llm=FakeLLM(),
    )
    assert "email" in result.fields_updated
    assert result.tool_calls_count == 1
    data = storage.load()
    entry = data["records"][pid]["email"]
    assert entry["status"] == "found"
    assert entry["value"] == "ada@lab.com"
    audit = data.get("meta", {}).get("research_audit", [])
    assert audit and audit[-1]["tool_calls_count"] == 1


@pytest.mark.smoke
def test_persist_proposal_missing_field_marks_pending(
    tmp_path: Path,
) -> None:
    storage = SpecialistStorage(category="contact", base_dir=tmp_path / "agents")
    pid = "uuid-partial"
    proposal = ResearchProposal(
        fields=[
            FieldProposal(
                field="email",
                value="a@b.com",
                status="found",
                confidence=0.9,
                sources=["https://example.com"],
            ),
        ],
    )
    updated, errors = _persist_proposal(
        storage,
        pid,
        proposal,
        allowed={"email", "phone"},
        min_confidence=0.6,
    )
    assert "email" in updated
    assert errors
    data = storage.load()
    phone = data["records"][pid]["phone"]
    assert phone["status"] == "pending"
    assert phone.get("last_error")
    assert "phone" in phone["last_error"].lower() or "proposal" in phone["last_error"].lower()


@pytest.mark.smoke
def test_run_field_research_timeout_marks_pending(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv("TAVILY_API_KEY", "tvly-test")
    monkeypatch.setenv("MYCELIUM_RESEARCH_TIMEOUT_SEC", "1")

    def _slow_execute(**kwargs: Any) -> ResearchRunResult:
        import time

        _ = kwargs
        time.sleep(2)
        return ResearchRunResult()

    monkeypatch.setattr("tools.research._execute_research", _slow_execute)

    storage = SpecialistStorage(category="contact", base_dir=tmp_path / "agents")
    pid = "uuid-timeout"
    result = run_field_research(
        category="contact",
        specialist_name="contact_specialist",
        person_id=pid,
        target_fields=["email"],
        context={"seed": {"name": "Ada"}},
        storage=storage,
    )
    assert any("timed out" in e.lower() for e in result.errors)
    entry = storage.load()["records"][pid]["email"]
    assert entry["status"] == "pending"
    assert "timed out" in entry["last_error"].lower()


@pytest.mark.smoke
def test_run_field_research_null_proposal_marks_all_pending(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv("TAVILY_API_KEY", "tvly-test")
    monkeypatch.setattr(
        "tools.research._run_llm_loop",
        lambda **kwargs: (None, 0, ["structured output failed"]),
    )

    storage = SpecialistStorage(category="contact", base_dir=tmp_path / "agents")
    pid = "uuid-null-proposal"
    run_field_research(
        category="contact",
        specialist_name="contact_specialist",
        person_id=pid,
        target_fields=["email", "phone"],
        context={"seed": {"name": "Ada"}},
        storage=storage,
        llm=MagicMock(),
    )
    data = storage.load()["records"][pid]
    assert data["email"]["status"] == "pending"
    assert data["phone"]["status"] == "pending"
    assert data["email"].get("last_error")
    assert data["phone"].get("last_error")
