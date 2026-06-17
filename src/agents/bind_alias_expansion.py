"""Lazy field alias expansion for closed-world identity grains."""

from __future__ import annotations

import os
from collections.abc import Callable
from dataclasses import dataclass

from pydantic import BaseModel, Field

from agents.entity_registry import EntityRegistry
from network.mvr import load_mvr

_CANONICAL_VALUE_CAP = 500
_ALIAS_EXPANSION_MODEL = os.getenv("MYCELIUM_ALIAS_EXPANSION_MODEL", "gpt-4o-mini")


@dataclass(frozen=True)
class AliasExpansionResult:
    """Outcome of lazy alias expansion for one bind field value."""

    entity_ids: list[str]
    aliases_written: int


AliasExpander = Callable[
    [str, str, str, EntityRegistry, str | None],
    list[str],
]


class _FieldAliasProposal(BaseModel):
    entity_ids: list[str] = Field(default_factory=list)


def load_network_guide_text() -> str | None:
    """Read ``guide.md`` from the active network root when present."""
    from network.paths import _paths_for_runtime

    guide_path = _paths_for_runtime().root / "guide.md"
    if not guide_path.is_file():
        return None
    return guide_path.read_text(encoding="utf-8")


def _canonical_field_values(
    registry: EntityRegistry,
    field: str,
    *,
    cap: int = _CANONICAL_VALUE_CAP,
) -> list[tuple[str, str]]:
    field_key = field.strip().lower()
    rows: list[tuple[str, str]] = []
    for entity in registry.list_entities():
        raw = entity.bind_value(field_key)
        if raw is None or not str(raw).strip():
            continue
        rows.append((entity.id, str(raw).strip()))
        if len(rows) >= cap:
            break
    return rows


def _build_alias_expansion_prompt(
    *,
    grain: str,
    field: str,
    query_value: str,
    guide_text: str | None,
    canonical_rows: list[tuple[str, str]],
) -> str:
    mvr = load_mvr(grain=grain)
    canonical_lines = "\n".join(
        f"- id={entity_id!r} {field}={value!r}"
        for entity_id, value in canonical_rows
    )
    guide_block = guide_text.strip() if guide_text else "(no guide.md provided)"
    return (
        "You map nickname or shorthand bind-field values to existing registry entities.\n"
        "Return entity ids that should receive the query value as a field alias.\n"
        "Do not invent new entities. Shared ambiguous nicknames may map to multiple ids.\n\n"
        f"Grain: {grain}\n"
        f"Grain description: {mvr.description}\n"
        f"Bind field: {field}\n"
        f"Query value: {query_value!r}\n\n"
        f"Network guide:\n{guide_block}\n\n"
        f"Canonical registry values for field {field!r}:\n{canonical_lines}\n"
    )


def _llm_expand_field_aliases(
    grain: str,
    field: str,
    query_value: str,
    registry: EntityRegistry,
    guide_text: str | None,
) -> list[str]:
    if not os.getenv("OPENAI_API_KEY", "").strip():
        return []

    canonical_rows = _canonical_field_values(registry, field)
    if not canonical_rows:
        return []

    prompt = _build_alias_expansion_prompt(
        grain=grain,
        field=field,
        query_value=query_value,
        guide_text=guide_text,
        canonical_rows=canonical_rows,
    )

    from langchain_openai import ChatOpenAI

    llm = ChatOpenAI(model=_ALIAS_EXPANSION_MODEL, temperature=0.0)
    structured = llm.with_structured_output(_FieldAliasProposal)
    result = structured.invoke(prompt)
    if not isinstance(result, _FieldAliasProposal):
        return []

    known_ids = {entity_id for entity_id, _ in canonical_rows}
    return [
        entity_id
        for entity_id in result.entity_ids
        if entity_id in known_ids and registry.lookup_by_id(entity_id) is not None
    ]


def expand_field_aliases(
    grain: str,
    field: str,
    query_value: str,
    *,
    registry: EntityRegistry,
    guide_text: str | None = None,
    expander: AliasExpander | None = None,
) -> AliasExpansionResult:
    """Attach lazy field aliases for ``query_value`` on existing entities."""
    text = str(query_value).strip()
    field_key = field.strip().lower()
    if not field_key or not text:
        return AliasExpansionResult(entity_ids=[], aliases_written=0)

    resolved_guide = guide_text if guide_text is not None else load_network_guide_text()
    if expander is not None:
        target_ids = expander(grain, field_key, text, registry, resolved_guide)
    else:
        target_ids = _llm_expand_field_aliases(
            grain,
            field_key,
            text,
            registry,
            resolved_guide,
        )

    written = 0
    unique_ids: list[str] = []
    seen: set[str] = set()
    for entity_id in target_ids:
        if not entity_id or entity_id in seen:
            continue
        if registry.lookup_by_id(entity_id) is None:
            continue
        seen.add(entity_id)
        unique_ids.append(entity_id)
        registry.add_field_alias(entity_id, field_key, text)
        written += 1

    return AliasExpansionResult(entity_ids=unique_ids, aliases_written=written)
