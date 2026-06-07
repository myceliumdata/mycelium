"""Smoke tests for skeleton ontology generation (Phase 5b; LLM mocked)."""

from __future__ import annotations

import pytest

from agents.classification.models import CategoryTreeData
from network.ontology import (
    OntologyGenerationError,
    ProposedCategory,
    ProposedOntology,
    generate_skeleton_ontology,
)

_CRM_SIX = frozenset(
    {
        "contact",
        "social",
        "relationships",
        "demographic",
        "professional",
        "financial",
    },
)


class _MockStructuredLLM:
    """Minimal stand-in for ChatOpenAI.with_structured_output().invoke()."""

    def __init__(self, responses: list[ProposedOntology]) -> None:
        self._responses = list(responses)
        self.calls = 0

    def with_structured_output(self, _schema: object) -> _MockStructuredLLM:
        return self

    def invoke(self, _messages: object) -> ProposedOntology:
        index = min(self.calls, len(self._responses) - 1)
        self.calls += 1
        return self._responses[index]


def _valid_wheat_ontology() -> ProposedOntology:
    return ProposedOntology(
        categories=[
            ProposedCategory(
                name="crop",
                description="Crop yields and planting data.",
                assigned_agent="crop_specialist",
                examples=["wheat_yield", "planting_date", "harvest_window"],
            ),
            ProposedCategory(
                name="soil",
                description="Soil chemistry and moisture.",
                assigned_agent="soil_specialist",
                examples=["ph_level", "moisture", "nitrogen"],
            ),
            ProposedCategory(
                name="equipment",
                description="Farm machinery and maintenance.",
                assigned_agent="equipment_specialist",
                examples=["tractor_id", "last_service", "fuel_level"],
            ),
        ],
    )


def _invalid_agent_ontology() -> ProposedOntology:
    return ProposedOntology(
        categories=[
            ProposedCategory(
                name="crop",
                description="Crop data.",
                assigned_agent="CropSpecialist",
                examples=["wheat_yield"],
            ),
            ProposedCategory(
                name="soil",
                description="Soil data.",
                assigned_agent="soil_specialist",
                examples=["ph_level"],
            ),
            ProposedCategory(
                name="weather",
                description="Weather data.",
                assigned_agent="weather_specialist",
                examples=["rainfall"],
            ),
        ],
    )


@pytest.mark.smoke
def test_generate_skeleton_ontology_happy_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    mock = _MockStructuredLLM([_valid_wheat_ontology()])

    result = generate_skeleton_ontology(
        "Track wheat fields, soil health, and farm equipment.",
        llm=mock,
    )

    assert isinstance(result.categories, CategoryTreeData)
    assert result.model_used == "gpt-4o-mini"
    assert len(result.categories.categories) == 3
    assert len(result.agents) == 3
    assert mock.calls == 1

    example_count = sum(
        len(cat.examples) for cat in result.categories.categories.values()
    )
    assert len(result.categories.attribute_map) == example_count
    assert result.categories.attribute_map["wheat_yield"] == "crop"
    assert result.agents[0].is_generated is True
    assert result.agents[0].module_path.startswith("agents.specialists.")


@pytest.mark.smoke
def test_invalid_agent_name_retries_then_raises(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    mock = _MockStructuredLLM([_invalid_agent_ontology(), _invalid_agent_ontology()])

    with pytest.raises(OntologyGenerationError, match="after retry"):
        generate_skeleton_ontology("Wheat network", llm=mock)

    assert mock.calls == 2


@pytest.mark.smoke
def test_empty_prompt_raises_before_llm(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    mock = _MockStructuredLLM([_valid_wheat_ontology()])

    with pytest.raises(ValueError, match="must not be empty"):
        generate_skeleton_ontology("   ", llm=mock)

    assert mock.calls == 0


@pytest.mark.smoke
def test_missing_api_key_raises_without_llm_call(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    with pytest.raises(OntologyGenerationError, match="OPENAI_API_KEY"):
        generate_skeleton_ontology("Wheat network")


@pytest.mark.smoke
def test_mock_llm_works_without_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    mock = _MockStructuredLLM([_valid_wheat_ontology()])

    result = generate_skeleton_ontology("Wheat network", llm=mock)

    assert len(result.agents) == 3
    assert mock.calls == 1


def _duplicate_slug_ontology() -> ProposedOntology:
    return ProposedOntology(
        categories=[
            ProposedCategory(
                name="crop",
                description="Crops",
                assigned_agent="crop_specialist",
                examples=["yield"],
            ),
            ProposedCategory(
                name="Crop",
                description="Duplicate slug",
                assigned_agent="crop_dup_specialist",
                examples=["area"],
            ),
            ProposedCategory(
                name="soil",
                description="Soil",
                assigned_agent="soil_specialist",
                examples=["ph"],
            ),
        ],
    )


def _nine_category_ontology() -> ProposedOntology:
    return ProposedOntology(
        categories=[
            ProposedCategory(
                name=f"cat_{index}",
                description=f"Category {index}",
                assigned_agent=f"cat_{index}_specialist",
                examples=[f"attr_{index}"],
            )
            for index in range(9)
        ],
    )


@pytest.mark.smoke
def test_duplicate_category_slug_retries_then_raises(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    mock = _MockStructuredLLM(
        [_duplicate_slug_ontology(), _duplicate_slug_ontology()],
    )

    with pytest.raises(OntologyGenerationError, match="after retry"):
        generate_skeleton_ontology("Wheat network", llm=mock)

    assert mock.calls == 2


@pytest.mark.smoke
def test_too_many_categories_validation_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    mock = _MockStructuredLLM([_nine_category_ontology(), _nine_category_ontology()])

    with pytest.raises(OntologyGenerationError, match="after retry"):
        generate_skeleton_ontology("Many categories", llm=mock)

    assert mock.calls == 2


@pytest.mark.smoke
def test_diverse_domain_not_hardcoded_crm_six(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    mock = _MockStructuredLLM([_valid_wheat_ontology()])

    result = generate_skeleton_ontology(
        "Monitor bacterial cultures in bioreactors: growth rate, medium pH, contamination flags.",
        llm=mock,
    )

    keys = set(result.categories.categories.keys())
    assert keys != _CRM_SIX
    assert not keys.issubset(_CRM_SIX)
