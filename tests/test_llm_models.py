"""Tests for central LLM model env resolution."""

from __future__ import annotations

import pytest

from utils.llm_models import (
    FALLBACK_MODEL,
    alias_expansion_model,
    classification_model,
    computation_codegen_model,
    llm_model,
    ontology_model,
    research_model,
)

_MODEL_ENV_KEYS = (
    "MYCELIUM_COMPUTATION_CODEGEN_MODEL",
    "MYCELIUM_CLASSIFICATION_MODEL",
    "MYCELIUM_ONTOLOGY_MODEL",
    "MYCELIUM_RESEARCH_MODEL",
    "MYCELIUM_ALIAS_EXPANSION_MODEL",
    "MYCELIUM_AGENT_FACTORY_REFINE_MODEL",
)


@pytest.fixture(autouse=True)
def _clear_model_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in _MODEL_ENV_KEYS:
        monkeypatch.delenv(key, raising=False)


def test_llm_model_unset_uses_fallback() -> None:
    assert llm_model("MYCELIUM_COMPUTATION_CODEGEN_MODEL") == FALLBACK_MODEL


def test_llm_model_empty_uses_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MYCELIUM_COMPUTATION_CODEGEN_MODEL", "   ")
    assert llm_model("MYCELIUM_COMPUTATION_CODEGEN_MODEL") == FALLBACK_MODEL


def test_llm_model_set_returns_value(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MYCELIUM_COMPUTATION_CODEGEN_MODEL", "gpt-4o")
    assert llm_model("MYCELIUM_COMPUTATION_CODEGEN_MODEL") == "gpt-4o"


@pytest.mark.parametrize(
    ("accessor", "env_key", "value"),
    [
        (computation_codegen_model, "MYCELIUM_COMPUTATION_CODEGEN_MODEL", "gpt-4o"),
        (classification_model, "MYCELIUM_CLASSIFICATION_MODEL", "gpt-4.1-mini"),
        (ontology_model, "MYCELIUM_ONTOLOGY_MODEL", "gpt-4.1"),
        (research_model, "MYCELIUM_RESEARCH_MODEL", "gpt-4o-mini"),
        (alias_expansion_model, "MYCELIUM_ALIAS_EXPANSION_MODEL", "gpt-4o-mini"),
    ],
)
def test_subsystem_accessors(
    monkeypatch: pytest.MonkeyPatch,
    accessor,
    env_key: str,
    value: str,
) -> None:
    assert accessor() == FALLBACK_MODEL
    monkeypatch.setenv(env_key, value)
    assert accessor() == value
