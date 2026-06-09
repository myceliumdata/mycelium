"""Read-only network snapshot for CLI status and future admin daemon."""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from agents.seed import find_by_key, get_seed_data
from agents.specialists.base import category_slug
from network.mvr import load_mvr
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


@dataclass(frozen=True)
class NetworkStatusSummary:
    network_name: str | None
    network_root: str
    display_name: str | None
    seed_people_count: int
    ontology_present: bool
    ontology_message: str
    categories: list[CategorySummary] = field(default_factory=list)
    specialists: list[SpecialistSummary] = field(default_factory=list)
    entity_key: str | None = None
    entity_matches: int = 0
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


def _storage_file(paths: NetworkPaths, category: str) -> Path:
    return paths.agents_dir / category_slug(category) / "storage.json"


def _strategy_file(paths: NetworkPaths, category: str) -> Path:
    return paths.agents_dir / category_slug(category) / "storage_strategy.json"


def _analyze_storage(paths: NetworkPaths, category: str) -> SpecialistSummary:
    storage_path = _storage_file(paths, category)
    strategy_path = _strategy_file(paths, category)
    strategy_name: str | None = None
    if strategy_path.is_file():
        try:
            strategy_payload = json.loads(strategy_path.read_text(encoding="utf-8"))
            if isinstance(strategy_payload, dict):
                raw = strategy_payload.get("strategy")
                strategy_name = raw if isinstance(raw, str) else None
        except (OSError, json.JSONDecodeError):
            strategy_name = None

    record_count = 0
    fields_tracked: set[str] = set()
    pending = na = found = 0

    if storage_path.is_file():
        try:
            payload = json.loads(storage_path.read_text(encoding="utf-8"))
            records = payload.get("records", {}) if isinstance(payload, dict) else {}
            if isinstance(records, dict):
                record_count = len(records)
                for record in records.values():
                    if not isinstance(record, dict):
                        continue
                    for field_name, value in record.items():
                        fields_tracked.add(field_name)
                        if isinstance(value, dict) and "status" in value:
                            status = str(value.get("status", "")).lower()
                            if status == "pending":
                                pending += 1
                            elif status == "na":
                                na += 1
                            elif status == "found" or value.get("value"):
                                found += 1
                        elif value not in (None, ""):
                            found += 1
        except (OSError, json.JSONDecodeError):
            pass

    return SpecialistSummary(
        name="",
        category=category,
        module_on_disk=False,
        storage_strategy=strategy_name,
        record_count=record_count,
        fields_tracked=sorted(fields_tracked),
        pending_count=pending,
        na_count=na,
        found_count=found,
    )


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
                storage_strategy=storage.storage_strategy,
                record_count=storage.record_count,
                fields_tracked=storage.fields_tracked,
                pending_count=storage.pending_count,
                na_count=storage.na_count,
                found_count=storage.found_count,
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
    statuses: list[EntityFieldStatus] = []
    seen_categories: set[str] = set()
    for agent_name, category in sorted(agent_map.items(), key=lambda item: item[1]):
        if category_filter and category != category_filter:
            continue
        if category in seen_categories:
            continue
        seen_categories.add(category)
        storage_path = _storage_file(paths, category)
        if not storage_path.is_file():
            continue
        try:
            payload = json.loads(storage_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        records = payload.get("records", {}) if isinstance(payload, dict) else {}
        if not isinstance(records, dict):
            continue
        record = records.get(record_id)
        if not isinstance(record, dict):
            continue
        for field_name, value in sorted(record.items()):
            status = "empty"
            display_value: str | None = None
            if isinstance(value, dict):
                raw_status = value.get("status")
                status = str(raw_status) if raw_status else "empty"
                raw_value = value.get("value")
                display_value = str(raw_value) if raw_value is not None else None
            elif value not in (None, ""):
                status = "found"
                display_value = str(value)
            statuses.append(
                EntityFieldStatus(
                    field=field_name,
                    category=category,
                    agent=agent_name,
                    status=status,
                    value=display_value,
                ),
            )
    return statuses


def build_network_status(
    *,
    category_filter: str | None = None,
    entity_key: str | None = None,
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

    seed_count = len(get_seed_data().people)
    registry_agents = _read_registry_agents(paths)
    agent_map = _agent_category_map(categories_doc, registry_agents)

    entity_fields: list[EntityFieldStatus] = []
    entity_matches = 0
    if entity_key:
        matches = find_by_key(entity_key)
        entity_matches = len(matches)
        if len(matches) == 1:
            entity_fields = _entity_field_statuses(
                paths,
                matches[0]["id"],
                agent_map,
                category_filter=category_filter,
            )

    return NetworkStatusSummary(
        network_name=meta.get("network_name"),
        network_root=str(paths.root),
        display_name=meta.get("network_display_name"),
        seed_people_count=seed_count,
        ontology_present=ontology_present,
        ontology_message=ontology_message,
        categories=_category_summaries(categories_doc, category_filter=category_filter),
        specialists=_specialist_summaries(
            paths,
            agent_map,
            category_filter=category_filter,
        ),
        entity_key=entity_key,
        entity_matches=entity_matches,
        entity_fields=entity_fields,
    )


def status_to_dict(summary: NetworkStatusSummary) -> dict[str, Any]:
    """Serialize a status summary for ``--json`` output."""
    return asdict(summary)


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
    "(found, assembled, not_found, entity_key_unresolved, entity_unknown, or error). "
    "Read outcome before results; use message for per-attribute detail."
)
_POLICY_ENTITY_UNKNOWN = (
    'When outcome is "entity_unknown", the entity_key had no seed match and no '
    "near-miss suggestions. required_fields lists MVR bind fields still needed "
    "(for CRM: employer when name comes from entity_key). Re-query with the same "
    "entity_key and binding when ready."
)
_POLICY_ENTITY_BIND = (
    'Supply MVR fields in query_entity JSON via binding (e.g. {"employer": "Acme Corp"}). '
    'On outcome entity_bound_provisional, results include id, name, and employer — '
    "use the bound uuid as entity_key for follow-ups. Duplicate bind returns found "
    "with the same id. After bind, core validation runs automatically; outcome "
    "entity_validated when MVR passes."
)
_POLICY_RESEARCH_GATE = (
    "Attribute research (specialists / Tavily) runs only when current_id is set and "
    "the entity is a seed match (pre-validated) or a registry row with "
    "validation_state validated. Provisional registry entities with requested "
    "attributes return outcome found with identity-only results and a message that "
    "core validation must complete before researching attributes. Same-turn bind, "
    "validate, and research is supported when validation passes in one graph run."
)
_POLICY_ENTITY_VALIDATED = (
    'When outcome is "entity_validated", provisional registry entity passed rule-based '
    "MVR checks (name and employer). The entity is promoted to validated in entities.json."
)
_POLICY_ENTITY_GROWTH = (
    "Network growth from queries: bind creates a registry row (entities.json), validation "
    "promotes it, gated research writes extended attributes to specialist storage keyed by "
    "entity_id. Registry rows track attr_sources (attr → category slug) and "
    "last_researched_at after each successful research pass. Seed remains bootstrap origin; "
    "registry rows override seed on conflict for the same bind key."
)
_POLICY_ENTITY_KEY_UNRESOLVED = (
    'When outcome is "entity_key_unresolved", the entity_key had no exact seed match '
    "but near-miss suggestions are provided in suggestions[]. Re-query with "
    "query_entity using a chosen suggestions[].entity_key (usually the highest score). "
    "No attribute data is authoritative until an exact match resolves. "
    "If suggestions are empty and the name is not a near-miss, expect entity_unknown."
)
_POLICY_MULTI_MATCH = (
    "When entity_key matches multiple seed records, results contains every match. "
    "Disambiguate using fields in each record (for example id and employer on CRM "
    "networks). The message summarizes status collectively unless per-record "
    "messaging is added later."
)
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
            "multi_match": _POLICY_MULTI_MATCH,
            "outcome": _POLICY_OUTCOME,
            "mvr": load_mvr(paths=paths).summary(),
            "entity_unknown": _POLICY_ENTITY_UNKNOWN,
            "entity_bind": _POLICY_ENTITY_BIND,
            "research_gate": _POLICY_RESEARCH_GATE,
            "entity_validated": _POLICY_ENTITY_VALIDATED,
            "entity_growth": _POLICY_ENTITY_GROWTH,
            "entity_key_unresolved": _POLICY_ENTITY_KEY_UNRESOLVED,
            "query": {
                "tool": "query_entity",
                "request_schema": "mycelium://schema/entity-query",
                "response_schema": "mycelium://schema/query-response",
                "key_field": "entity_key",
                "optional_fields": ["requested_attributes", "binding", "thread_id"],
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
        "Use **`query_entity`** with JSON: `entity_key`, optional `requested_attributes`, "
        "optional `thread_id`. Responses are **`QueryResponse`** "
        "(`outcome`, `suggestions`, `required_fields`, `results`, `message`, `debug`, "
        "`trace_id`, `thread_id`); read **`message`** for per-attribute status. "
        "On **`outcome: entity_key_unresolved`**, retry with a **`suggestions[].entity_key`**. "
        "On **`entity_unknown`**, supply **`binding`** per MVR **`required_fields`**. "
        "Use **`health_check`** for server liveness and network binding. "
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


def _format_entity_drill_down(summary: NetworkStatusSummary) -> list[str]:
    if not summary.entity_key:
        return []
    lines = [
        f"Entity lookup: {summary.entity_key!r} ({summary.entity_matches} match(es))",
    ]
    if summary.entity_matches == 0:
        lines.append("  No seed match.")
    elif summary.entity_matches > 1:
        lines.append("  Multiple seed matches — narrow the key.")
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
    lines.append(f"Seed: ✅ ({summary.seed_people_count})")

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

    if summary.entity_key:
        lines.extend(_format_entity_drill_down(summary))
    return "\n".join(lines)


def format_status_verbose(summary: NetworkStatusSummary) -> str:
    """Render a debug-oriented status report (``--verbose``)."""
    lines = [_format_network_header(summary)]
    lines.append(f"Root: {summary.network_root}")
    lines.append(f"Seed: {summary.seed_people_count} records")
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
