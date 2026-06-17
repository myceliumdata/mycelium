"""Read-only network snapshot for CLI status and future admin daemon."""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from agents.classification import get_category_tree
from agents.entity_registry import RegistryEntity, get_entity_registry
from network.metering_policy import load_metering_policy
from network.mvr import load_mvr, load_mvr_config
from network.paths import NetworkPaths, network_metadata, resolve_network_root


@dataclass(frozen=True)
class CategorySummary:
    name: str
    assigned_agent: str | None
    example_count: int
    examples: tuple[str, ...] = ()


@dataclass(frozen=True)
class SpecialistSummary:
    name: str
    category: str
    module_on_disk: bool
    storage_strategy: str | None
    record_count: int
    fields_tracked: list[str]
    pending_count: int = 0
    na_count: int = 0
    found_count: int = 0


@dataclass(frozen=True)
class EntityFieldStatus:
    field: str
    category: str
    agent: str
    status: str
    value: str | None = None
    field_kind: str = "extended"
    attr_source: str | None = None
    last_researched_at: str | None = None
    versions: tuple[dict[str, Any], ...] = ()


@dataclass(frozen=True)
class EntityMatchSummary:
    id: str
    name: str
    employer: str | None
    source: str
    validation_state: str | None = None
    research_allowed: bool = True


@dataclass(frozen=True)
class StatusResolve:
    """Active inspect target — exactly one of id or lookup is set."""

    id: str | None = None
    lookup: dict[str, str] | None = None


@dataclass(frozen=True)
class NetworkStatusSummary:
    network_name: str | None
    network_root: str
    display_name: str | None
    ontology_present: bool
    ontology_message: str
    categories: list[CategorySummary] = field(default_factory=list)
    specialists: list[SpecialistSummary] = field(default_factory=list)
    registry_entity_count: int = 0
    resolve: StatusResolve | None = None
    resolve_matches: int = 0
    resolve_kind: str | None = None
    resolve_required_fields: list[str] = field(default_factory=list)
    resolve_suggestions: list[dict[str, Any]] = field(default_factory=list)
    resolve_match_summaries: list[EntityMatchSummary] = field(default_factory=list)
    entity_fields: list[EntityFieldStatus] = field(default_factory=list)


def _paths() -> NetworkPaths:
    root = resolve_network_root()
    return NetworkPaths.from_root(root)


def _read_categories(paths: NetworkPaths) -> dict[str, Any] | None:
    if not paths.categories_path.is_file():
        return None
    try:
        data = json.loads(paths.categories_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def _read_registry_agents(paths: NetworkPaths) -> list[dict[str, Any]]:
    """List registered agents (read ``agent_registry.json`` only; no bootstrap write)."""
    if not paths.registry_path.is_file():
        return []
    try:
        raw = json.loads(paths.registry_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    agents = raw.get("agents")
    if not isinstance(agents, dict):
        return []
    return [value for value in agents.values() if isinstance(value, dict)]


def _specialists_dir() -> Path:
    return Path(os.getenv("MYCELIUM_SPECIALISTS_DIR", "src/agents/specialists"))


def _analyze_storage(paths: NetworkPaths, category: str) -> dict[str, Any]:
    _ = paths
    from agents.specialists.protocol import dispatch_analyze_category_storage

    return dispatch_analyze_category_storage(category)


def _agent_category_map(
    categories_doc: dict[str, Any] | None,
    registry_agents: list[dict[str, Any]],
) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for agent in registry_agents:
        name = agent.get("name")
        category = agent.get("category")
        if isinstance(name, str) and name.strip():
            mapping[name.strip()] = str(category) if category else ""
    if categories_doc:
        raw_categories = categories_doc.get("categories")
        if isinstance(raw_categories, dict):
            for category_name, meta in raw_categories.items():
                if not isinstance(meta, dict):
                    continue
                assigned = meta.get("assigned_agent")
                if isinstance(assigned, str) and assigned.strip():
                    mapping.setdefault(assigned.strip(), str(category_name))
    return mapping


def _category_summaries(
    categories_doc: dict[str, Any] | None,
    *,
    category_filter: str | None,
) -> list[CategorySummary]:
    if not categories_doc:
        return []
    raw_categories = categories_doc.get("categories")
    if not isinstance(raw_categories, dict):
        return []
    summaries: list[CategorySummary] = []
    for name, meta in sorted(raw_categories.items()):
        if category_filter and name != category_filter:
            continue
        if not isinstance(meta, dict):
            continue
        raw_examples = meta.get("examples")
        example_list = (
            [str(item) for item in raw_examples]
            if isinstance(raw_examples, list)
            else []
        )
        assigned = meta.get("assigned_agent")
        summaries.append(
            CategorySummary(
                name=str(name),
                assigned_agent=assigned if isinstance(assigned, str) else None,
                example_count=len(example_list),
                examples=tuple(example_list),
            ),
        )
    return summaries


def _specialist_summaries(
    paths: NetworkPaths,
    agent_map: dict[str, str],
    *,
    category_filter: str | None,
) -> list[SpecialistSummary]:
    specialists_dir = _specialists_dir()
    summaries: list[SpecialistSummary] = []
    for agent_name in sorted(agent_map):
        category = agent_map[agent_name]
        if category_filter and category != category_filter:
            continue
        storage = _analyze_storage(paths, category)
        summaries.append(
            SpecialistSummary(
                name=agent_name,
                category=category,
                module_on_disk=(specialists_dir / f"{agent_name}.py").is_file(),
                storage_strategy=storage.get("storage_strategy"),
                record_count=int(storage.get("record_count", 0)),
                fields_tracked=list(storage.get("fields_tracked", [])),
                pending_count=int(storage.get("pending_count", 0)),
                na_count=int(storage.get("na_count", 0)),
                found_count=int(storage.get("found_count", 0)),
            ),
        )
    return summaries


def _entity_field_statuses(
    paths: NetworkPaths,
    record_id: str,
    agent_map: dict[str, str],
    *,
    category_filter: str | None,
) -> list[EntityFieldStatus]:
    _ = paths
    from agents.specialists.protocol import dispatch_entity_field_statuses

    statuses: list[EntityFieldStatus] = []
    seen_categories: set[str] = set()
    for agent_name, category in sorted(agent_map.items(), key=lambda item: item[1]):
        if category_filter and category != category_filter:
            continue
        if category in seen_categories:
            continue
        seen_categories.add(category)
        for row in dispatch_entity_field_statuses(agent_name, category, record_id):
            statuses.append(
                EntityFieldStatus(
                    field=row["field"],
                    category=row["category"],
                    agent=row["agent"],
                    status=row["status"],
                    value=row.get("value"),
                    versions=tuple(row.get("versions") or ()),
                ),
            )
    return statuses


def _registry_entity_count() -> int:
    return get_entity_registry().entity_count()


def _registry_entity_for_match(record: dict[str, Any]) -> RegistryEntity | None:
    if not record.get("_registry"):
        return None
    entity_id = record.get("id")
    if not isinstance(entity_id, str) or not entity_id:
        return None
    return get_entity_registry().lookup_by_id(entity_id)


def _match_summaries(matches: list[dict[str, Any]]) -> list[EntityMatchSummary]:
    summaries: list[EntityMatchSummary] = []
    for match in matches:
        source = "registry" if match.get("_registry") else "seed"
        validation_state = match.get("_validation_state")
        if isinstance(validation_state, str):
            research_allowed = validation_state == "validated"
        else:
            research_allowed = source == "seed"
        summaries.append(
            EntityMatchSummary(
                id=str(match.get("id") or ""),
                name=str(match.get("name") or ""),
                employer=match.get("employer"),
                source=source,
                validation_state=(
                    validation_state if isinstance(validation_state, str) else None
                ),
                research_allowed=research_allowed,
            ),
        )
    return summaries


def _bind_field_versions(
    paths: NetworkPaths,
    record_id: str,
    field_name: str,
) -> tuple[dict[str, Any], ...]:
    _ = paths
    category = get_category_tree().mapped_category(field_name.strip().lower())
    if not category:
        return ()
    from agents.specialists.protocol import dispatch_read_fields

    categories = get_category_tree().get_categories()
    cat = categories.get(category)
    agent_name = cat.assigned_agent if cat is not None else None
    if not agent_name:
        from agents.registry import get_agent_registry

        for agent in get_agent_registry().list_agents():
            if agent.get("category") == category:
                raw = agent.get("name")
                agent_name = str(raw) if raw else None
                break
    if not agent_name:
        return ()
    read = dispatch_read_fields(
        agent_name,
        record_id,
        [field_name],
        include_versions=True,
    )
    entry = read.get(field_name.strip().lower())
    if isinstance(entry, dict):
        provenance = entry.get("provenance")
        if isinstance(provenance, dict):
            return tuple(provenance.get("versions") or [])
    return ()


def _bind_field_statuses(
    paths: NetworkPaths,
    match: dict[str, Any],
    registry_entity: RegistryEntity | None,
) -> list[EntityFieldStatus]:
    record_id = match.get("id")
    record_key = record_id if isinstance(record_id, str) and record_id else ""
    rows: list[EntityFieldStatus] = []
    for field_name in load_mvr().bind_fields:
        value = match.get(field_name)
        if field_name == "name" and not value:
            value = match.get("name") or ""
        status = "seed"
        if registry_entity is not None:
            status = registry_entity.field_states.get(field_name) or (
                registry_entity.validation_state
            )
        versions: tuple[dict[str, Any], ...] = ()
        if record_key:
            versions = _bind_field_versions(paths, record_key, field_name)
        rows.append(
            EntityFieldStatus(
                field=field_name,
                category="bind",
                agent="—",
                status=status,
                value=str(value) if value is not None else None,
                field_kind="bind",
                versions=versions,
            ),
        )
    return rows


def _entity_fields_for_match(
    paths: NetworkPaths,
    match: dict[str, Any],
    agent_map: dict[str, str],
    *,
    category_filter: str | None,
) -> list[EntityFieldStatus]:
    record_id = match.get("id")
    if not isinstance(record_id, str) or not record_id:
        return []
    registry_entity = _registry_entity_for_match(match)
    fields = _bind_field_statuses(paths, match, registry_entity)
    extended = _entity_field_statuses(
        paths,
        record_id,
        agent_map,
        category_filter=category_filter,
    )
    if registry_entity is not None:
        enriched: list[EntityFieldStatus] = []
        for item in extended:
            enriched.append(
                EntityFieldStatus(
                    field=item.field,
                    category=item.category,
                    agent=item.agent,
                    status=item.status,
                    value=item.value,
                    field_kind="extended",
                    attr_source=registry_entity.attr_sources.get(item.field),
                    last_researched_at=registry_entity.last_researched_at.get(
                        item.field,
                    ),
                    versions=item.versions,
                ),
            )
        fields.extend(enriched)
    else:
        fields.extend(extended)
    return fields


def build_network_status(
    *,
    category_filter: str | None = None,
    resolve_id: str | None = None,
    resolve_lookup: dict[str, str] | None = None,
) -> NetworkStatusSummary:
    """Build a read-only snapshot of the active network."""
    paths = _paths()
    meta = network_metadata(root=paths.root)
    categories_doc = _read_categories(paths)
    ontology_present = categories_doc is not None
    ontology_message = (
        "present"
        if ontology_present
        else "not created yet — run a query to bootstrap categories.json"
    )

    registry_agents = _read_registry_agents(paths)
    agent_map = _agent_category_map(categories_doc, registry_agents)

    entity_fields: list[EntityFieldStatus] = []
    resolve_matches = 0
    resolve_kind: str | None = None
    resolve_required_fields: list[str] = []
    resolve_suggestions: list[dict[str, Any]] = []
    resolve_match_summaries: list[EntityMatchSummary] = []
    status_resolve: StatusResolve | None = None

    if resolve_id and resolve_lookup:
        raise ValueError("Use resolve_id or resolve_lookup for drill-down, not both")

    if resolve_id:
        from agents.entity_registry import get_entity_registry, registry_entity_to_match

        status_resolve = StatusResolve(id=resolve_id.strip(), lookup=None)
        registry = get_entity_registry()
        entity = registry.lookup_by_id(resolve_id.strip())
        if entity is not None:
            matches = [registry_entity_to_match(entity)]
            resolve_kind = "exact"
            resolve_matches = 1
            resolve_match_summaries = _match_summaries(matches)
            entity_fields = _entity_fields_for_match(
                paths,
                matches[0],
                agent_map,
                category_filter=category_filter,
            )
        else:
            resolve_kind = "none"
    elif resolve_lookup:
        from agents.entity_resolution import resolve_status_for_target_lookup

        status_resolve = StatusResolve(id=None, lookup=dict(resolve_lookup))
        resolution = resolve_status_for_target_lookup(resolve_lookup)
        resolve_kind = resolution.kind
        resolve_required_fields = list(resolution.required_fields)
        resolve_suggestions = [
            item.model_dump() for item in resolution.suggestions
        ]
        matches = resolution.matches
        resolve_matches = len(matches)
        resolve_match_summaries = _match_summaries(matches)
        if len(matches) == 1:
            entity_fields = _entity_fields_for_match(
                paths,
                matches[0],
                agent_map,
                category_filter=category_filter,
            )

    return NetworkStatusSummary(
        network_name=meta.get("network_name"),
        network_root=str(paths.root),
        display_name=meta.get("network_display_name"),
        ontology_present=ontology_present,
        ontology_message=ontology_message,
        categories=_category_summaries(categories_doc, category_filter=category_filter),
        specialists=_specialist_summaries(
            paths,
            agent_map,
            category_filter=category_filter,
        ),
        registry_entity_count=_registry_entity_count(),
        resolve=status_resolve,
        resolve_matches=resolve_matches,
        resolve_kind=resolve_kind,
        resolve_required_fields=resolve_required_fields,
        resolve_suggestions=resolve_suggestions,
        resolve_match_summaries=resolve_match_summaries,
        entity_fields=entity_fields,
    )


def status_to_dict(summary: NetworkStatusSummary) -> dict[str, Any]:
    """Serialize a status summary for ``--json`` output."""
    data = asdict(summary)
    if summary.resolve is None:
        data.pop("resolve", None)
    else:
        resolve_out: dict[str, Any] = {}
        if summary.resolve.id:
            resolve_out["id"] = summary.resolve.id
        if summary.resolve.lookup:
            resolve_out["lookup"] = summary.resolve.lookup
        data["resolve"] = resolve_out
    return json.loads(json.dumps(data))


_POLICY_EXTENSIBILITY = (
    "You may request attributes that fit this network's domain. Each request is "
    "classified against the ontology. In-scope attributes are researched by "
    "specialist agents; a specialist is created automatically when one does not "
    "exist yet."
)
_POLICY_OUT_OF_SCOPE = (
    "If an attribute cannot be classified into this network's ontology, the query "
    "response will say it does not appear related to this network. Such attributes "
    "are not researched."
)
_POLICY_OUTCOME = (
    "Every query_entity response includes a machine-readable outcome field "
    "(lookup_resolved, lookup_incomplete, lookup_suggested, found, assembled, "
    "not_found, quote_required, payment_required, principal_required, or error). "
    "Read outcome before results; use message for per-attribute detail."
)
_POLICY_RESEARCH_GATE = (
    "Attribute research (specialists / Tavily) runs only when current_id is set and "
    "the entity is a validated registry row (including seed_bootstrap imports) or "
    "validation_state validated. Provisional registry entities with requested "
    "attributes return outcome found with identity-only results and a message that "
    "core validation must complete before researching attributes. Same-turn bind, "
    "validate, and research is supported when validation passes in one graph run."
)
_POLICY_METERING = (
    "When metering.enabled is true, billable attribute research and delivery require an "
    "accepted quote before specialists run. Responses with outcome quote_required include "
    "a structured quote (line_items, cache_state, total_usd). When metering.payment.enabled "
    "is also true: call pay_quote to settle, then retry query_entity with quote_id — "
    "outcome payment_required if quote_id is sent before pay_quote. Negotiation (MCP quotes) "
    "is separate from settlement (PaymentProvider / pay_quote). Set optional provenance=true "
    "on EntityQuery to request sources/audit trail (query_provenance meter). Outcome "
    "principal_required when billing principal is missing for sponsor_public or pool funding "
    "models. Bind and validate phases stay free. Default CRM keeps metering and payment disabled."
)
_POLICY_ENTITY_GROWTH = (
    "Network growth from queries: create-on-deliver writes a registry row (entities.json) "
    "with bind_values; validation promotes provisional rows; gated research writes "
    "extended attributes to specialist storage keyed by entity_id. Registry rows track "
    "attr_sources (attr → category slug) and last_researched_at after each successful "
    "research pass. Optional seed.json is bootstrap-only; registry rows are canonical "
    "at query time."
)
_POLICY_REGISTRY = (
    "Registry rows in entities.json store MVR bind fields in bind_values keyed by "
    "mvr.bind_fields (e.g. name, employer). bind_index is a generic compound key from "
    "normalized bind_values in policy order. Seed import maps seed rows[] into "
    "bind_values on refresh or network create."
)
_POLICY_STATUS_INSPECT = (
    "Status inspect (CLI network status --id / --lookup-json, admin GET /status): "
    "exact AND match on id or lookup only — no fuzzy lookup_suggested. Response "
    "includes resolve: { id, lookup } mirroring the inspect input, plus "
    "resolve_matches, resolve_kind, and entity_fields with versioned storage detail."
)
_POLICY_HISTORICAL = (
    "Pre-2026 entity_key / binding single-step protocol removed from public surfaces "
    "(Program 3, June 2026)."
)
_POLICY_QUERY_PROVENANCE = (
    "Set provenance=true on EntityQuery to attach structured version history on "
    "QueryResponse.provenance for requested extended attributes (bind fields omitted). "
    "Default results[] stay flat; provenance.entities[].attributes.<field> carries "
    "current_version_id and versions[] copied from specialist storage."
)
# Target protocol (MVR redesign M2–M9). Public CLI/MCP/admin use target fields since M9.
_POLICY_MVR_REDESIGN_TARGET = (
    "Target query protocol (MVR redesign M9+): Step 1 — send id OR "
    "lookup (AND within map); optional requested_attributes, provenance, "
    "confirm_new_entity, and grain (step 1 only) on step 1. Multi-grain "
    "networks fan out lookup per mvr.grains with per-grain key filtering; "
    "optional grain skips fan-out. On team grain use bind field name; team "
    "disambiguator key applies to player grain only. See docs/query-grain-router.md. "
    "Partial lookup searches the registry; "
    "lookup_incomplete returns required_fields for missing MVR bind keys when "
    "no near-miss bind-field matches; partial name or employer 0-hit may return "
    "lookup_suggested. "
    "Full MVR with 0 hits returns lookup_suggested when the same name exists "
    "under a different employer or a near-miss bind-field matches — retry step 1 "
    "with lookup merged from suggestions[].suggested_lookup (or suggestions[].id "
    "for one known row); set confirm_new_entity=true only to intentionally create "
    "a new bind after reviewing suggestions. "
    "lookup_resolved issues delivery.delivery_id (create_on_deliver true only "
    "when step 2 will create from full MVR with 0 registry hits). Step 2 — "
    "send delivery_id and optional quote_id only. Bind field names come from "
    "policy.mvr.bind_fields. See docs/plans/mvr-redesign-program.md."
)
_MVR_REDESIGN_STEP1_EXAMPLE: dict[str, Any] = {
    "request": {
        "lookup": {"employer": "IBM"},
        "requested_attributes": ["linkedin"],
        "provenance": False,
    },
    "response": {
        "outcome": "lookup_resolved",
        "total_matches": 237,
        "results": [],
        "delivery": {"delivery_id": "d_…", "expires_at": "…"},
        "quote": None,
    },
}
_MVR_REDESIGN_STEP2_EXAMPLE: dict[str, Any] = {
    "request": {"delivery_id": "d_…", "quote_id": "q_…"},
    "response": {
        "outcome": "assembled",
        "results": [{"id": "…", "name": "…", "employer": "…", "linkedin": "…"}],
    },
}
_QUERY_PROVENANCE_EXAMPLE: dict[str, Any] = {
    "provenance": {
        "entities": [
            {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "attributes": {
                    "linkedin": {
                        "current_version_id": "v1",
                        "versions": [
                            {
                                "id": "v1",
                                "at": "2026-06-11T12:00:00+00:00",
                                "status": "found",
                                "value": "https://linkedin.com/in/example",
                                "confidence": 0.9,
                                "sources": [{"url": "https://linkedin.com/in/example"}],
                                "actor": {
                                    "kind": "research",
                                    "category": "social",
                                    "specialist": "social_specialist",
                                },
                            },
                        ],
                    },
                },
            },
        ],
    },
}
_GUIDE_MISSING_NOTE = "Network author has not provided guide.md yet."


def _read_guide(paths: NetworkPaths) -> tuple[bool, str | None]:
    guide_path = paths.root / "guide.md"
    if not guide_path.is_file():
        return False, None
    try:
        return True, guide_path.read_text(encoding="utf-8")
    except OSError:
        return False, None


def _ontology_capabilities(categories_doc: dict[str, Any] | None) -> dict[str, Any]:
    if not categories_doc:
        return {
            "present": False,
            "message": "not created yet — run a query to bootstrap categories.json",
            "categories": [],
        }
    raw_categories = categories_doc.get("categories")
    if not isinstance(raw_categories, dict):
        return {
            "present": False,
            "message": "categories.json present but invalid",
            "categories": [],
        }
    categories: list[dict[str, Any]] = []
    for name, meta in sorted(raw_categories.items()):
        if not isinstance(meta, dict):
            continue
        description = meta.get("description")
        raw_examples = meta.get("examples")
        categories.append(
            {
                "name": str(name),
                "description": description if isinstance(description, str) else "",
                "examples": (
                    [str(item) for item in raw_examples]
                    if isinstance(raw_examples, list)
                    else []
                ),
            },
        )
    return {
        "present": True,
        "message": None,
        "categories": categories,
    }


def build_network_capabilities() -> dict[str, Any]:
    """Build connect-time MCP onboarding payload (guide, ontology, policy)."""
    paths = _paths()
    meta = network_metadata(root=paths.root)
    categories_doc = _read_categories(paths)
    guide_present, guide_text = _read_guide(paths)

    payload: dict[str, Any] = {
        "network_name": meta.get("network_name"),
        "display_name": meta.get("network_display_name"),
        "guide_present": guide_present,
        "guide": guide_text,
        "ontology": _ontology_capabilities(categories_doc),
        "policy": {
            "extensibility": _POLICY_EXTENSIBILITY,
            "out_of_scope": _POLICY_OUT_OF_SCOPE,
            "outcome": _POLICY_OUTCOME,
            "registry": _POLICY_REGISTRY,
            "status_inspect": _POLICY_STATUS_INSPECT,
            "mvr": load_mvr_config(paths=paths).summary(),
            "research_gate": _POLICY_RESEARCH_GATE,
            "metering": _POLICY_METERING,
            "metering_policy": load_metering_policy(paths=paths).summary(),
            "entity_growth": _POLICY_ENTITY_GROWTH,
            "historical": _POLICY_HISTORICAL,
            "query": {
                "tool": "query_entity",
                "request_schema": "mycelium://schema/entity-query",
                "response_schema": "mycelium://schema/query-response",
                "key_field": "lookup",
                "optional_fields": [
                    "id",
                    "lookup",
                    "delivery_id",
                    "requested_attributes",
                    "thread_id",
                    "quote_id",
                    "principal",
                    "provenance",
                    "confirm_new_entity",
                ],
                "response_provenance": {
                    "description": _POLICY_QUERY_PROVENANCE,
                    "response_field": "provenance",
                    "request_flag": "provenance",
                    "example": _QUERY_PROVENANCE_EXAMPLE,
                },
                "protocol_status": "target two-step (id/lookup → delivery_id)",
                "target_protocol": {
                    "description": _POLICY_MVR_REDESIGN_TARGET,
                    "shipping": "MVR redesign program — live since M9",
                    "docs": [
                        "docs/plans/mvr-redesign-program.md",
                        "docs/plans/mvr-best-practices.md",
                        "docs/plans/mvr-redesign-entity-query-examples.md",
                    ],
                    "step1_example": _MVR_REDESIGN_STEP1_EXAMPLE,
                    "step2_example": _MVR_REDESIGN_STEP2_EXAMPLE,
                    "target_fields_step1": ["id", "lookup", "requested_attributes", "provenance"],
                    "target_fields_step2": ["delivery_id", "quote_id"],
                    "target_outcomes": [
                        "lookup_resolved",
                        "quote_required",
                        "not_found",
                        "assembled",
                        "found",
                    ],
                },
            },
        },
    }
    if not guide_present:
        payload["guide_note"] = _GUIDE_MISSING_NOTE
    return payload


def format_mcp_instructions(capabilities: dict[str, Any]) -> str:
    """Render MCP server instructions from network capabilities."""
    display_name = capabilities.get("display_name") or capabilities.get("network_name") or "network"
    network_name = capabilities.get("network_name") or "network"
    text = (
        f"Mycelium network **{display_name}** (`{network_name}`). "
        "Call **`describe_network`** for the author guide, ontology, and usage policy. "
        "Use **`query_entity`** with JSON: step 1 — `id` or `lookup` (+ optional "
        "`requested_attributes`, `provenance`); step 2 — `delivery_id` (+ `quote_id` "
        "after quote_required / pay_quote). "
        "When payment is enabled: quote_required → **`pay_quote`** → step 2 with quote_id. "
        "Responses are **`QueryResponse`** "
        "(`outcome`, `delivery`, `total_matches`, `quote`, `results`, `message`, "
        "`provenance` when step 1 set provenance=true, `debug`, `trace_id`, `thread_id`). "
        "Step 1 outcomes: `lookup_resolved`, `quote_required`, `not_found`. "
        "Step 2 outcomes: `found`, `assembled`. "
        "Use **`health_check`** for server liveness and network binding. "
        "See describe_network policy.query for step examples. "
        "Registry, categories, seed, and specialists reload from disk before each query — "
        "restart MCP only after code deploy or if reload fails."
    )
    if capabilities.get("display_name") or capabilities.get("network_name"):
        if (
            capabilities.get("display_name")
            and capabilities.get("network_name")
            and capabilities["display_name"] != capabilities["network_name"]
        ):
            label = f"{capabilities['display_name']} ({capabilities['network_name']})"
        else:
            label = capabilities.get("display_name") or capabilities.get("network_name")
        text += f" Active network: {label}."
    return text


def _specialists_have_storage(specialists: list[SpecialistSummary]) -> bool:
    """True when any specialist has persisted records or field activity."""
    return any(
        spec.record_count > 0
        or spec.fields_tracked
        or spec.pending_count
        or spec.na_count
        or spec.found_count
        for spec in specialists
    )


def _format_network_header(summary: NetworkStatusSummary) -> str:
    label = summary.network_name or "network"
    if summary.display_name and summary.display_name != summary.network_name:
        return f"Network: {label} ({summary.display_name})"
    return f"Network: {label}"


def format_category_examples(category_name: str, examples: list[str] | tuple[str, ...]) -> str:
    """Format one ontology category line for demo output."""
    items = list(examples)
    if not items:
        return category_name
    if len(items) == 1:
        return f"{category_name} (e.g., {items[0]})"
    if len(items) == 2:
        return f"{category_name} (e.g., {items[0]}, {items[1]})"
    return f"{category_name} (e.g., {items[0]}, {items[1]}, …)"


def _format_resolve_label(resolve: StatusResolve) -> str:
    if resolve.id:
        return resolve.id
    if resolve.lookup:
        return ", ".join(f"{key}={value!r}" for key, value in resolve.lookup.items())
    return "?"


def _format_entity_drill_down(summary: NetworkStatusSummary) -> list[str]:
    if summary.resolve is None:
        return []
    kind = summary.resolve_kind or "unknown"
    label = _format_resolve_label(summary.resolve)
    lines = [
        f"Resolve: {label!r} ({summary.resolve_matches} match(es), {kind})",
    ]
    if summary.resolve_required_fields:
        lines.append(
            f"  Required fields: {', '.join(summary.resolve_required_fields)}",
        )
    if summary.resolve_suggestions:
        lines.append("  Suggestions:")
        for item in summary.resolve_suggestions[:3]:
            suggested = item.get("suggested_lookup") or {}
            if suggested:
                label = ", ".join(f"{key}={value!r}" for key, value in suggested.items())
            else:
                label = item.get("name") or "?"
            lines.append(
                f"    {label} (score={item.get('score')})",
            )
    if summary.resolve_matches == 0:
        lines.append("  No match.")
    elif summary.resolve_matches > 1:
        lines.append("  Multiple matches — narrow the key.")
        for match in summary.resolve_match_summaries:
            source = match.source
            validation = (
                f" {match.validation_state}" if match.validation_state else ""
            )
            lines.append(
                f"    {match.name} ({match.id}) [{source}{validation}]",
            )
    elif summary.entity_fields:
        lines.append("  Fields:")
        for item in summary.entity_fields:
            value = f" value={item.value!r}" if item.value else ""
            lines.append(
                f"    {item.field} ({item.category}/{item.agent}): "
                f"{item.status}{value}",
            )
    else:
        lines.append("  No specialist storage for this record yet.")
    return lines


def format_status_demo(summary: NetworkStatusSummary) -> str:
    """Render a scannable demo-oriented status report (default CLI layout)."""
    lines = [_format_network_header(summary)]
    entity_mark = "✅" if summary.registry_entity_count > 0 else "❌"
    lines.append(f"Entities: {entity_mark} ({summary.registry_entity_count})")

    if summary.ontology_present and summary.categories:
        lines.append("Current ontology:")
        for category in summary.categories:
            lines.append(
                f"  {format_category_examples(category.name, category.examples)}",
            )
    else:
        lines.append("Current ontology: ❌")

    stored = [
        spec for spec in summary.specialists if spec.record_count > 0
    ]
    if stored:
        lines.append("Existing specialists:")
        for spec in sorted(stored, key=lambda item: item.category):
            lines.append(f"  {spec.category} ({spec.record_count})")
    else:
        lines.append("Existing specialists: ❌")

    if summary.resolve is not None:
        lines.extend(_format_entity_drill_down(summary))
    return "\n".join(lines)


def format_status_verbose(summary: NetworkStatusSummary) -> str:
    """Render a debug-oriented status report (``--verbose``)."""
    lines = [_format_network_header(summary)]
    lines.append(f"Root: {summary.network_root}")
    lines.append(f"Entities: {summary.registry_entity_count} records")
    if summary.ontology_present:
        lines.append(f"Ontology: {len(summary.categories)} categories")
        for category in summary.categories:
            agent = category.assigned_agent or "—"
            lines.append(
                f"  {category.name}: agent={agent} examples={category.example_count}",
            )
    else:
        lines.append(f"Ontology: {summary.ontology_message}")

    if summary.specialists and _specialists_have_storage(summary.specialists):
        lines.append("Specialists:")
        for spec in summary.specialists:
            module = "yes" if spec.module_on_disk else "no"
            fields = ", ".join(spec.fields_tracked) if spec.fields_tracked else "—"
            lines.append(
                f"  {spec.name}  category={spec.category}  module={module}  "
                f"records={spec.record_count}  fields={fields}",
            )
            if spec.pending_count or spec.na_count or spec.found_count:
                lines.append(
                    f"    status counts: found={spec.found_count} "
                    f"pending={spec.pending_count} na={spec.na_count}",
                )
    elif summary.ontology_present and summary.categories:
        lines.append(
            "Specialists: none with storage yet "
            f"(ontology defines {len(summary.categories)} categories)",
        )
    else:
        lines.append("Specialists: none registered")

    lines.extend(_format_entity_drill_down(summary))
    return "\n".join(lines)


def format_status_human(summary: NetworkStatusSummary) -> str:
    """Alias for verbose layout (backward compatibility)."""
    return format_status_verbose(summary)
