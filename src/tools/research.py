"""Category-agnostic specialist field research (LLM + Tavily web_search).

Phase 1: synchronous execution from specialist nodes (slice 1200). The runner API
is designed so async dispatch can call the same validation/persist path later.
"""

from __future__ import annotations

import json
import os
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

import jinja2
from pydantic import BaseModel, Field

from agents.specialist_fields import (
    append_version,
    current_status,
    current_value,
    current_version,
    ensure_versioned_for_write,
    field_has_value,
    is_versioned_field,
    research_actor,
    update_current_pending,
)
from agents.specialists.base import SpecialistStorage
from network.mvr import MvrPolicy, load_mvr
from network.env_util import env_int
from tools.tavily import create_tavily_search_tool, is_web_search_available

_RESEARCH_TEMPLATE_DIR = (
    Path(__file__).resolve().parent.parent / "agents" / "factory" / "templates" / "research"
)
class FieldProposal(BaseModel):
    """One researched attribute proposal from the LLM."""

    field: str
    value: str | None = None
    status: Literal["found", "na"] = "na"
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    sources: list[str] = Field(default_factory=list)
    reason: str | None = None


class ResearchProposal(BaseModel):
    """Structured output from the research LLM."""

    fields: list[FieldProposal] = Field(default_factory=list)
    notes: str = ""


@dataclass
class ResearchRunResult:
    """Outcome of a single run_field_research invocation."""

    fields_updated: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    tool_calls_count: int = 0


def _env_float(name: str, default: float) -> float:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def research_min_confidence() -> float:
    return _env_float("MYCELIUM_RESEARCH_MIN_CONFIDENCE", 0.6)


def research_max_tool_rounds() -> int:
    return env_int("MYCELIUM_RESEARCH_MAX_TOOL_ROUNDS", 3)


def research_timeout_sec() -> int:
    return env_int("MYCELIUM_RESEARCH_TIMEOUT_SEC", 120)


def research_model() -> str:
    return os.getenv("MYCELIUM_RESEARCH_MODEL", "gpt-4o-mini").strip() or "gpt-4o-mini"


def is_research_available() -> bool:
    """True when both OpenAI and Tavily keys are configured."""
    return bool(os.getenv("OPENAI_API_KEY", "").strip()) and is_web_search_available()


def load_category_metadata(category: str) -> dict[str, Any]:
    """Load category description and examples from the classification tree cache."""
    from agents.classification import get_category_tree

    slug = category.strip().lower()
    tree = get_category_tree()
    if tree._data is None or slug not in tree._data.categories:
        return {"description": "", "examples": [], "assigned_agent": ""}
    cat = tree._data.categories[slug]
    return {
        "description": cat.description,
        "examples": list(cat.examples),
        "assigned_agent": cat.assigned_agent or "",
    }


def _normalize_fields(target_fields: list[str]) -> list[str]:
    return [f.strip().lower() for f in target_fields if f and f.strip()]


def _jinja_env() -> jinja2.Environment:
    return jinja2.Environment(
        loader=jinja2.FileSystemLoader(_RESEARCH_TEMPLATE_DIR.parent),
        trim_blocks=True,
        lstrip_blocks=True,
    )


def bind_disambiguators(context: dict[str, Any], mvr: MvrPolicy) -> dict[str, str]:
    """Non-empty bind values for fields declared in MVR bind_fields."""
    bind = context.get("bind")
    if not isinstance(bind, dict):
        return {}
    result: dict[str, str] = {}
    for bind_field in mvr.bind_fields:
        key = bind_field.strip().lower()
        if not key:
            continue
        raw = bind.get(key)
        if raw is None:
            raw = bind.get(bind_field)
        text = str(raw or "").strip()
        if text:
            result[key] = text
    return result


def has_extra_bind_disambiguators(disambiguators: dict[str, str]) -> bool:
    """True when any non-name bind field has a value (triggers mandatory search rules)."""
    return any(key != "name" for key in disambiguators)


def _looks_like_field_record_map(records: dict[str, Any]) -> bool:
    """True when dict keys are field names mapping to specialist storage records."""
    if not records:
        return False
    for value in records.values():
        if not isinstance(value, dict):
            return False
        if is_versioned_field(value) or "status" in value:
            continue
        return False
    return True


def _peer_category_row(records: dict[str, Any], entity_id: str) -> dict[str, Any] | None:
    """Field records for entity_id, or a flattened row already scoped to one entity."""
    nested = records.get(entity_id)
    if isinstance(nested, dict) and nested and _looks_like_field_record_map(nested):
        return nested
    if _looks_like_field_record_map(records):
        return records
    return None


def _trim_peer_fields(row: dict[str, Any]) -> dict[str, Any]:
    """Keep found peer fields only (omit pending/na from prominent block)."""
    return {
        key: value
        for key, value in row.items()
        if isinstance(value, dict) and field_has_value(value)
    }


def peer_specialists_for_entity(
    context: dict[str, Any],
    *,
    entity_id: str,
    category: str,
) -> dict[str, Any]:
    """Peer category slices for entity_id (exclude own category; found fields only)."""
    specialists = context.get("specialists")
    if not isinstance(specialists, dict):
        return {}
    own = category.strip().lower()
    peers: dict[str, Any] = {}
    for cat, records in specialists.items():
        cat_key = str(cat).strip().lower()
        if cat_key == own or not isinstance(records, dict):
            continue
        row = _peer_category_row(records, entity_id)
        if not isinstance(row, dict) or not row:
            continue
        trimmed = _trim_peer_fields(row)
        if trimmed:
            peers[cat_key] = trimmed
    return peers


def peer_display_for_prompt(peer_specialists: dict[str, Any]) -> dict[str, list[dict[str, str]]]:
    """Human-readable peer lines grouped by category for the prompt template."""
    display: dict[str, list[dict[str, str]]] = {}
    for cat, fields in peer_specialists.items():
        lines: list[dict[str, str]] = []
        for peer_field, record in fields.items():
            if not isinstance(record, dict) or not field_has_value(record):
                continue
            value = str(current_value(record) or "").strip()
            if not value:
                continue
            version = current_version(record) if is_versioned_field(record) else record
            sources = (version or {}).get("sources") or record.get("sources") or []
            if sources and isinstance(sources[0], dict):
                source = str(sources[0].get("url") or "").strip()
            else:
                source = str(sources[0]).strip() if sources else ""
            lines.append({"field": peer_field, "value": value, "source": source})
        if lines:
            display[cat] = lines
    return display


def format_peer_context_block(peer_display: dict[str, list[dict[str, str]]]) -> str:
    """Plain-text peer findings block (avoids Jinja trim_blocks eating newlines)."""
    lines = [
        "PEER SPECIALIST FINDINGS (read-only):",
        "Use these to disambiguate the person and inform searches. "
        "Do not write peer fields unless listed in target_fields.",
        "",
    ]
    for cat, items in peer_display.items():
        lines.append(f"{cat}:")
        for item in items:
            suffix = f" (sources: {item['source']})" if item.get("source") else ""
            lines.append(f"  - {item['field']}: {item['value']}{suffix}")
        lines.append("")
    while lines and not lines[-1]:
        lines.pop()
    return "\n".join(lines)


def operator_overrides_for_target_fields(
    context: dict[str, Any],
    target_fields: list[str],
) -> list[dict[str, Any]]:
    """Return operator-set current versions for target fields in specialist storage."""
    storage = context.get("storage")
    if not isinstance(storage, dict):
        return []
    overrides: list[dict[str, Any]] = []
    for field_name in _normalize_fields(target_fields):
        entry = storage.get(field_name)
        if not is_versioned_field(entry):
            continue
        version = current_version(entry)
        if not isinstance(version, dict):
            continue
        actor = version.get("actor")
        if not isinstance(actor, dict) or actor.get("kind") != "operator":
            continue
        overrides.append(
            {
                "field": field_name,
                "value": version.get("value"),
                "at": version.get("at"),
                "note": version.get("note") or version.get("reason"),
            },
        )
    return overrides


def _current_actor_kind(entry: Any) -> str | None:
    if not isinstance(entry, dict) or not is_versioned_field(entry):
        return None
    version = current_version(entry)
    if not isinstance(version, dict):
        return None
    actor = version.get("actor")
    if isinstance(actor, dict):
        raw = actor.get("kind")
        return str(raw) if raw else None
    return None


def build_research_prompts(
    *,
    category: str,
    specialist_name: str,
    person_id: str,
    target_fields: list[str],
    context: dict[str, Any],
) -> tuple[str, str]:
    """Return (system_message, user_message) for the research LLM."""
    env = _jinja_env()
    meta = load_category_metadata(category)
    min_conf = research_min_confidence()
    mvr = load_mvr()
    disambiguators = bind_disambiguators(context, mvr)
    extra_disamb = has_extra_bind_disambiguators(disambiguators)
    peer_specialists = peer_specialists_for_entity(
        context,
        entity_id=person_id,
        category=category,
    )
    peer_display = peer_display_for_prompt(peer_specialists)
    operator_overrides = operator_overrides_for_target_fields(context, target_fields)
    template_vars = {
        "category": category,
        "specialist_name": specialist_name,
        "min_confidence": min_conf,
        "bind_disambiguators": disambiguators,
        "has_extra_bind_disambiguators": extra_disamb,
        "mvr_bind_fields": list(mvr.bind_fields),
        "has_peer_specialists": bool(peer_display),
        "peer_specialists": peer_specialists,
        "peer_display": peer_display,
        "operator_overrides": operator_overrides,
        "has_operator_overrides": bool(operator_overrides),
    }

    system_tpl = env.get_template("research/_system.j2")
    system = system_tpl.render(**template_vars)

    fragment_name = f"research/{category.strip().lower()}.md.j2"
    try:
        fragment = env.get_template(fragment_name).render().strip()
    except jinja2.TemplateNotFound:
        fragment = ""

    user_payload = {
        "person_id": person_id,
        "category": category,
        "specialist_name": specialist_name,
        "category_description": meta.get("description"),
        "category_examples": meta.get("examples"),
        "target_fields": target_fields,
        "context": context,
        "min_confidence": min_conf,
    }
    user_parts = [
        "Research the following person for the listed target_fields only.",
        json.dumps(user_payload, indent=2, default=str),
    ]
    if fragment:
        user_parts.insert(1, f"Category guidance:\n{fragment}")
    if extra_disamb:
        disambiguation = env.get_template("research/_disambiguation.j2").render(**template_vars).strip()
        user_parts.insert(0, disambiguation)
    if operator_overrides:
        operator_block = env.get_template("research/_operator_deference.j2").render(
            **template_vars,
        ).strip()
        insert_at = 1 if extra_disamb else 0
        user_parts.insert(insert_at, operator_block)
    if peer_display:
        peer_block = format_peer_context_block(peer_display)
        insert_at = 1 if extra_disamb else 0
        user_parts.insert(insert_at, peer_block)
    user = "\n\n".join(user_parts)
    return system, user


def _tool_result_text(raw: Any) -> str:
    if isinstance(raw, dict):
        return json.dumps(raw, default=str)[:8000]
    return str(raw)[:8000]


def _run_llm_loop(
    *,
    system: str,
    user: str,
    llm: Any,
    max_rounds: int,
) -> tuple[ResearchProposal | None, int, list[str]]:
    """Tool-calling loop then structured ResearchProposal invoke."""
    from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage

    tool = create_tavily_search_tool()
    tools_by_name = {getattr(tool, "name", "web_search"): tool}
    llm_tools = llm.bind_tools([tool])

    messages: list[Any] = [
        SystemMessage(content=system),
        HumanMessage(content=user),
    ]
    tool_calls_count = 0
    errors: list[str] = []

    for _ in range(max_rounds):
        ai = llm_tools.invoke(messages)
        messages.append(ai)
        tool_calls = getattr(ai, "tool_calls", None) or []
        if not tool_calls:
            break
        for tc in tool_calls:
            tool_calls_count += 1
            name = tc.get("name") if isinstance(tc, dict) else getattr(tc, "name", "")
            tc_id = tc.get("id") if isinstance(tc, dict) else getattr(tc, "id", "")
            args = tc.get("args") if isinstance(tc, dict) else getattr(tc, "args", {})
            bound = tools_by_name.get(name)
            if bound is None:
                errors.append(f"unknown tool: {name!r}")
                messages.append(
                    ToolMessage(content=f"Unknown tool: {name}", tool_call_id=tc_id or ""),
                )
                continue
            try:
                raw = bound.invoke(args)
                messages.append(
                    ToolMessage(content=_tool_result_text(raw), tool_call_id=tc_id or ""),
                )
            except Exception as exc:
                errors.append(f"tool {name!r} failed: {exc}")
                messages.append(
                    ToolMessage(content=f"Tool error: {exc}", tool_call_id=tc_id or ""),
                )

    messages.append(
        HumanMessage(
            content=(
                "Produce the final ResearchProposal now (no more tool calls). "
                "Include every target_fields entry with status found or na."
            ),
        ),
    )
    structured = llm.with_structured_output(ResearchProposal)
    proposal = structured.invoke(messages)
    if isinstance(proposal, ResearchProposal):
        return proposal, tool_calls_count, errors
    if isinstance(proposal, dict):
        return ResearchProposal.model_validate(proposal), tool_calls_count, errors
    errors.append("structured output was not a ResearchProposal")
    return None, tool_calls_count, errors


def _validate_and_build_record(
    proposal: FieldProposal,
    *,
    allowed: set[str],
    min_confidence: float,
    category: str,
    specialist_name: str,
) -> tuple[dict[str, Any] | None, str | None]:
    """Return (version body for append, error message)."""
    field = proposal.field.strip().lower()
    if field not in allowed:
        return None, f"rejected field not in target_fields: {proposal.field!r}"

    now = datetime.now(timezone.utc).isoformat()
    conf = float(proposal.confidence)
    sources = [{"url": s.strip()} for s in proposal.sources if s and str(s).strip()]
    actor = research_actor(category=category, specialist_name=specialist_name)

    if proposal.status == "found":
        value = (proposal.value or "").strip()
        if not value:
            return {
                "at": now,
                "status": "na",
                "reason": "Model returned found but value was empty",
                "actor": actor,
            }, None
        if conf < min_confidence:
            reason = proposal.reason or (
                f"Confidence {conf:.2f} below threshold {min_confidence}"
            )
            return {"at": now, "status": "na", "reason": reason, "actor": actor}, None
        if not sources:
            return {
                "at": now,
                "status": "na",
                "reason": "found status requires at least one source URL",
                "actor": actor,
            }, None
        return {
            "at": now,
            "status": "found",
            "value": value,
            "confidence": conf,
            "sources": sources,
            "actor": actor,
        }, None

    reason = (proposal.reason or "").strip()
    if not reason:
        if conf < min_confidence:
            reason = f"Confidence {conf:.2f} below threshold {min_confidence}"
        else:
            reason = "Insufficient evidence from search results"
    return {"at": now, "status": "na", "reason": reason, "actor": actor}, None


def _write_pending(
    entry: dict[str, Any] | None,
    *,
    at: str,
    last_error: str,
    started_at: str | None,
    category: str,
    specialist_name: str,
) -> dict[str, Any]:
    """Append or in-place update pending per P1-11."""
    shell = ensure_versioned_for_write(entry)
    version = current_version(shell)
    actor = research_actor(category=category, specialist_name=specialist_name)
    if version is not None and version.get("status") == "pending":
        return update_current_pending(shell, at=at, last_error=last_error)
    started = started_at or at
    body = {
        "at": at,
        "status": "pending",
        "started_at": started,
        "last_error": last_error,
        "actor": actor,
    }
    return append_version(shell, body)


def _mark_pending(
    storage: SpecialistStorage,
    person_id: str,
    fields: list[str],
    *,
    last_error: str,
    category: str,
    specialist_name: str,
) -> None:
    data = storage.load()
    records = data.setdefault("records", {})
    rec = records.setdefault(person_id, {})
    now = datetime.now(timezone.utc).isoformat()
    for fld in fields:
        existing = rec.get(fld)
        if field_has_value(existing):
            continue
        started = None
        if isinstance(existing, dict):
            if is_versioned_field(existing):
                version = current_version(existing)
                if version is not None:
                    started = str(version.get("started_at") or version.get("at") or "")
            else:
                started = str(existing.get("started_at") or "")
        rec[fld] = _write_pending(
            existing if isinstance(existing, dict) else None,
            at=now,
            last_error=last_error,
            started_at=started,
            category=category,
            specialist_name=specialist_name,
        )
    storage.save(data)


def _append_research_audit(
    data: dict[str, Any],
    *,
    category: str,
    specialist_name: str,
    person_id: str,
    fields_updated: list[str],
    tool_calls_count: int,
    errors: list[str],
    context_bind: dict[str, str] | None = None,
) -> None:
    meta = data.setdefault("meta", {})
    if not isinstance(meta, dict):
        return
    audit = meta.setdefault("research_audit", [])
    if not isinstance(audit, list):
        return
    entry: dict[str, Any] = {
        "at": datetime.now(timezone.utc).isoformat(),
        "category": category,
        "specialist": specialist_name,
        "person_id": person_id,
        "fields_updated": fields_updated,
        "tool_calls_count": tool_calls_count,
        "errors": errors,
    }
    if context_bind is not None:
        entry["context_bind"] = context_bind
    audit.append(entry)


def _pending_started_at(entry: Any) -> str | None:
    if not isinstance(entry, dict):
        return None
    if is_versioned_field(entry):
        version = current_version(entry)
        if version is None:
            return None
        return str(version.get("started_at") or version.get("at") or "") or None
    raw = entry.get("started_at")
    return str(raw) if raw else None


def _persist_field_version(
    existing: Any,
    version_body: dict[str, Any],
    *,
    category: str,
    specialist_name: str,
) -> dict[str, Any]:
    """Apply P1-11 transition rules for one field entry."""
    if field_has_value(existing) and _current_actor_kind(existing) != "operator":
        return existing if isinstance(existing, dict) else ensure_versioned_for_write(None)
    shell = ensure_versioned_for_write(existing)
    current = current_version(shell)
    new_status = version_body.get("status")
    if current is None:
        return append_version(shell, version_body)
    current_status_value = current.get("status")
    if current_status_value == "pending" and new_status == "pending":
        return update_current_pending(
            shell,
            at=str(version_body.get("at") or ""),
            last_error=str(version_body.get("last_error") or ""),
        )
    _ = category, specialist_name
    return append_version(shell, version_body)


def _persist_proposal(
    storage: SpecialistStorage,
    person_id: str,
    proposal: ResearchProposal,
    *,
    allowed: set[str],
    min_confidence: float,
    category: str,
    specialist_name: str,
) -> tuple[list[str], list[str]]:
    data = storage.load()
    records = data.setdefault("records", {})
    rec = records.setdefault(person_id, {})
    updated: list[str] = []
    errors: list[str] = []
    now = datetime.now(timezone.utc).isoformat()

    proposals_by_field = {p.field.strip().lower(): p for p in proposal.fields}
    for fld in sorted(allowed):
        existing = rec.get(fld)
        started = _pending_started_at(existing)
        fp = proposals_by_field.get(fld)
        if fp is None:
            msg = f"No proposal returned for field {fld!r}"
            errors.append(msg)
            rec[fld] = _write_pending(
                existing if isinstance(existing, dict) else None,
                at=now,
                last_error=msg,
                started_at=started,
                category=category,
                specialist_name=specialist_name,
            )
            continue
        version_body, err = _validate_and_build_record(
            fp,
            allowed=allowed,
            min_confidence=min_confidence,
            category=category,
            specialist_name=specialist_name,
        )
        if err:
            errors.append(err)
            rec[fld] = _write_pending(
                existing if isinstance(existing, dict) else None,
                at=now,
                last_error=err,
                started_at=started,
                category=category,
                specialist_name=specialist_name,
            )
            continue
        if version_body is not None:
            rec[fld] = _persist_field_version(
                existing,
                version_body,
                category=category,
                specialist_name=specialist_name,
            )
            if current_status(rec[fld]) in ("found", "na"):
                updated.append(fld)

    for fld in sorted(allowed):
        entry = rec.get(fld)
        status = current_status(entry) if isinstance(entry, dict) else "empty"
        if status in ("found", "na"):
            continue
        if status == "pending" and isinstance(entry, dict):
            version = current_version(entry)
            if version and version.get("last_error"):
                continue
        msg = f"Field {fld!r} missing after research persist"
        errors.append(msg)
        started = _pending_started_at(entry)
        rec[fld] = _write_pending(
            entry if isinstance(entry, dict) else None,
            at=now,
            last_error=msg,
            started_at=started,
            category=category,
            specialist_name=specialist_name,
        )

    storage.save(data)
    return updated, errors


def _execute_research(
    *,
    category: str,
    specialist_name: str,
    person_id: str,
    target_fields: list[str],
    context: dict[str, Any],
    storage: SpecialistStorage,
    llm: Any | None,
) -> ResearchRunResult:
    allowed_list = _normalize_fields(target_fields)
    if not allowed_list:
        return ResearchRunResult(errors=["no target_fields to research"])

    if llm is None:
        from langchain_openai import ChatOpenAI

        llm = ChatOpenAI(model=research_model(), temperature=0.0)

    system, user = build_research_prompts(
        category=category,
        specialist_name=specialist_name,
        person_id=person_id,
        target_fields=allowed_list,
        context=context,
    )
    min_conf = research_min_confidence()
    max_rounds = research_max_tool_rounds()

    proposal, tool_calls_count, loop_errors = _run_llm_loop(
        system=system,
        user=user,
        llm=llm,
        max_rounds=max_rounds,
    )
    errors = list(loop_errors)

    if proposal is None:
        _mark_pending(
            storage,
            person_id,
            allowed_list,
            last_error="; ".join(errors) or "research LLM failed",
            category=category,
            specialist_name=specialist_name,
        )
        return ResearchRunResult(errors=errors, tool_calls_count=tool_calls_count)

    updated, persist_errors = _persist_proposal(
        storage,
        person_id,
        proposal,
        allowed=set(allowed_list),
        min_confidence=min_conf,
        category=category,
        specialist_name=specialist_name,
    )
    errors.extend(persist_errors)

    data = storage.load()
    _append_research_audit(
        data,
        category=category,
        specialist_name=specialist_name,
        person_id=person_id,
        fields_updated=updated,
        tool_calls_count=tool_calls_count,
        errors=errors,
        context_bind=bind_disambiguators(context, load_mvr()),
    )
    storage.save(data)

    return ResearchRunResult(
        fields_updated=updated,
        errors=errors,
        tool_calls_count=tool_calls_count,
    )


def run_field_research(
    *,
    category: str,
    specialist_name: str,
    person_id: str,
    target_fields: list[str],
    context: dict[str, Any],
    storage: SpecialistStorage,
    llm: Any | None = None,
) -> ResearchRunResult:
    """
    Execute the LLM + Tavily tool loop and persist outcomes to specialist storage.

    On missing API keys, returns errors without running LLM (caller should leave
    fields pending). On LLM/tool failure, marks target fields pending with last_error.
    """
    if not is_research_available():
        msg = "research unavailable: OPENAI_API_KEY and/or TAVILY_API_KEY missing"
        allowed = _normalize_fields(target_fields)
        if allowed:
            _mark_pending(
                storage,
                person_id,
                allowed,
                last_error=msg,
                category=category,
                specialist_name=specialist_name,
            )
        return ResearchRunResult(errors=[msg])

    timeout = research_timeout_sec()

    def _run() -> ResearchRunResult:
        return _execute_research(
            category=category,
            specialist_name=specialist_name,
            person_id=person_id,
            target_fields=target_fields,
            context=context,
            storage=storage,
            llm=llm,
        )

    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(_run)
        try:
            return future.result(timeout=timeout)
        except FuturesTimeoutError:
            msg = f"research timed out after {timeout}s"
            allowed = _normalize_fields(target_fields)
            if allowed:
                _mark_pending(
                    storage,
                    person_id,
                    allowed,
                    last_error=msg,
                    category=category,
                    specialist_name=specialist_name,
                )
            return ResearchRunResult(errors=[msg])
