"""Lazy field alias expansion for bootstrap-only record types."""

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


# Injectable expander returns canonical bind-field strings (not entity ids).
AliasExpander = Callable[
    [str, str, str, EntityRegistry, str | None],
    list[str],
]


class _FieldAliasProposal(BaseModel):
    canonical_values: list[str] = Field(
        default_factory=list,
        description=(
            "Exact canonical bind-field strings from the provided list that match "
            "the query nickname or shorthand. Empty when the query is not a real alias."
        ),
    )


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
) -> list[str]:
    field_key = field.strip().lower()
    values: list[str] = []
    seen: set[str] = set()
    for entity in registry.list_entities():
        raw = entity.bind_value(field_key)
        if raw is None or not str(raw).strip():
            continue
        value = str(raw).strip()
        if value in seen:
            continue
        seen.add(value)
        values.append(value)
        if len(values) >= cap:
            break
    return values


def _canonical_values_to_entity_ids(
    registry: EntityRegistry,
    field_key: str,
    canonical_values: list[str],
) -> list[str]:
    """Map canonical bind strings to registry entity ids (unknown values dropped)."""
    entity_ids: list[str] = []
    seen: set[str] = set()
    for raw in canonical_values:
        value = str(raw).strip()
        if not value:
            continue
        entity = registry.lookup_by_bind_values({field_key: value})
        if entity is None:
            continue
        if entity.id in seen:
            continue
        seen.add(entity.id)
        entity_ids.append(entity.id)
    return entity_ids


def _build_alias_expansion_prompt(
    *,
    record_type: str,
    field: str,
    query_value: str,
    guide_text: str | None,
    canonical_values: list[str],
) -> str:
    mvr = load_mvr(record_type=record_type)
    canonical_lines = "\n".join(
        f"- {field}={value!r}" for value in canonical_values
    )
    guide_block = guide_text.strip() if guide_text else "(no guide.md provided)"
    return (
        "You resolve whether a query is a real nickname, shorthand, or historical "
        "label for one or more rows in the canonical list below.\n"
        "Return exact canonical bind-field strings from the list (character-for-character "
        "match to a listed value). Do not invent entities or values. Do not return entity "
        "ids. Do not combine unrelated fragments from different rows. Mashups, "
        "typo-combos, and unrecognized strings → return an empty list.\n"
        "Use the network guide for domain-specific nickname patterns and negative "
        "examples.\n\n"
        f"Record type: {record_type}\n"
        f"Record type description: {mvr.description}\n"
        f"Bind field: {field}\n"
        f"Query value: {query_value!r}\n\n"
        f"Network guide:\n{guide_block}\n\n"
        f"Canonical registry values for field {field!r}:\n{canonical_lines}\n"
    )


def _llm_propose_canonical_values(
    record_type: str,
    field: str,
    query_value: str,
    registry: EntityRegistry,
    guide_text: str | None,
) -> list[str]:
    if not os.getenv("OPENAI_API_KEY", "").strip():
        return []

    canonical_values = _canonical_field_values(registry, field)
    if not canonical_values:
        return []

    prompt = _build_alias_expansion_prompt(
        record_type=record_type,
        field=field,
        query_value=query_value,
        guide_text=guide_text,
        canonical_values=canonical_values,
    )

    from langchain_openai import ChatOpenAI

    llm = ChatOpenAI(model=_ALIAS_EXPANSION_MODEL, temperature=0.0)
    structured = llm.with_structured_output(_FieldAliasProposal)
    result = structured.invoke(prompt)
    if not isinstance(result, _FieldAliasProposal):
        return []

    allowed = set(canonical_values)
    return [
        str(value).strip()
        for value in result.canonical_values
        if str(value).strip() in allowed
    ]


def expand_field_aliases(
    record_type: str,
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
        canonical_values = expander(record_type, field_key, text, registry, resolved_guide)
    else:
        canonical_values = _llm_propose_canonical_values(
            record_type,
            field_key,
            text,
            registry,
            resolved_guide,
        )

    target_ids = _canonical_values_to_entity_ids(registry, field_key, canonical_values)

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
