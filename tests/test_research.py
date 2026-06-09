"""Smoke tests for specialist research runner (mocked LLM/Tavily)."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

from agents.classification import get_category_tree, reset_category_tree
from agents.specialists.base import SpecialistStorage
from network.mvr import MvrPolicy
from tools.research import (
    FieldProposal,
    ResearchProposal,
    ResearchRunResult,
    _persist_proposal,
    _validate_and_build_record,
    bind_disambiguators,
    build_research_prompts,
    has_extra_bind_disambiguators,
    is_research_available,
    load_category_metadata,
    research_min_confidence,
    run_field_research,
)


@pytest.fixture
def categories_seed_tree(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Isolated categories cache from embedded _SEED_CATEGORIES."""
    monkeypatch.setenv("MYCELIUM_CATEGORIES_PATH", str(tmp_path / "categories.json"))
    reset_category_tree()
    get_category_tree()


@pytest.mark.smoke
def test_build_research_prompts_crm_mvr_employer_mandates_disambiguation() -> None:
    system, user = build_research_prompts(
        category="relationships",
        specialist_name="relationships_specialist",
        person_id="uuid-angela",
        target_fields=["spouse"],
        context={
            "entity_id": "uuid-angela",
            "bind": {"name": "Angela Murphy", "employer": "Talentcare"},
            "storage": {},
        },
    )
    assert user.startswith("DISAMBIGUATION (mandatory):")
    assert "employer: Talentcare" in user
    assert "FIRST web_search" in user
    assert "Bind disambiguation (mandatory)" in system
    assert "non-name bind disambiguators" in system


@pytest.mark.smoke
def test_build_research_prompts_name_only_bind_omits_disambiguation() -> None:
    system, user = build_research_prompts(
        category="relationships",
        specialist_name="relationships_specialist",
        person_id="uuid-jane",
        target_fields=["spouse"],
        context={
            "entity_id": "uuid-jane",
            "bind": {"name": "Jane"},
            "storage": {},
        },
    )
    assert "DISAMBIGUATION" not in user
    assert "Bind disambiguation (mandatory)" not in system
    assert "name-only searches are allowed" in system


@pytest.mark.smoke
def test_build_research_prompts_custom_mvr_account_id_disambiguation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    custom_mvr = MvrPolicy(
        bind_fields=["name", "account_id"],
        name_source="entity_key",
        description="Custom network",
    )
    monkeypatch.setattr("tools.research.load_mvr", lambda **kwargs: custom_mvr)
    system, user = build_research_prompts(
        category="contact",
        specialist_name="contact_specialist",
        person_id="uuid-acct",
        target_fields=["email"],
        context={
            "entity_id": "uuid-acct",
            "bind": {"name": "Jane", "account_id": "ACME-42"},
            "storage": {},
        },
    )
    assert "account_id: ACME-42" in user
    assert "employer:" not in user.split("Category guidance", 1)[0]
    assert "Bind disambiguation (mandatory)" in system
    assert "account_id" in system


@pytest.mark.smoke
def test_build_research_prompts_whitespace_bind_value_treated_as_absent() -> None:
    system, user = build_research_prompts(
        category="contact",
        specialist_name="contact_specialist",
        person_id="uuid-jane",
        target_fields=["email"],
        context={
            "entity_id": "uuid-jane",
            "bind": {"name": "Jane", "employer": "   "},
            "storage": {},
        },
    )
    assert "DISAMBIGUATION" not in user
    assert "Bind disambiguation (mandatory)" not in system
    disamb = bind_disambiguators(
        {"bind": {"name": "Jane", "employer": "   "}},
        MvrPolicy(bind_fields=["name", "employer"], name_source="entity_key", description=""),
    )
    assert has_extra_bind_disambiguators(disamb) is False


@pytest.mark.smoke
def test_build_research_prompts_flattened_peer_context_renders_header() -> None:
    """Production _research_context shape: specialists[cat] is field dict, not nested by entity_id."""
    _system, user = build_research_prompts(
        category="relationships",
        specialist_name="relationships_specialist",
        person_id="uuid-angela",
        target_fields=["spouse"],
        context={
            "entity_id": "uuid-angela",
            "bind": {"name": "Angela Murphy", "employer": "TalentCare"},
            "storage": {"spouse": {"status": "pending", "started_at": "2026-06-09T00:00:00+00:00"}},
            "specialists": {
                "contact": {
                    "email": {
                        "status": "found",
                        "value": "a@talentcare.us",
                        "sources": ["https://rocketreach.co/angela"],
                    },
                    "address": {
                        "status": "na",
                        "reason": "No public address",
                    },
                },
                "demographic": {
                    "city": {
                        "status": "found",
                        "value": "Austin, TX",
                        "sources": ["https://example.com/profile"],
                    },
                },
            },
        },
    )
    peer_section = user.split("Research the following person", 1)[0]
    assert peer_section.startswith("DISAMBIGUATION (mandatory):")
    assert "PEER SPECIALIST FINDINGS" in peer_section
    assert "contact:" in peer_section
    assert "a@talentcare.us" in peer_section
    assert "Austin, TX" in peer_section
    assert "address" not in peer_section
    assert peer_section.index("DISAMBIGUATION") < peer_section.index("PEER SPECIALIST FINDINGS")


@pytest.mark.smoke
def test_build_research_prompts_nested_peer_shape_still_works() -> None:
    _system, user = build_research_prompts(
        category="relationships",
        specialist_name="relationships_specialist",
        person_id="uuid-peer",
        target_fields=["spouse"],
        context={
            "entity_id": "uuid-peer",
            "bind": {"name": "Angela Murphy", "employer": "Talentcare"},
            "storage": {},
            "specialists": {
                "professional": {
                    "uuid-peer": {
                        "title": {"status": "found", "value": "VP Sales"},
                    },
                },
                "relationships": {
                    "uuid-peer": {"spouse": {"status": "pending"}},
                },
            },
        },
    )
    peer_section = user.split("Research the following person", 1)[0]
    assert "PEER SPECIALIST FINDINGS" in peer_section
    assert "professional:" in peer_section
    assert "VP Sales" in peer_section
    assert "tojson" not in peer_section.lower()


@pytest.mark.smoke
def test_build_research_prompts_omits_na_peer_fields_from_header() -> None:
    _system, user = build_research_prompts(
        category="relationships",
        specialist_name="relationships_specialist",
        person_id="uuid-peer",
        target_fields=["spouse"],
        context={
            "entity_id": "uuid-peer",
            "bind": {"name": "Jane"},
            "storage": {},
            "specialists": {
                "contact": {
                    "email": {"status": "found", "value": "jane@example.com", "sources": ["https://x.com"]},
                    "phone": {"status": "na", "reason": "not listed"},
                },
            },
        },
    )
    peer_section = user.split("Research the following person", 1)[0]
    assert "jane@example.com" in peer_section
    assert "phone" not in peer_section


@pytest.mark.smoke
def test_load_category_metadata_contact(categories_seed_tree: None) -> None:
    meta = load_category_metadata("contact")
    assert "email" in meta.get("examples", [])
    assert meta.get("assigned_agent") == "contact_specialist"


@pytest.mark.smoke
def test_load_category_metadata_financial(categories_seed_tree: None) -> None:
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
        context={"entity_id": pid, "bind": {"name": "Ada", "employer": "Lab"}, "specialists": {}},
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
            "entity_id": pid,
            "bind": {"name": "Ada", "employer": "Lab"},
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
    assert audit[-1]["context_bind"] == {"name": "Ada", "employer": "Lab"}


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
        context={"entity_id": pid, "bind": {"name": "Ada"}, "specialists": {}},
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
        context={"entity_id": pid, "bind": {"name": "Ada"}, "specialists": {}},
        storage=storage,
        llm=MagicMock(),
    )
    data = storage.load()["records"][pid]
    assert data["email"]["status"] == "pending"
    assert data["phone"]["status"] == "pending"
    assert data["email"].get("last_error")
    assert data["phone"].get("last_error")
