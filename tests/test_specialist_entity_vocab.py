"""Smoke tests: framework specialist modules use entity-neutral graph vocabulary."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from agents.factory.agent_factory import get_agent_factory, reset_agent_factory
from agents.registry import get_agent_registry, reset_agent_registry
from models.state import EntityQuery, MyceliumGraphState


_SPECIALIST_SPECS: list[tuple[str, str, str, list[str]]] = [
    ("contact", "contact_specialist", "email", ["email"]),
    ("demographic", "demographic_specialist", "age", ["age"]),
    ("professional", "professional_specialist", "title", ["title"]),
    ("social", "social_specialist", "linkedin", ["linkedin"]),
]


def _bootstrap_specialist(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    category: str,
    agent_name: str,
    description: str,
    examples: list[str],
) -> Any:
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
        category,
        agent_name,
        description,
        examples=examples,
        auto_commit=False,
    )
    registry = get_agent_registry()
    fn = registry.get_agent_fn(agent_name)
    assert fn is not None, f"{agent_name} not loadable from registry"
    return fn


def _minimal_state(*, requested: list[str]) -> MyceliumGraphState:
    seed = {"id": "test-uuid", "name": "Jane", "employer": "Acme"}
    return MyceliumGraphState(
        query=EntityQuery(entity_key="Jane", requested_attributes=requested),
        current_id="test-uuid",
        context={"entity_id": seed["id"], "bind": {"name": seed["name"], "employer": seed.get("employer")}, "specialists": {}},
        target_fields=requested,
        matched_records=[seed],
    )


@pytest.mark.smoke
@pytest.mark.parametrize(
    ("category", "agent_name", "field", "examples"),
    _SPECIALIST_SPECS,
)
def test_framework_specialist_uses_entity_vocab(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    category: str,
    agent_name: str,
    field: str,
    examples: list[str],
) -> None:
    monkeypatch.setattr(
        "tools.research.is_research_available",
        lambda: False,
    )
    fn = _bootstrap_specialist(
        tmp_path,
        monkeypatch,
        category=category,
        agent_name=agent_name,
        description=f"Test {category} specialist",
        examples=examples,
    )
    state = _minimal_state(requested=[field])

    result = fn(state)

    assert isinstance(result, dict)
    assert "matched_persons" not in result
    if "matched_records" in result:
        assert isinstance(result["matched_records"], list)


@pytest.mark.smoke
def test_framework_demographic_specialist_import_module_bind_context(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Registry file-load path: generated demographic_specialist uses bind, not seed."""
    monkeypatch.setattr("tools.research.is_research_available", lambda: False)
    fn = _bootstrap_specialist(
        tmp_path,
        monkeypatch,
        category="demographic",
        agent_name="demographic_specialist",
        description="Test demographic specialist",
        examples=["age"],
    )
    state = MyceliumGraphState(
        query=EntityQuery(entity_key="Jane", requested_attributes=["age"]),
        current_id="test-uuid",
        context={
            "entity_id": "test-uuid",
            "bind": {"name": "Jane", "employer": "Acme"},
            "specialists": {},
        },
        target_fields=["age"],
    )
    result = fn(state)
    assert result["specialist_contrib"]["id"] == "test-uuid"
    assert "Jane" in result["response"].message
    assert "seed" not in state.context


def _assert_specialist_source_uses_bind_not_seed(text: str) -> None:
    assert 'ctx.get("seed")' not in text
    assert 'context.get("seed")' not in text
    assert "entity_id" in text
    assert "_research_context" in text


@pytest.mark.smoke
def test_framework_specialist_template_uses_bind_not_seed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Factory template and rendered specialists use entity_id + bind, not seed."""
    template_path = (
        Path(__file__).resolve().parent.parent
        / "src"
        / "agents"
        / "factory"
        / "templates"
        / "specialist_agent.py.j2"
    )
    _assert_specialist_source_uses_bind_not_seed(
        template_path.read_text(encoding="utf-8"),
    )

    specialists_dir = tmp_path / "specialists"
    reg_path = tmp_path / "reg.json"
    monkeypatch.setenv("MYCELIUM_AGENT_REGISTRY_PATH", str(reg_path))
    monkeypatch.setenv("MYCELIUM_SPECIALISTS_DIR", str(specialists_dir))
    monkeypatch.setenv("MYCELIUM_AGENT_DATA_DIR", str(tmp_path / "agent_data"))
    reset_agent_registry()
    reset_agent_factory()
    factory = get_agent_factory()
    for category, agent_name, _field, examples in _SPECIALIST_SPECS:
        factory.create_specialist(
            category,
            agent_name,
            f"Test {category} specialist",
            examples=examples,
            auto_commit=False,
        )

    paths = sorted(specialists_dir.glob("*_specialist.py"))
    assert len(paths) == 4
    for path in paths:
        _assert_specialist_source_uses_bind_not_seed(path.read_text(encoding="utf-8"))


@pytest.mark.smoke
def test_crm_reference_contact_specialist_uses_entity_vocab() -> None:
    """Committed CRM example specialist is a reference copy aligned with the factory template."""
    from pathlib import Path

    ref_path = (
        Path(__file__).resolve().parent.parent
        / "examples"
        / "networks"
        / "crm"
        / "specialists"
        / "contact_specialist.py"
    )
    text = ref_path.read_text(encoding="utf-8")
    assert "entity_key" in text
    assert "entity_id" in text
    assert "bind" in text
    assert "person_key" not in text
    assert "matched_persons" not in text
    assert "not currently available but may be in the future" not in text
    assert "model_copy" not in text
