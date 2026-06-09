"""Tests for supervisor routing and the thin supervisor agent node."""

from __future__ import annotations

import types
from pathlib import Path

import pytest

from agents.routing import evaluate_supervisor_turn
from agents.supervisor import supervisor_agent
from models.state import EntityQuery, MyceliumGraphState


def _seed_lookup(rows: list[dict]) -> callable:
    def lookup(entity_key: str) -> list[dict]:
        key = entity_key.strip().lower()
        return [r for r in rows if (r.get("name") or "").lower() == key]

    return lookup


@pytest.mark.smoke
def test_routing_delegates_lookup_to_seed() -> None:
    row = {"id": "p1", "name": "Ada", "employer": "Lab"}
    state = MyceliumGraphState(query=EntityQuery(entity_key="Ada"))

    decision = evaluate_supervisor_turn(state, seed_lookup=_seed_lookup([row]))

    assert len(decision.response.results) == 1
    assert decision.response.results[0]["name"] == "Ada"
    assert decision.response.outcome == "found"
    assert "Found record for" in decision.response.message
    assert "core record" not in decision.response.message.lower()


@pytest.mark.smoke
def test_routing_not_found_when_missing() -> None:
    state = MyceliumGraphState(query=EntityQuery(entity_key="Missing"))

    decision = evaluate_supervisor_turn(state, seed_lookup=_seed_lookup([]))

    assert decision.response.results == []
    assert decision.response.outcome == "not_found"
    assert "No record found" in decision.response.message
    assert "core record" not in decision.response.message.lower()
    assert "ingest" not in decision.response.message.lower()
    assert "provided_data" not in decision.response.message.lower()


@pytest.mark.smoke
def test_routing_non_core_attributes() -> None:
    row = {"id": "p1", "name": "Ada", "employer": "Lab"}
    state = MyceliumGraphState(
        query=EntityQuery(entity_key="Ada", requested_attributes=["age"]),
    )

    decision = evaluate_supervisor_turn(state, seed_lookup=_seed_lookup([row]))

    assert len(decision.response.results) == 1
    assert decision.response.outcome == "assembled"
    assert "Classified age as demographic" in decision.response.message
    assert "researching" in decision.response.message.lower()
    assert "age" in decision.response.message


@pytest.mark.smoke
def test_supervisor_agent_plans_no_specialists_without_attrs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Name-only query: supervisor resolves seed; graph assemble builds response."""
    import json

    from agents.seed import reset_seed_data

    seed = tmp_path / "seed.json"
    seed.write_text(
        json.dumps(
            {
                "people": [
                    {"id": "p1", "name": "any-key", "employer": "Co"},
                ],
            },
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("MYCELIUM_SEED_PATH", str(seed))
    reset_seed_data()

    state = MyceliumGraphState(query=EntityQuery(entity_key="any-key"))
    result = supervisor_agent(state)

    assert result.get("route") is None
    assert "response" not in result
    meta = result["context"]["_meta"]
    assert meta.get("specialists_to_invoke") == []
    assert any("resolved via seed" in entry for entry in result["audit_log"])


@pytest.mark.smoke
def test_supervisor_agent_classifies_requested_attributes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from agents.classification import reset_category_tree
    from agents.classification.engine import CategoryTree
    from agents.classification.models import CategoryProposal

    def _garbage_unknown_proposals(
        self: CategoryTree,
        attributes: list[str],
        llm: object | None = None,
        model: str = "gpt-4o-mini",
    ) -> list[CategoryProposal]:
        _ = llm, model
        return [
            CategoryProposal(
                attribute=a,
                category="unknown",
                description="Not classifiable",
                confidence=0.95,
            )
            for a in attributes
            if a.strip().lower() not in {"email", "phone"}
        ]

    monkeypatch.setattr(
        CategoryTree,
        "_llm_propose_for_attributes",
        _garbage_unknown_proposals,
    )
    reset_category_tree()
    from agents.registry import get_agent_registry, reset_agent_registry

    monkeypatch.setenv(
        "MYCELIUM_AGENT_REGISTRY_PATH",
        str(tmp_path / "reg_classify.json"),
    )
    reset_agent_registry()
    registry = get_agent_registry()
    registry.register_agent(
        {
            "name": "contact_specialist",
            "category": "contact",
            "description": "Contact specialist (pre-registered for routing test)",
            "module_path": "agents.specialists.contact_specialist",
            "entrypoint": "contact_specialist",
            "is_generated": False,
        },
        save=False,
    )

    state = MyceliumGraphState(
        query=EntityQuery(
            entity_key="any-key",
            requested_attributes=["email", "foo_unknown"],
        ),
    )

    result = supervisor_agent(state)

    assert "contact_specialist" in result["context"]["_meta"]["specialists_to_invoke"]
    assert len(result["classifications"]) == 2
    by_attr = {c["attribute"]: c for c in result["classifications"]}
    assert by_attr["email"]["category"] == "contact"
    assert by_attr["email"]["assigned_agent"] == "contact_specialist"
    assert by_attr["foo_unknown"]["category"] == "unknown"
    assert by_attr["foo_unknown"]["confidence"] == 0.0
    assert any("classified 'email'" in entry for entry in result["audit_log"])
    assert not any("classified 'foo_unknown'" in entry for entry in result["audit_log"])
    assert any("contact_specialist" in entry for entry in result["audit_log"])


@pytest.mark.smoke
def test_supervisor_triggers_creation_for_unregistered_specialist(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from agents.classification import reset_category_tree
    from agents.classification.engine import CategoryTree
    from agents.classification.models import CategoryProposal
    from agents.factory.agent_factory import AgentFactory, reset_agent_factory
    from agents.registry import get_agent_registry, reset_agent_registry

    def _no_llm_for_known(
        self: CategoryTree,
        attributes: list[str],
        llm: object | None = None,
        model: str = "gpt-4o-mini",
    ) -> list[CategoryProposal]:
        _ = self, llm, model
        return []

    monkeypatch.setattr(
        CategoryTree,
        "_llm_propose_for_attributes",
        _no_llm_for_known,
    )
    reset_category_tree()

    reg_path = tmp_path / "reg_trigger.json"
    monkeypatch.setenv("MYCELIUM_AGENT_REGISTRY_PATH", str(reg_path))
    reset_agent_registry()
    reset_agent_factory()

    create_calls: list[dict[str, str]] = []

    def _fake_create(
        self: AgentFactory,
        category: str,
        agent_name: str,
        description: str,
        examples: list[str] | None = None,
        *,
        llm_refine: bool = False,
        auto_commit: bool = True,
    ) -> dict[str, object]:
        _ = self, examples, llm_refine, auto_commit
        create_calls.append(
            {
                "category": category,
                "agent_name": agent_name,
                "description": description,
            },
        )
        get_agent_registry().register_agent(
            {
                "name": agent_name,
                "category": category,
                "description": description,
                "module_path": f"agents.specialists.{agent_name}",
                "entrypoint": agent_name,
                "is_generated": True,
            },
            save=False,
        )
        return {"created": True, "agent_name": agent_name}

    monkeypatch.setattr(AgentFactory, "create_specialist", _fake_create)

    state = MyceliumGraphState(
        query=EntityQuery(entity_key="any-key", requested_attributes=["email"]),
    )
    result = supervisor_agent(state)

    assert len(create_calls) == 1
    assert create_calls[0]["agent_name"] == "contact_specialist"
    assert create_calls[0]["category"] == "contact"
    assert "contact_specialist" in result["context"]["_meta"]["specialists_to_invoke"]
    assert any("created new specialist" in entry for entry in result["audit_log"])


@pytest.mark.smoke
def test_classification_engine_basic(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from agents.classification import CategoryTree, reset_category_tree
    from agents.classification.models import CategoryProposal

    def _garbage_unknown_proposals(
        self: CategoryTree,
        attributes: list[str],
        llm: object | None = None,
        model: str = "gpt-4o-mini",
    ) -> list[CategoryProposal]:
        _ = llm, model
        return [
            CategoryProposal(
                attribute=a,
                category="unknown",
                confidence=0.95,
            )
            for a in attributes
        ]

    monkeypatch.setattr(
        CategoryTree,
        "_llm_propose_for_attributes",
        _garbage_unknown_proposals,
    )
    reset_category_tree()
    tree = CategoryTree(cache_path=tmp_path / "categories.json")
    found = tree.classify("email")
    assert found.category == "contact"
    assert found.assigned_agent == "contact_specialist"
    assert found.confidence > 0.9
    unknown = tree.classify("foo_unknown")
    assert unknown.category == "unknown"
    assert unknown.confidence == 0.0
    assert tree.classify("foo_unknown").category == "unknown"


@pytest.mark.smoke
def test_refresh_from_llm_early_return_when_all_known(tmp_path: Path) -> None:
    from agents.classification import CategoryTree, reset_category_tree

    reset_category_tree()
    tree = CategoryTree(cache_path=tmp_path / "categories.json")

    result = tree.refresh_from_llm(["email", "phone"])

    assert result["reason"] == "all already known"
    assert result["updated_attributes"] == []


@pytest.mark.smoke
def test_refresh_from_llm_merge_with_mock_llm(tmp_path: Path) -> None:
    from agents.classification import CategoryTree, reset_category_tree
    from agents.classification.models import CategoryProposal, CategoryProposals

    reset_category_tree()
    tree = CategoryTree(cache_path=tmp_path / "categories.json")

    class _FakeStructured:
        def invoke(self, prompt: str) -> CategoryProposals:
            _ = prompt
            return CategoryProposals(
                proposals=[
                    CategoryProposal(
                        attribute="liquid_assets",
                        category="financial",
                        description="Financial attributes",
                        assigned_agent="financial_specialist",
                        confidence=0.9,
                    ),
                ]
            )

    class _FakeLLM:
        def with_structured_output(self, schema: type) -> _FakeStructured:
            _ = schema
            return _FakeStructured()

    changes = tree.refresh_from_llm(["liquid_assets"], llm=_FakeLLM())

    assert "liquid_assets" in changes["updated_attributes"]
    assert tree.classify("liquid_assets").category == "financial"


@pytest.mark.smoke
def test_classify_known_attr_does_not_call_llm(tmp_path: Path) -> None:
    from agents.classification import CategoryTree, reset_category_tree

    reset_category_tree()
    tree = CategoryTree(cache_path=tmp_path / "categories.json")
    called: list[str] = []

    def _should_not_run(
        self: CategoryTree,
        attributes: list[str],
        llm: object | None = None,
        model: str = "gpt-4o-mini",
    ) -> list:
        _ = self, llm, model
        called.extend(attributes)
        raise AssertionError("LLM must not run for known attributes")

    tree._llm_propose_for_attributes = types.MethodType(_should_not_run, tree)
    result = tree.classify("email")
    assert result.category == "contact"
    assert called == []


@pytest.mark.smoke
def test_classify_garbage_unknown_cached(tmp_path: Path) -> None:
    from agents.classification import CategoryTree, reset_category_tree
    from agents.classification.models import CategoryProposal

    reset_category_tree()
    tree = CategoryTree(cache_path=tmp_path / "categories.json")
    llm_calls = 0

    class _FakeStructured:
        def invoke(self, prompt: str) -> list[CategoryProposal]:
            _ = prompt
            return [
                CategoryProposal(
                    attribute="foo_bar_baz",
                    category="unknown",
                    confidence=0.9,
                ),
            ]

    class _FakeLLM:
        def with_structured_output(self, schema: type) -> _FakeStructured:
            _ = schema
            return _FakeStructured()

    def _counting_propose(
        self: CategoryTree,
        attributes: list[str],
        llm: object | None = None,
        model: str = "gpt-4o-mini",
    ) -> list[CategoryProposal]:
        nonlocal llm_calls
        _ = self, model
        llm_calls += 1
        fake = _FakeLLM()
        return fake.with_structured_output(list).invoke("")

    tree._llm_propose_for_attributes = types.MethodType(_counting_propose, tree)

    first = tree.classify("foo_bar_baz")
    second = tree.classify("foo_bar_baz")
    assert first.category == "unknown"
    assert second.category == "unknown"
    assert first.confidence == 0.0
    assert llm_calls == 1
    assert tree._data.attribute_map["foo_bar_baz"] == "unknown"


@pytest.mark.smoke
def test_classify_sensible_unknown_llm_then_cached(tmp_path: Path) -> None:
    from agents.classification import CategoryTree, reset_category_tree
    from agents.classification.models import CategoryProposal

    reset_category_tree()
    tree = CategoryTree(cache_path=tmp_path / "categories.json")
    llm_calls = 0

    class _FakeStructured:
        def invoke(self, prompt: str) -> list[CategoryProposal]:
            _ = prompt
            return [
                CategoryProposal(
                    attribute="liquid_assets",
                    category="financial",
                    description="Financial attributes",
                    assigned_agent="financial_specialist",
                    confidence=0.9,
                ),
            ]

    class _FakeLLM:
        def with_structured_output(self, schema: type) -> _FakeStructured:
            _ = schema
            return _FakeStructured()

    def _counting_propose(
        self: CategoryTree,
        attributes: list[str],
        llm: object | None = None,
        model: str = "gpt-4o-mini",
    ) -> list[CategoryProposal]:
        nonlocal llm_calls
        _ = self, model
        llm_calls += 1
        fake = _FakeLLM()
        return fake.with_structured_output(list).invoke("")

    tree._llm_propose_for_attributes = types.MethodType(_counting_propose, tree)

    first = tree.classify("liquid_assets")
    second = tree.classify("liquid_assets")
    assert first.category == "financial"
    assert second.category == "financial"
    assert first.confidence == 0.9
    assert second.confidence == 0.95
    assert llm_calls == 1


@pytest.mark.smoke
def test_agent_registry_empty_seed_when_missing_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from agents.registry import get_agent_registry, reset_agent_registry

    monkeypatch.setenv("MYCELIUM_AGENT_REGISTRY_PATH", str(tmp_path / "reg.json"))
    reset_agent_registry()
    registry = get_agent_registry()
    assert not registry.has_agent("core_data")
    assert registry.list_agents() == []


@pytest.mark.smoke
def test_agent_registry_register_persists_to_tmp(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from agents.registry import get_agent_registry, reset_agent_registry

    reg_path = tmp_path / "reg.json"
    monkeypatch.setenv("MYCELIUM_AGENT_REGISTRY_PATH", str(reg_path))
    reset_agent_registry()
    registry = get_agent_registry()
    registry.register_agent(
        {
            "name": "demo_specialist",
            "category": "demo",
            "description": "Demo specialist for registry test",
            "module_path": "agents.specialists.demographic_specialist",
            "entrypoint": "demographic_specialist",
            "is_generated": True,
            "created_at": "2026-06-07T00:00:00+00:00",
        },
    )
    reset_agent_registry()
    reloaded = get_agent_registry()
    assert reloaded.has_agent("demo_specialist")
    assert not reloaded.has_agent("core_data")
    assert len(reloaded.list_agents()) == 1
    assert reg_path.exists()


@pytest.mark.smoke
def test_specialist_storage_init_load_save_strategy(tmp_path: Path) -> None:
    from agents.specialists.base import SpecialistStorage

    storage = SpecialistStorage("demo", base_dir=tmp_path)
    data = storage.load()
    assert "records" in data
    storage.save({"records": {"p1": {"email": "a@b"}}})
    assert storage.load()["records"]["p1"]["email"] == "a@b"
    strategy = storage.get_strategy()
    assert strategy["strategy"] == "flat_json_v1"
    with pytest.raises(NotImplementedError):
        storage.migrate_to("minisql_v1")
