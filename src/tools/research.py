"""Category-agnostic specialist field research (LLM + web_search).

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

from network.mvr import MvrPolicy, load_mvr
from network.env_util import env_int
from tools.web_search import (
    UnknownSearchProviderError,
    create_web_search_tool,
    is_web_search_available,
    search_provider,
)
from utils.llm_models import research_model

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


def is_research_available() -> bool:
    """True when both OpenAI and the active search provider key are configured."""
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


def _research_actor(*, category: str, specialist_name: str) -> dict[str, str]:
    return {
        "kind": "research",
        "category": category,
        "specialist": specialist_name,
    }


def _looks_like_context_field_map(records: dict[str, Any]) -> bool:
    """True when dict keys are field names mapping to normalized context snapshots."""
    if not records:
        return False
    for value in records.values():
        if not isinstance(value, dict):
            return False
        if "status" not in value or "value" not in value:
            return False
    return True


def _peer_category_row(records: dict[str, Any], entity_id: str) -> dict[str, Any] | None:
    """Field snapshots for entity_id, or a flattened row already scoped to one entity."""
    nested = records.get(entity_id)
    if isinstance(nested, dict) and nested and _looks_like_context_field_map(nested):
        return nested
    if _looks_like_context_field_map(records):
        return records
    return None


def _trim_peer_fields(row: dict[str, Any]) -> dict[str, Any]:
    """Keep found peer fields only (omit pending/na from prominent block)."""
    return {
        key: value
        for key, value in row.items()
        if isinstance(value, dict)
        and value.get("status") == "found"
        and value.get("value") not in (None, "")
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
            if not isinstance(record, dict):
                continue
            value = str(record.get("value") or "").strip()
            if not value:
                continue
            sources = record.get("sources") or []
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
        if not isinstance(entry, dict):
            continue
        operator = entry.get("operator")
        if not isinstance(operator, dict) or not operator.get("set"):
            continue
        overrides.append(
            {
                "field": field_name,
                "value": operator.get("value"),
                "at": operator.get("at"),
                "note": operator.get("note"),
            },
        )
    return overrides


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
    leading: list[str] = []
    if extra_disamb:
        disambiguation = env.get_template("research/_disambiguation.j2").render(**template_vars).strip()
        leading.append(disambiguation)
    if operator_overrides:
        operator_block = env.get_template("research/_operator_deference.j2").render(
            **template_vars,
        ).strip()
        leading.append(operator_block)
    if peer_display:
        leading.append(format_peer_context_block(peer_display))

    body: list[str] = []
    if fragment:
        body.append(f"Category guidance:\n{fragment}")
    body.append("Research the following person for the listed target_fields only.")
    body.append(json.dumps(user_payload, indent=2, default=str))
    user = "\n\n".join([*leading, *body])
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

    tool = create_web_search_tool()
    tool_name = getattr(tool, "name", "web_search")
    tools_by_name = {
        tool_name: tool,
        "web_search": tool,
        "tavily_search": tool,
        "exa_search_results_json": tool,
        "brave_search": tool,
    }
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
    actor = _research_actor(category=category, specialist_name=specialist_name)

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


def _mark_pending(
    category: str,
    specialist_name: str,
    person_id: str,
    fields: list[str],
    *,
    last_error: str,
) -> None:
    from agents.specialists.protocol import dispatch_mark_pending

    dispatch_mark_pending(
        category,
        specialist_name,
        person_id,
        fields,
        last_error=last_error,
    )


def _execute_research(
    *,
    category: str,
    specialist_name: str,
    person_id: str,
    target_fields: list[str],
    context: dict[str, Any],
    llm: Any | None,
) -> ResearchRunResult:
    from agents.specialists.protocol import (
        dispatch_append_research_audit,
        dispatch_persist_research,
    )

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
            category,
            specialist_name,
            person_id,
            allowed_list,
            last_error="; ".join(errors) or "research LLM failed",
        )
        return ResearchRunResult(errors=errors, tool_calls_count=tool_calls_count)

    updated, persist_errors = dispatch_persist_research(
        category,
        specialist_name,
        person_id,
        proposal,
        allowed=set(allowed_list),
        min_confidence=min_conf,
        validate_and_build=_validate_and_build_record,
    )
    errors.extend(persist_errors)

    dispatch_append_research_audit(
        category,
        specialist_name,
        person_id,
        fields_updated=updated,
        tool_calls_count=tool_calls_count,
        errors=errors,
        context_bind=bind_disambiguators(context, load_mvr()),
    )

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
    llm: Any | None = None,
) -> ResearchRunResult:
    """
    Execute the LLM + web_search tool loop and persist outcomes to specialist storage.

    On missing API keys, returns errors without running LLM (caller should leave
    fields pending). On LLM/tool failure, marks target fields pending with last_error.
    """
    if not is_research_available():
        try:
            provider_label = search_provider()
        except UnknownSearchProviderError as exc:
            provider_label = str(exc)
        msg = (
            "research unavailable: OPENAI_API_KEY and/or search API key missing "
            f"(SEARCH_PROVIDER={provider_label})"
        )
        allowed = _normalize_fields(target_fields)
        if allowed:
            _mark_pending(
                category,
                specialist_name,
                person_id,
                allowed,
                last_error=msg,
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
                    category,
                    specialist_name,
                    person_id,
                    allowed,
                    last_error=msg,
                )
            return ResearchRunResult(errors=[msg])
