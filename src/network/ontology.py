"""Skeleton ontology generation from a network creation prompt (Phase 5b)."""

from __future__ import annotations

import os
import re
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field

from agents.classification.models import Category, CategoryTreeData
from agents.registry import RegisteredAgent
from agents.specialists.base import registry_storage_paths

_AGENT_NAME_RE = re.compile(r"^[a-z][a-z0-9_]*_specialist$")
_MIN_CATEGORIES = 3
_MAX_CATEGORIES = 8


class OntologyGenerationError(Exception):
    """Raised when skeleton ontology generation fails after retry."""


class ProposedCategory(BaseModel):
    """Structured LLM output for one coarse category."""

    name: str
    description: str
    assigned_agent: str
    examples: list[str] = Field(default_factory=list)


class ProposedOntology(BaseModel):
    """Structured LLM output for a full skeleton ontology."""

    categories: list[ProposedCategory]


class SkeletonOntologyResult(BaseModel):
    """Validated skeleton ontology ready for persistence by ``network create``."""

    categories: CategoryTreeData
    agents: list[RegisteredAgent]
    model_used: str


def _slugify_category_key(name: str) -> str:
    return name.strip().lower().replace(" ", "_").replace("-", "_")


def _system_prompt() -> str:
    return (
        "You design skeleton ontologies for Mycelium networks. "
        "A Mycelium network is a scoped specialist graph: each network manages "
        "a user-described domain (people, vehicles, organisms, artifacts, crops, "
        "clocks, bacteria, etc. — not CRM-only).\n\n"
        "Given a creation prompt describing what data the network manages, propose "
        f"{_MIN_CATEGORIES}–{_MAX_CATEGORIES} coarse categories. Each category must have:\n"
        "- name: short snake_case key (lowercase, underscores, no spaces)\n"
        "- description: one sentence\n"
        "- assigned_agent: exactly one specialist name matching "
        r"^[a-z][a-z0-9_]*_specialist$ (e.g. crop_specialist)\n"
        "- examples: 3–10 starter attribute names for that category only\n\n"
        "Do NOT invent exhaustive attribute lists. Examples seed a minimal "
        "attribute_map; query-time classification handles unknown attributes later. "
        "Use domain-appropriate categories — do not default to person/CRM taxonomy "
        "unless the prompt is clearly about people/CRM data."
    )


def _build_user_prompt(creation_prompt: str) -> str:
    return (
        "Design a skeleton ontology for a new Mycelium network.\n\n"
        f"Creation prompt:\n{creation_prompt}"
    )


def _validate_openai_api_key() -> None:
    if not os.getenv("OPENAI_API_KEY", "").strip():
        raise OntologyGenerationError(
            "OPENAI_API_KEY is not set. Add it to the framework .env before "
            "generating a network ontology.",
        )


def _convert_proposed(proposed: ProposedOntology, model: str) -> SkeletonOntologyResult:
    errors: list[str] = []
    count = len(proposed.categories)
    if count < _MIN_CATEGORIES:
        errors.append(
            f"expected {_MIN_CATEGORIES}–{_MAX_CATEGORIES} categories, got {count}",
        )
    if count > _MAX_CATEGORIES:
        errors.append(
            f"expected {_MIN_CATEGORIES}–{_MAX_CATEGORIES} categories, got {count}",
        )

    categories_dict: dict[str, Category] = {}
    attribute_map: dict[str, str] = {}
    agents: list[RegisteredAgent] = []
    agent_names_seen: set[str] = set()
    now = datetime.now(timezone.utc)
    now_iso = now.isoformat()

    for item in proposed.categories:
        key = _slugify_category_key(item.name)
        if not key:
            errors.append(f"empty category name after slugify: {item.name!r}")
            continue
        if key in categories_dict:
            errors.append(f"duplicate category key: {key}")
            continue
        if not _AGENT_NAME_RE.match(item.assigned_agent):
            errors.append(
                f"invalid assigned_agent {item.assigned_agent!r} for category {key}",
            )
            continue
        if item.assigned_agent in agent_names_seen:
            errors.append(f"duplicate assigned_agent: {item.assigned_agent}")
            continue

        description = item.description.strip()
        if not description:
            errors.append(f"empty description for category {key}")
            continue

        agent_names_seen.add(item.assigned_agent)
        examples = [ex.strip() for ex in item.examples if ex.strip()]
        categories_dict[key] = Category(
            description=description,
            assigned_agent=item.assigned_agent,
            examples=examples,
        )
        for example in examples:
            norm = example.lower()
            if norm and norm not in attribute_map:
                attribute_map[norm] = key

        storage_path, strategy_path = registry_storage_paths(key)
        agents.append(
            RegisteredAgent(
                name=item.assigned_agent,
                category=key,
                description=description,
                module_path=f"agents.specialists.{item.assigned_agent}",
                entrypoint=item.assigned_agent,
                storage_path=storage_path,
                strategy_path=strategy_path,
                is_generated=True,
                created_at=now_iso,
            ),
        )

    if errors:
        raise ValueError("; ".join(errors))

    if len(categories_dict) < _MIN_CATEGORIES:
        raise ValueError(
            f"expected at least {_MIN_CATEGORIES} valid categories after validation",
        )

    tree = CategoryTreeData(
        version="1.0",
        last_updated=now,
        model_used=model,
        categories=categories_dict,
        attribute_map=attribute_map,
    )
    return SkeletonOntologyResult(categories=tree, agents=agents, model_used=model)


def _invoke_llm(
    creation_prompt: str,
    model: str,
    llm: Any | None = None,
    *,
    prior_errors: str | None = None,
) -> ProposedOntology:
    from langchain_openai import ChatOpenAI

    client = llm if llm is not None else ChatOpenAI(model=model, temperature=0.0)
    user = _build_user_prompt(creation_prompt)
    if prior_errors:
        user += (
            f"\n\nPrevious attempt failed validation:\n{prior_errors}\n"
            "Please fix and try again."
        )

    structured_llm = client.with_structured_output(ProposedOntology)
    result = structured_llm.invoke(
        [
            ("system", _system_prompt()),
            ("human", user),
        ],
    )
    if isinstance(result, ProposedOntology):
        return result
    return ProposedOntology.model_validate(result)


def generate_skeleton_ontology(
    creation_prompt: str,
    *,
    model: str = "gpt-4o-mini",
    llm: Any | None = None,
) -> SkeletonOntologyResult:
    """LLM + validate + optional one retry. Raises OntologyGenerationError on failure."""
    prompt = creation_prompt.strip()
    if not prompt:
        raise ValueError("creation_prompt must not be empty")

    if llm is None:
        _validate_openai_api_key()

    last_error: str | None = None
    for attempt in range(2):
        try:
            proposed = _invoke_llm(prompt, model, llm, prior_errors=last_error)
            return _convert_proposed(proposed, model)
        except ValueError as exc:
            last_error = str(exc)
            if attempt == 1:
                raise OntologyGenerationError(
                    f"Ontology validation failed after retry: {last_error}",
                ) from exc
        except OntologyGenerationError:
            raise
        except Exception as exc:
            raise OntologyGenerationError(f"Ontology LLM call failed: {exc}") from exc

    raise OntologyGenerationError("Ontology generation failed")
