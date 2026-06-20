"""batting_specialist — warehouse-backed career batting stats (baseball pack)."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

_bootstrap_path = Path(__file__).resolve().parent / "pack_bootstrap.py"
_bootstrap_spec = importlib.util.spec_from_file_location(
    "_baseball_pack_bootstrap",
    _bootstrap_path,
)
if _bootstrap_spec is None or _bootstrap_spec.loader is None:
    raise ImportError(f"Cannot load pack_bootstrap from {_bootstrap_path}")
_bootstrap_mod = importlib.util.module_from_spec(_bootstrap_spec)
_bootstrap_spec.loader.exec_module(_bootstrap_mod)
_bootstrap_mod.bootstrap(__file__)

from agents.specialists.agent import SpecialistAgent
from agents.specialists.fields import field_display_value, field_has_value, field_is_na
from models.state import MyceliumGraphState
from network.intent_map import (
    labels_for_intent_slug,
    load_intent_map,
    lookup_intent_slug,
)
from network.intent_normalization import resolve_intent_slug
from network.paths import NetworkPaths

from pack_common import run_warehouse_player_graph
from specialist_loader import load_derive_resolve, load_warehouse_resolve


def _legacy_derive_entry(
    record: dict[str, Any],
    requested_key: str,
    intent_slug: str,
    intent_map: dict[str, str],
):
    def _hit(key: str):
        entry = record.get(key)
        if field_has_value(entry) or field_is_na(entry):
            return entry
        return None

    for key in (requested_key, intent_slug):
        entry = _hit(key)
        if entry is not None:
            return entry
    alias_keys = labels_for_intent_slug(intent_slug, intent_map) - {
        requested_key,
        intent_slug,
    }
    for key in sorted(alias_keys):
        entry = _hit(key)
        if entry is not None:
            return entry
    return None


def _batting_derive_on_miss(key: str) -> bool:
    return True


def _batting_derive_on_miss_resolve(
    agent: SpecialistAgent,
    entity_id: str,
    key: str,
    *,
    record: dict[str, Any],
    player_id: str,
    warehouse: Any,
    manifest: dict[str, Any],
    paths: NetworkPaths,
    sources: list[dict[str, Any]],
    now: str,
) -> tuple[dict[str, Any], list[str], list[str], list[str]]:
    dr = load_derive_resolve()
    wr = load_warehouse_resolve()
    if not dr.derive_on_miss_enabled(manifest, "batting"):
        agent.write_na_field(entity_id, key, at=now)
        return {key: "N/A"}, [], [key], []

    requested_key = key
    intent_map = load_intent_map(paths)
    intent_slug = lookup_intent_slug(requested_key, intent_map)
    if intent_slug is None:
        intent_slug = resolve_intent_slug(
            requested_key,
            domain="batting",
            manifest=manifest,
            paths=paths,
            intent_map=intent_map,
        )

    values: dict[str, Any] = {}
    found_attrs: list[str] = []
    na_attrs: list[str] = []
    audit: list[str] = []

    if intent_slug != requested_key:
        audit.append(f"batting_specialist: intent {requested_key} -> {intent_slug}")

    slug_entry = record.get(intent_slug)
    if field_has_value(slug_entry):
        values[requested_key] = field_display_value(slug_entry)
        found_attrs.append(requested_key)
        return values, found_attrs, na_attrs, audit
    if field_is_na(slug_entry):
        values[requested_key] = "N/A"
        na_attrs.append(requested_key)
        return values, found_attrs, na_attrs, audit

    legacy_entry = _legacy_derive_entry(
        record,
        requested_key,
        intent_slug,
        intent_map,
    )
    if legacy_entry is not None:
        if field_has_value(legacy_entry):
            values[requested_key] = field_display_value(legacy_entry)
            found_attrs.append(requested_key)
        else:
            values[requested_key] = "N/A"
            na_attrs.append(requested_key)
        return values, found_attrs, na_attrs, audit

    derive_result = dr.generate_and_run_derive(
        requested_key,
        player_id=player_id,
        warehouse=warehouse,
        paths=paths,
        manifest=manifest,
    )
    audit.extend(derive_result.audit_log)
    derived = derive_result.field
    if derived is not None:
        computation: dict[str, str] = {
            "language": "python",
            "inline": derived.computation_inline,
        }
        if derived.model:
            computation["model"] = derived.model
        written = agent.write_computed_field(
            entity_id,
            intent_slug,
            value=derived.value,
            sources=sources,
            computation=computation,
            parameters=dr.provenance_parameters(
                player_id=player_id,
                paths=paths,
                warehouse=warehouse,
                attribute=requested_key,
                intent_slug=intent_slug,
            ),
            at=now,
        )
        values[requested_key] = written
        found_attrs.append(requested_key)
        return values, found_attrs, na_attrs, audit

    agent.write_na_field(entity_id, intent_slug, at=now)
    values[requested_key] = "N/A"
    na_attrs.append(requested_key)
    return values, found_attrs, na_attrs, audit


def _run_batting_specialist_graph(state: MyceliumGraphState | dict[str, Any]) -> dict[str, Any]:
    return run_warehouse_player_graph(
        state,
        agent=AGENT,
        category="batting",
        domain="batting",
        on_miss=_batting_derive_on_miss,
        on_miss_resolve=_batting_derive_on_miss_resolve,
    )


class BattingSpecialist(SpecialistAgent):
    category = "batting"
    agent_name = "batting_specialist"

    def run(self, state: MyceliumGraphState | dict[str, Any]) -> dict[str, Any]:
        return _run_batting_specialist_graph(state)


AGENT = BattingSpecialist()


def batting_specialist(state: MyceliumGraphState | dict[str, Any]) -> dict[str, Any]:
    return AGENT.run(state)