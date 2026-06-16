"""Dispatch specialist storage I/O — framework entry point (no direct storage access)."""

from __future__ import annotations

from typing import Any, Callable

from agents.registry import RegisteredAgent, get_agent_registry


def resolve_owner(attribute: str) -> tuple[str, str]:
    """Return ``(category, assigned_agent)`` from ``categories.json`` ``attribute_map``."""
    from agents.classification import get_category_tree

    normalized = attribute.strip().lower()
    if not normalized:
        raise ValueError("attribute name is required")

    tree = get_category_tree()
    category = tree.mapped_category(normalized)
    if not category:
        raise ValueError(
            f"MVR bind field {attribute!r} is not mapped in categories.json attribute_map",
        )

    categories = tree.get_categories()
    cat = categories.get(category)
    if cat is None or not cat.assigned_agent:
        raise ValueError(
            f"category {category!r} has no assigned_agent for attribute {attribute!r}",
        )
    return category, cat.assigned_agent



def _load_specialist_module(agent_name: str) -> Any:
    import importlib.util
    import sys

    from network.paths import runtime_path

    registry = get_agent_registry()
    for raw in registry.list_agents():
        if raw.get("name") == agent_name:
            entry = RegisteredAgent.model_validate(raw)
            specialists_dir = runtime_path("MYCELIUM_SPECIALISTS_DIR")
            py_file = specialists_dir / f"{entry.name}.py"
            if py_file.is_file():
                spec = importlib.util.spec_from_file_location(
                    f"dyn_specialist_{entry.name}",
                    str(py_file),
                )
                if spec and spec.loader:
                    mod = importlib.util.module_from_spec(spec)
                    sys.modules[spec.name] = mod
                    spec.loader.exec_module(mod)
                    return mod
            return importlib.import_module(entry.module_path)

    fallback = f"agents.specialists.{agent_name}"
    try:
        return importlib.import_module(fallback)
    except ModuleNotFoundError as exc:
        raise ValueError(f"Unknown specialist agent: {agent_name!r}") from exc


def _call_handler(
    agent_name: str,
    handler: str,
    *args: Any,
    **kwargs: Any,
) -> Any:
    mod = _load_specialist_module(agent_name)
    fn: Callable[..., Any] | None = getattr(mod, handler, None)
    if fn is None:
        raise ValueError(
            f"Specialist {agent_name!r} missing handler {handler!r}",
        )
    return fn(*args, **kwargs)


def dispatch_write_fields(
    agent_name: str,
    entity_id: str,
    fields: dict[str, str],
    *,
    actor_kind: str,
    at: str | None = None,
) -> dict[str, str]:
    return _call_handler(
        agent_name,
        "write_fields",
        entity_id,
        fields,
        actor_kind=actor_kind,
        at=at,
    )


def dispatch_read_fields(
    agent_name: str,
    entity_id: str,
    fields: list[str],
    *,
    include_versions: bool = False,
    include_provenance: bool | None = None,
) -> dict[str, Any]:
    """Return ``{field: FieldSnapshot}`` for each requested field key."""
    kwargs: dict[str, Any] = {}
    if include_provenance is not None:
        kwargs["include_provenance"] = include_provenance
    else:
        kwargs["include_versions"] = include_versions
    return _call_handler(
        agent_name,
        "read_fields",
        entity_id,
        fields,
        **kwargs,
    )


def dispatch_bootstrap_entity(
    agent_name: str,
    entity_id: str,
    fields: dict[str, str],
    *,
    actor_kind: str = "seed_bootstrap",
) -> dict[str, str]:
    return _call_handler(
        agent_name,
        "bootstrap_entity",
        entity_id,
        fields,
        actor_kind=actor_kind,
    )


def dispatch_write_bind_fields_multi(
    entity_id: str,
    normalized_fields: dict[str, str],
    *,
    actor_kind: str,
    at: str,
) -> dict[str, str]:
    from agents.specialists.handlers import write_bind_fields_multi

    return write_bind_fields_multi(
        entity_id,
        normalized_fields,
        resolve_owner=resolve_owner,
        actor_kind=actor_kind,
        at=at,
    )


def dispatch_read_category_slice(
    agent_name: str,
    category: str,
    entity_ids: list[str],
    *,
    bind_fields: frozenset[str] | set[str] | None = None,
) -> dict[str, dict[str, Any]]:
    from agents.specialists.handlers import read_category_slice

    _ = agent_name
    return read_category_slice(category, entity_ids, bind_fields=bind_fields)


def dispatch_analyze_category_storage(category: str) -> dict[str, Any]:
    from agents.specialists.handlers import analyze_category_storage

    return analyze_category_storage(category)


def dispatch_entity_field_statuses(
    agent_name: str,
    category: str,
    entity_id: str,
) -> list[dict[str, Any]]:
    from agents.specialists.handlers import entity_field_statuses_for_category

    return entity_field_statuses_for_category(category, agent_name, entity_id)


def dispatch_ensure_category_storage(category: str) -> None:
    from agents.specialists.handlers import ensure_category_storage

    ensure_category_storage(category)


def dispatch_mark_pending(
    category: str,
    specialist_name: str,
    entity_id: str,
    fields: list[str],
    *,
    last_error: str,
) -> None:
    from agents.specialists.research_handlers import mark_pending

    mark_pending(
        category,
        specialist_name,
        entity_id,
        fields,
        last_error=last_error,
    )


def dispatch_persist_research(
    category: str,
    specialist_name: str,
    entity_id: str,
    proposal: Any,
    *,
    allowed: set[str],
    min_confidence: float,
    validate_and_build: Callable[..., tuple[dict[str, Any] | None, str | None]],
) -> tuple[list[str], list[str]]:
    from agents.specialists.research_handlers import persist_proposal

    return persist_proposal(
        category,
        specialist_name,
        entity_id,
        proposal,
        allowed=allowed,
        min_confidence=min_confidence,
        validate_and_build=validate_and_build,
    )


def dispatch_append_research_audit(
    category: str,
    specialist_name: str,
    entity_id: str,
    *,
    fields_updated: list[str],
    tool_calls_count: int,
    errors: list[str],
    context_bind: dict[str, str] | None = None,
) -> None:
    from agents.specialists.research_handlers import append_research_audit

    append_research_audit(
        category,
        specialist_name,
        entity_id,
        fields_updated=fields_updated,
        tool_calls_count=tool_calls_count,
        errors=errors,
        context_bind=context_bind,
    )
