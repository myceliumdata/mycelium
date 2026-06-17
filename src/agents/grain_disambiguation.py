"""LLM disambiguation when multiple MVR grains return registry hits."""

from __future__ import annotations

import os
from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel

from agents.bind_alias_expansion import load_network_guide_text
from agents.entity_registry import RegistryEntity
from network.mvr import load_mvr, load_mvr_config

_DISAMBIGUATION_MODEL = os.getenv("MYCELIUM_GRAIN_DISAMBIGUATION_MODEL", "gpt-4o-mini")


@dataclass(frozen=True)
class GrainDisambiguationResult:
    """Outcome of multi-grain hit disambiguation (trigger A)."""

    kind: Literal["chosen", "chosen_grain", "ambiguous"]
    grain: str | None = None
    entity_id: str | None = None


GrainDisambiguator = Callable[
    [list[tuple[str, str, RegistryEntity]], str | None],
    GrainDisambiguationResult,
]


class _DisambiguationProposal(BaseModel):
    outcome: Literal["chosen", "chosen_grain", "ambiguous"]
    grain: str | None = None
    entity_id: str | None = None


def _build_disambiguation_prompt(
    hits: list[tuple[str, str, RegistryEntity]],
    guide_text: str | None,
) -> str:
    config = load_mvr_config()
    guide_block = guide_text.strip() if guide_text else "(no guide.md provided)"
    lines: list[str] = []
    for grain, entity_id, entity in hits:
        mvr = load_mvr(grain=grain)
        bind_parts = [
            f"{field}={entity.bind_value(field.strip().lower())!r}"
            for field in mvr.bind_fields
            if field.strip() and entity.bind_value(field.strip().lower())
        ]
        desc = config.grains[grain].description
        lines.append(
            f"- grain={grain!r} entity_id={entity_id!r} "
            f"description={desc!r} bind_values=({', '.join(bind_parts)})",
        )
    hit_block = "\n".join(lines)
    return (
        "Multiple entity grains matched the same lookup. Choose exactly one outcome:\n"
        "- chosen: pick one specific entity (set grain + entity_id)\n"
        "- chosen_grain: pick one grain and return all its hits on that grain\n"
        "- ambiguous: cannot disambiguate; user must pick (cross-grain ambiguous)\n\n"
        f"Network guide:\n{guide_block}\n\n"
        f"Candidates:\n{hit_block}\n"
    )


def _llm_disambiguate_grain_hits(
    hits: list[tuple[str, str, RegistryEntity]],
    guide_text: str | None,
) -> GrainDisambiguationResult:
    if not os.getenv("OPENAI_API_KEY", "").strip():
        return GrainDisambiguationResult(kind="ambiguous")

    prompt = _build_disambiguation_prompt(hits, guide_text)
    from langchain_openai import ChatOpenAI

    llm = ChatOpenAI(model=_DISAMBIGUATION_MODEL, temperature=0.0)
    structured = llm.with_structured_output(_DisambiguationProposal)
    result = structured.invoke(prompt)
    if not isinstance(result, _DisambiguationProposal):
        return GrainDisambiguationResult(kind="ambiguous")

    known = {(grain, entity_id) for grain, entity_id, _ in hits}
    grains_known = {grain for grain, _, _ in hits}

    if result.outcome == "chosen":
        if (
            result.grain in grains_known
            and result.entity_id
            and (result.grain, result.entity_id) in known
        ):
            return GrainDisambiguationResult(
                kind="chosen",
                grain=result.grain,
                entity_id=result.entity_id,
            )
        return GrainDisambiguationResult(kind="ambiguous")

    if result.outcome == "chosen_grain" and result.grain in grains_known:
        return GrainDisambiguationResult(kind="chosen_grain", grain=result.grain)

    return GrainDisambiguationResult(kind="ambiguous")


def disambiguate_grain_hits(
    hits: list[tuple[str, str, RegistryEntity]],
    *,
    guide_text: str | None = None,
    disambiguator: GrainDisambiguator | None = None,
) -> GrainDisambiguationResult:
    """Resolve multi-grain registry hits (trigger A — ≥2 grains with hits)."""
    if not hits:
        return GrainDisambiguationResult(kind="ambiguous")

    resolved_guide = guide_text if guide_text is not None else load_network_guide_text()
    if disambiguator is not None:
        return disambiguator(hits, resolved_guide)
    return _llm_disambiguate_grain_hits(hits, resolved_guide)
