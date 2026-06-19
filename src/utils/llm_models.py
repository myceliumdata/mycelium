"""Central env-only LLM model selection for framework subsystems.

``computation_codegen_model`` selects the LLM that writes provenance ``computation``
code when no recipe exists for a requested attribute (codegen + semantic review).
"""

from __future__ import annotations

import os

FALLBACK_MODEL = "gpt-4o-mini"


def llm_model(env_key: str) -> str:
    """Read model from env_key; empty/unset → FALLBACK_MODEL."""
    raw = os.getenv(env_key, "").strip()
    return raw or FALLBACK_MODEL


def computation_codegen_model() -> str:
    return llm_model("MYCELIUM_COMPUTATION_CODEGEN_MODEL")


def classification_model() -> str:
    return llm_model("MYCELIUM_CLASSIFICATION_MODEL")


def ontology_model() -> str:
    return llm_model("MYCELIUM_ONTOLOGY_MODEL")


def research_model() -> str:
    return llm_model("MYCELIUM_RESEARCH_MODEL")


def alias_expansion_model() -> str:
    return llm_model("MYCELIUM_ALIAS_EXPANSION_MODEL")


def agent_factory_refine_model() -> str:
    return llm_model("MYCELIUM_AGENT_FACTORY_REFINE_MODEL")


def intent_normalization_model() -> str:
    return llm_model("MYCELIUM_INTENT_NORMALIZATION_MODEL")
