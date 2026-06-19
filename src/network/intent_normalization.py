"""LLM intent slug resolution for computation-on-miss cache deduplication."""

from __future__ import annotations

import os
import re
from typing import Any, Callable

from pydantic import BaseModel, Field

from network.intent_map import lookup_intent_slug, save_intent_mapping
from network.paths import NetworkPaths
from network.warehouse_context import format_warehouse_context
from utils.llm_models import intent_normalization_model

INTENT_SLUG_RE = re.compile(r"^[a-z0-9_]{1,64}$")
_CONFIDENCE_THRESHOLD = 0.7


class IntentProposal(BaseModel):
    intent_slug: str
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


def validate_intent_slug(slug: str) -> bool:
    return bool(INTENT_SLUG_RE.match(slug.strip().lower()))


def _normalize_label(label: str) -> str:
    return label.strip().lower()


def _build_intent_prompt(label: str, *, domain: str, manifest: dict[str, Any]) -> str:
    context = format_warehouse_context(manifest, domain)
    return (
        f"{context}\n\n"
        "Given the warehouse domain context above, infer a canonical intent slug for the "
        "requested attribute label.\n"
        f"Requested attribute label: {label}\n\n"
        "The intent slug identifies what stat or computation the label means (for cache dedup). "
        "Use snake_case only: lowercase letters, digits, underscores, max 64 characters.\n"
        "Examples: career_avg and batting_average might both map to career_batting_average.\n"
        "Return intent_slug and confidence (0.0-1.0)."
    )


def _build_intent_fix_prompt(label: str, *, domain: str, manifest: dict[str, Any], bad_slug: str) -> str:
    base = _build_intent_prompt(label, domain=domain, manifest=manifest)
    return (
        f"{base}\n\n"
        f"Previous intent_slug {bad_slug!r} was invalid. "
        "Use only [a-z0-9_]+, 1-64 characters."
    )


def _invoke_intent_llm(
    prompt: str,
    *,
    llm_invoke: Callable[[str], IntentProposal | dict[str, Any]] | None = None,
) -> IntentProposal:
    if llm_invoke is not None:
        result = llm_invoke(prompt)
        if isinstance(result, IntentProposal):
            return result
        return IntentProposal.model_validate(result)

    if not os.getenv("OPENAI_API_KEY", "").strip():
        raise RuntimeError("OPENAI_API_KEY not set for intent normalization")

    from langchain_openai import ChatOpenAI

    llm = ChatOpenAI(model=intent_normalization_model(), temperature=0.0)
    structured = llm.with_structured_output(IntentProposal)
    result = structured.invoke(prompt)
    if isinstance(result, IntentProposal):
        return result
    return IntentProposal.model_validate(result)


def resolve_intent_slug(
    label: str,
    *,
    domain: str,
    manifest: dict[str, Any],
    paths: NetworkPaths,
    intent_map: dict[str, str],
    llm_invoke: Callable[[str], IntentProposal | dict[str, Any]] | None = None,
) -> str:
    """Resolve canonical intent slug for a requested attribute label."""
    requested = _normalize_label(label)
    if not requested:
        return requested

    mapped = lookup_intent_slug(requested, intent_map)
    if mapped is not None and validate_intent_slug(mapped):
        return mapped

    prompt = _build_intent_prompt(requested, domain=domain, manifest=manifest)
    proposal: IntentProposal | None = None
    for attempt in range(2):
        try:
            current_prompt = prompt if attempt == 0 else _build_intent_fix_prompt(
                requested,
                domain=domain,
                manifest=manifest,
                bad_slug=proposal.intent_slug if proposal else "",
            )
            proposal = _invoke_intent_llm(current_prompt, llm_invoke=llm_invoke)
        except Exception:
            return requested

        slug = proposal.intent_slug.strip().lower()
        if validate_intent_slug(slug):
            if float(proposal.confidence) >= _CONFIDENCE_THRESHOLD:
                save_intent_mapping(paths, requested, slug)
                intent_map[requested] = slug
            return slug if float(proposal.confidence) >= _CONFIDENCE_THRESHOLD else requested

    return requested
