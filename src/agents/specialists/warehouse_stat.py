"""Framework warehouse stat specialists — manifest-backed player/team reads."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from agents.registry_bridge import entity_source_key
from agents.responses import response_found, response_non_core, response_not_found
from agents.specialists.agent import SpecialistAgent
from agents.specialists.fields import field_display_value, field_has_value, field_is_na
from models.state import MyceliumGraphState, graph_requested_attributes
from network.dataset_source import load_pack_dataset_source
from network.intent_map import (
    labels_for_intent_slug,
    load_intent_map,
    lookup_intent_slug,
)
from network.intent_normalization import resolve_intent_slug
from network.paths import NetworkPaths, resolve_network_root
from network.warehouse_context import domain_meta


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def coerce_state(state: MyceliumGraphState | dict[str, Any]) -> MyceliumGraphState:
    if isinstance(state, MyceliumGraphState):
        return state
    return MyceliumGraphState.model_validate(state)


def resolve_entity_id(state: MyceliumGraphState) -> str | None:
    if state.current_id:
        return state.current_id
    ctx = state.context if isinstance(state.context, dict) else {}
    entity_id = ctx.get("entity_id")
    if entity_id:
        return str(entity_id)
    if state.matched_records and len(state.matched_records) == 1:
        return state.matched_records[0].get("id")
    return None


def resolve_owned_fields(state: MyceliumGraphState, category: str) -> list[str]:
    if state.target_fields:
        return list(state.target_fields)
    owned: list[str] = []
    for cl in state.classifications or []:
        if cl.get("category") == category and cl.get("attribute"):
            owned.append(cl["attribute"])
    if owned:
        return owned
    return [
        attr.strip().lower()
        for attr in graph_requested_attributes(state)
        if attr.strip()
    ]


def identity_from_context(
    ctx: dict[str, Any],
    entity_id: str | None,
) -> list[dict[str, Any]]:
    bind = ctx.get("bind")
    if entity_id and isinstance(bind, dict):
        bind_values = {
            str(key): str(value)
            for key, value in bind.items()
            if value is not None and str(value).strip()
        }
        return [{"id": entity_id, "bind_values": bind_values}]
    return []


def overall_field_status(
    *,
    found_attrs: list[str],
    na_attrs: list[str],
    pending: list[str],
) -> str:
    if pending:
        return "pending"
    if found_attrs and not na_attrs:
        return "found"
    if na_attrs and not found_attrs:
        return "na"
    if na_attrs:
        return "mixed"
    return "pending"


def query_year_id(state: MyceliumGraphState) -> str | None:
    """Return yearID from step-1 query scope or step-2 delivery-bound scope."""
    raw_scope: dict[str, Any]
    if state.delivery_scope_query_scope:
        raw_scope = state.delivery_scope_query_scope
    else:
        raw_scope = state.query.scope or {}
    raw = raw_scope.get("yearID")
    if raw is None:
        return None
    text = str(raw).strip()
    return text or None


def _legacy_derive_entry(
    record: dict[str, Any],
    requested_key: str,
    intent_slug: str,
    intent_map: dict[str, str],
) -> Any:
    def _hit(key: str) -> Any:
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


class WarehousePlayerStatSpecialist(SpecialistAgent):
    """Manifest-backed player warehouse reads with optional derive-on-miss."""

    domain: str = ""
    player_source_key: str = ""
    player_record_type: str = "player"

    def _load_warehouse_resolve(self) -> Any:
        raise NotImplementedError(
            f"{type(self).__name__} must implement _load_warehouse_resolve()",
        )

    def _load_derive_resolve(self) -> Any:
        raise NotImplementedError(
            f"{type(self).__name__} must implement _load_derive_resolve()",
        )

    def derive_on_miss_enabled(self, manifest: dict[str, Any]) -> bool:
        return bool(domain_meta(manifest, self.domain).get("derive_on_miss"))

    def defer_miss_to_research(self, key: str, manifest: dict[str, Any]) -> bool:
        """When true, leave field empty for WarehouseResearchStatSpecialist follow-on."""
        _ = key, manifest
        return False

    def resolve_derive_on_miss(
        self,
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
        dr = self._load_derive_resolve()
        if not self.derive_on_miss_enabled(manifest):
            self.write_na_field(entity_id, key, at=now)
            return {key: "N/A"}, [], [key], []

        requested_key = key
        intent_map = load_intent_map(paths)
        intent_slug = lookup_intent_slug(requested_key, intent_map)
        if intent_slug is None:
            intent_slug = resolve_intent_slug(
                requested_key,
                domain=self.domain,
                manifest=manifest,
                paths=paths,
                intent_map=intent_map,
            )

        values: dict[str, Any] = {}
        found_attrs: list[str] = []
        na_attrs: list[str] = []
        audit: list[str] = []

        if intent_slug != requested_key:
            audit.append(
                f"{self.agent_name}: intent {requested_key} -> {intent_slug}",
            )

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
            domain=self.domain,
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
            written = self.write_computed_field(
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

        self.write_na_field(entity_id, intent_slug, at=now)
        values[requested_key] = "N/A"
        na_attrs.append(requested_key)
        return values, found_attrs, na_attrs, audit

    def _evaluate_player_warehouse_fields(
        self,
        entity_id: str,
        owned: list[str],
        *,
        paths: NetworkPaths,
        year_id: str | None = None,
    ) -> tuple[dict[str, Any], str, list[str]]:
        wr = self._load_warehouse_resolve()
        data = self.storage.load()
        record = data.get("records", {}).get(entity_id, {})
        if not isinstance(record, dict):
            record = {}

        sources = load_pack_dataset_source(paths) or []
        warehouse = wr.default_warehouse_path(paths)
        manifest = wr.load_manifest(paths)
        player_id = entity_source_key(
            entity_id,
            self.player_source_key,
            record_type=self.player_record_type,
        )
        now = now_iso()
        values: dict[str, Any] = {}
        na_attrs: list[str] = []
        found_attrs: list[str] = []
        audit: list[str] = []

        for field in owned:
            key = field.strip().lower()
            entry = record.get(key)
            if field_has_value(entry):
                values[key] = field_display_value(entry)
                found_attrs.append(key)
                continue
            if field_is_na(entry):
                values[key] = "N/A"
                na_attrs.append(key)
                continue

            if not player_id or manifest is None:
                self.write_na_field(entity_id, key, at=now)
                values[key] = "N/A"
                na_attrs.append(key)
                continue

            try:
                resolved = wr.resolve_domain_attribute(
                    key,
                    domain=self.domain,
                    manifest=manifest,
                    player_id=player_id,
                    warehouse=warehouse,
                    year_id=year_id,
                )
            except FileNotFoundError:
                self.write_na_field(entity_id, key, at=now)
                values[key] = "N/A"
                na_attrs.append(key)
                continue

            if resolved is None and self.derive_on_miss_enabled(manifest):
                extra_values, extra_found, extra_na, extra_audit = (
                    self.resolve_derive_on_miss(
                        entity_id,
                        key,
                        record=record,
                        player_id=player_id,
                        warehouse=warehouse,
                        manifest=manifest,
                        paths=paths,
                        sources=sources,
                        now=now,
                    )
                )
                values.update(extra_values)
                found_attrs.extend(extra_found)
                na_attrs.extend(extra_na)
                audit.extend(extra_audit)
                continue

            if resolved is None:
                if self.defer_miss_to_research(key, manifest):
                    continue
                self.write_na_field(entity_id, key, at=now)
                values[key] = "N/A"
                na_attrs.append(key)
                continue

            written = self.write_computed_field(
                entity_id,
                key,
                value=resolved.value,
                sources=sources,
                computation={"language": "python", "inline": resolved.computation_inline},
            parameters=wr.provenance_parameters(
                player_id=player_id,
                paths=paths,
                warehouse=warehouse,
                attribute=resolved.attribute,
                column=resolved.column,
                year_id=year_id,
                scope_in_provenance=resolved.scope_in_provenance,
                compose_columns=resolved.compose_columns,
            ),
                at=now,
            )
            values[key] = written
            found_attrs.append(key)

        overall = overall_field_status(
            found_attrs=found_attrs,
            na_attrs=na_attrs,
            pending=[],
        )
        return values, overall, audit

    def run(self, state: MyceliumGraphState | dict[str, Any]) -> dict[str, Any]:
        current = coerce_state(state)
        ctx = current.context if isinstance(current.context, dict) else {}
        entity_id = resolve_entity_id(current)
        owned = resolve_owned_fields(current, self.category)
        thread_id, trace_id = current.invocation_thread_id, current.invocation_trace_id
        id_kwargs = {"thread_id": thread_id, "trace_id": trace_id}
        clf_kwargs = (
            {"classifications": current.classifications}
            if current.classifications
            else {}
        )
        identity_records = identity_from_context(ctx, entity_id)

        if not entity_id:
            resp = response_not_found(
                current.query,
                specialist=self.agent_name,
                **id_kwargs,
                **clf_kwargs,
            )
            return {
                "response": resp,
                "route": None,
                "audit_log": [f"{self.agent_name}: no id in state."],
                "specialist_contrib": {
                    "id": None,
                    "fields": owned,
                    "values": {},
                    "status": "not_found",
                },
                "matched_records": current.matched_records or [],
                "classifications": current.classifications or [],
            }

        paths = NetworkPaths.from_root(resolve_network_root())
        year_id = query_year_id(current)
        values, overall_status, derive_audit = self._evaluate_player_warehouse_fields(
            entity_id,
            owned,
            paths=paths,
            year_id=year_id,
        )
        contrib = {
            "id": entity_id,
            "category": self.category,
            "fields": owned,
            "values": values,
            "status": overall_status,
            "researched_fields": [],
        }

        if overall_status == "found":
            resp = response_found(
                current.query,
                base_records=identity_records or None,
                specialist=self.agent_name,
                **id_kwargs,
                **clf_kwargs,
            )
        else:
            resp = response_non_core(
                current.query,
                base_records=identity_records or None,
                attributes=owned,
                specialist=self.agent_name,
                **id_kwargs,
                **clf_kwargs,
            )

        return {
            "response": resp,
            "route": None,
            "audit_log": [
                f"{self.agent_name}: {overall_status} for id={entity_id!r} "
                f"(category={self.category}).",
                *derive_audit,
            ],
            "specialist_contrib": contrib,
            "matched_records": current.matched_records or [],
            "classifications": current.classifications or [],
            "context": ctx,
            "current_id": entity_id,
            "target_fields": owned,
        }


class WarehouseResearchStatSpecialist(WarehousePlayerStatSpecialist):
    """Warehouse player reads with optional Tavily research on unaliased misses."""

    def research_on_miss_enabled(self, manifest: dict[str, Any]) -> bool:
        return bool(domain_meta(manifest, self.domain).get("research_on_miss"))

    def defer_miss_to_research(self, key: str, manifest: dict[str, Any]) -> bool:
        if not self.research_on_miss_enabled(manifest):
            return False
        wr = self._load_warehouse_resolve()
        aliases = wr.domain_aliases(manifest, self.domain)
        return key not in aliases

    def _research_context(
        self,
        ctx: dict[str, Any],
        entity_id: str,
    ) -> dict[str, Any]:
        from agents.specialists.snapshots import normalize_context_fields

        data = self.storage.load()
        raw = data.get("records", {}).get(entity_id, {})
        out: dict[str, Any] = {
            "entity_id": entity_id,
            "bind": ctx.get("bind") if isinstance(ctx.get("bind"), dict) else {},
            "storage": (
                normalize_context_fields(raw, category=self.category)
                if isinstance(raw, dict)
                else {}
            ),
        }
        specialists_all = ctx.get("specialists")
        if isinstance(specialists_all, dict):
            peers: dict[str, Any] = {}
            for cat, records in specialists_all.items():
                if not isinstance(records, dict) or cat == self.category:
                    continue
                row = records.get(entity_id)
                if isinstance(row, dict) and row:
                    peers[cat] = row
            if peers:
                out["specialists"] = peers
        return out

    def _fields_needing_research(
        self,
        owned: list[str],
        values: dict[str, Any],
    ) -> list[str]:
        need: list[str] = []
        for field in owned:
            key = field.strip().lower()
            if key in values:
                continue
            need.append(key)
        return need

    def _mark_fields_pending(self, entity_id: str, fields: list[str]) -> None:
        from agents.specialists.research_handlers import mark_pending

        mark_pending(
            self.category,
            self.agent_name,
            entity_id,
            fields,
            last_error="",
        )

    def _run_research_on_miss(
        self,
        entity_id: str,
        need: list[str],
        ctx: dict[str, Any],
    ) -> tuple[list[str], list[str]]:
        from tools.research import ResearchRunResult, is_research_available, run_field_research

        audit: list[str] = []
        if not need:
            return audit, []
        if not is_research_available():
            self._mark_fields_pending(entity_id, need)
            audit.append(
                f"{self.agent_name}: research unavailable for id={entity_id!r} fields={need!r}",
            )
            return audit, []

        self._mark_fields_pending(entity_id, need)
        result: ResearchRunResult = run_field_research(
            category=self.category,
            specialist_name=self.agent_name,
            person_id=entity_id,
            target_fields=need,
            context=self._research_context(ctx, entity_id),
            storage=self.storage,
        )
        updated = list(result.fields_updated) if result else []
        audit.append(
            f"{self.agent_name}: research id={entity_id!r} fields={need!r} "
            f"updated={updated!r} tool_calls={result.tool_calls_count} "
            f"errors={len(result.errors)}",
        )
        return audit, updated

    def run(self, state: MyceliumGraphState | dict[str, Any]) -> dict[str, Any]:
        current = coerce_state(state)
        ctx = current.context if isinstance(current.context, dict) else {}
        entity_id = resolve_entity_id(current)
        owned = resolve_owned_fields(current, self.category)
        thread_id, trace_id = current.invocation_thread_id, current.invocation_trace_id
        id_kwargs = {"thread_id": thread_id, "trace_id": trace_id}
        clf_kwargs = (
            {"classifications": current.classifications}
            if current.classifications
            else {}
        )
        identity_records = identity_from_context(ctx, entity_id)

        if not entity_id:
            resp = response_not_found(
                current.query,
                specialist=self.agent_name,
                **id_kwargs,
                **clf_kwargs,
            )
            return {
                "response": resp,
                "route": None,
                "audit_log": [f"{self.agent_name}: no id in state."],
                "specialist_contrib": {
                    "id": None,
                    "fields": owned,
                    "values": {},
                    "status": "not_found",
                },
                "matched_records": current.matched_records or [],
                "classifications": current.classifications or [],
            }

        paths = NetworkPaths.from_root(resolve_network_root())
        year_id = query_year_id(current)
        values, overall_status, derive_audit = self._evaluate_player_warehouse_fields(
            entity_id,
            owned,
            paths=paths,
            year_id=year_id,
        )
        research_audit: list[str] = []
        researched_fields: list[str] = []
        manifest = self._load_warehouse_resolve().load_manifest(paths)
        if manifest and self.research_on_miss_enabled(manifest):
            need = self._fields_needing_research(owned, values)
            if need:
                extra_audit, researched_fields = self._run_research_on_miss(
                    entity_id,
                    need,
                    ctx,
                )
                research_audit.extend(extra_audit)
                data = self.storage.load()
                record = data.get("records", {}).get(entity_id, {})
                if not isinstance(record, dict):
                    record = {}
                for field in owned:
                    key = field.strip().lower()
                    if key in values:
                        continue
                    entry = record.get(key)
                    if field_has_value(entry):
                        values[key] = field_display_value(entry)
                    elif field_is_na(entry):
                        values[key] = "N/A"

                found_attrs = [k for k, v in values.items() if v != "N/A"]
                na_attrs = [k for k, v in values.items() if v == "N/A"]
                overall_status = overall_field_status(
                    found_attrs=found_attrs,
                    na_attrs=na_attrs,
                    pending=[],
                )

        contrib = {
            "id": entity_id,
            "category": self.category,
            "fields": owned,
            "values": values,
            "status": overall_status,
            "researched_fields": researched_fields,
        }

        if overall_status == "found":
            resp = response_found(
                current.query,
                base_records=identity_records or None,
                specialist=self.agent_name,
                **id_kwargs,
                **clf_kwargs,
            )
        else:
            resp = response_non_core(
                current.query,
                base_records=identity_records or None,
                attributes=owned,
                specialist=self.agent_name,
                **id_kwargs,
                **clf_kwargs,
            )

        return {
            "response": resp,
            "route": None,
            "audit_log": [
                f"{self.agent_name}: {overall_status} for id={entity_id!r} "
                f"(category={self.category}).",
                *derive_audit,
                *research_audit,
            ],
            "specialist_contrib": contrib,
            "matched_records": current.matched_records or [],
            "classifications": current.classifications or [],
            "context": ctx,
            "current_id": entity_id,
            "target_fields": owned,
        }


class WarehouseTeamStatSpecialist(SpecialistAgent):
    """Manifest-backed team warehouse reads (no derive-on-miss v1)."""

    domain: str = ""
    team_source_key: str = ""
    team_record_type: str = "team"

    def _load_warehouse_resolve(self) -> Any:
        raise NotImplementedError(
            f"{type(self).__name__} must implement _load_warehouse_resolve()",
        )

    def _evaluate_team_warehouse_fields(
        self,
        entity_id: str,
        owned: list[str],
        *,
        paths: NetworkPaths,
        year_id: str | None = None,
    ) -> tuple[dict[str, Any], str]:
        wr = self._load_warehouse_resolve()
        data = self.storage.load()
        record = data.get("records", {}).get(entity_id, {})
        if not isinstance(record, dict):
            record = {}

        sources = load_pack_dataset_source(paths) or []
        warehouse = wr.default_warehouse_path(paths)
        manifest = wr.load_manifest(paths)
        team_id = entity_source_key(
            entity_id,
            self.team_source_key,
            record_type=self.team_record_type,
        )
        now = now_iso()
        values: dict[str, Any] = {}
        na_attrs: list[str] = []
        found_attrs: list[str] = []

        for field in owned:
            key = field.strip().lower()
            entry = record.get(key)
            if field_has_value(entry):
                values[key] = field_display_value(entry)
                found_attrs.append(key)
                continue
            if field_is_na(entry):
                values[key] = "N/A"
                na_attrs.append(key)
                continue

            if not team_id or manifest is None:
                self.write_na_field(entity_id, key, at=now)
                values[key] = "N/A"
                na_attrs.append(key)
                continue

            try:
                resolved = wr.resolve_team_domain_attribute(
                    key,
                    domain=self.domain,
                    manifest=manifest,
                    team_id=team_id,
                    warehouse=warehouse,
                    year_id=year_id,
                )
            except FileNotFoundError:
                self.write_na_field(entity_id, key, at=now)
                values[key] = "N/A"
                na_attrs.append(key)
                continue

            if resolved is None:
                self.write_na_field(entity_id, key, at=now)
                values[key] = "N/A"
                na_attrs.append(key)
                continue

            written = self.write_computed_field(
                entity_id,
                key,
                value=resolved.value,
                sources=sources,
                computation={"language": "python", "inline": resolved.computation_inline},
                parameters=wr.team_provenance_parameters(
                    team_id=team_id,
                    paths=paths,
                    warehouse=warehouse,
                    attribute=resolved.attribute,
                    column=resolved.column,
                    year_id=year_id,
                    scope_in_provenance=resolved.scope_in_provenance,
                ),
                at=now,
            )
            values[key] = written
            found_attrs.append(key)

        overall = overall_field_status(
            found_attrs=found_attrs,
            na_attrs=na_attrs,
            pending=[],
        )
        return values, overall

    def run(self, state: MyceliumGraphState | dict[str, Any]) -> dict[str, Any]:
        current = coerce_state(state)
        ctx = current.context if isinstance(current.context, dict) else {}
        entity_id = resolve_entity_id(current)
        owned = resolve_owned_fields(current, self.category)
        thread_id, trace_id = current.invocation_thread_id, current.invocation_trace_id
        id_kwargs = {"thread_id": thread_id, "trace_id": trace_id}
        clf_kwargs = (
            {"classifications": current.classifications}
            if current.classifications
            else {}
        )
        identity_records = identity_from_context(ctx, entity_id)

        if not entity_id:
            resp = response_not_found(
                current.query,
                specialist=self.agent_name,
                **id_kwargs,
                **clf_kwargs,
            )
            return {
                "response": resp,
                "route": None,
                "audit_log": [f"{self.agent_name}: no id in state."],
                "specialist_contrib": {
                    "id": None,
                    "fields": owned,
                    "values": {},
                    "status": "not_found",
                },
                "matched_records": current.matched_records or [],
                "classifications": current.classifications or [],
            }

        paths = NetworkPaths.from_root(resolve_network_root())
        year_id = query_year_id(current)
        values, overall_status = self._evaluate_team_warehouse_fields(
            entity_id,
            owned,
            paths=paths,
            year_id=year_id,
        )
        contrib = {
            "id": entity_id,
            "category": self.category,
            "fields": owned,
            "values": values,
            "status": overall_status,
            "researched_fields": [],
        }

        if overall_status == "found":
            resp = response_found(
                current.query,
                base_records=identity_records or None,
                specialist=self.agent_name,
                **id_kwargs,
                **clf_kwargs,
            )
        else:
            resp = response_non_core(
                current.query,
                base_records=identity_records or None,
                attributes=owned,
                specialist=self.agent_name,
                **id_kwargs,
                **clf_kwargs,
            )

        return {
            "response": resp,
            "route": None,
            "audit_log": [
                f"{self.agent_name}: {overall_status} for id={entity_id!r} "
                f"(category={self.category}).",
            ],
            "specialist_contrib": contrib,
            "matched_records": current.matched_records or [],
            "classifications": current.classifications or [],
            "context": ctx,
            "current_id": entity_id,
            "target_fields": owned,
        }
