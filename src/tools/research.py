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

from agents.specialists.base import SpecialistStorage
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


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def research_min_confidence() -> float:
    return _env_float("MYCELIUM_RESEARCH_MIN_CONFIDENCE", 0.6)


def research_max_tool_rounds() -> int:
    return _env_int("MYCELIUM_RESEARCH_MAX_TOOL_ROUNDS", 3)


def research_timeout_sec() -> int:
    return _env_int("MYCELIUM_RESEARCH_TIMEOUT_SEC", 120)


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


def _bind_prompt_vars(context: dict[str, Any]) -> tuple[str, str, bool]:
    """Extract bind name/employer for research prompt templates."""
    bind = context.get("bind")
    if not isinstance(bind, dict):
        return "", "", False
    name = str(bind.get("name") or "").strip()
    employer = str(bind.get("employer") or "").strip()
    return name, employer, bool(employer)


def _context_bind_snapshot(context: dict[str, Any]) -> dict[str, str] | None:
    """Name + employer only for research audit entries."""
    bind = context.get("bind")
    if not isinstance(bind, dict):
        return None
    name, employer, has_employer = _bind_prompt_vars(context)
    return {"name": name, "employer": employer if has_employer else ""}


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
    bind_name, bind_employer, bind_has_employer = _bind_prompt_vars(context)
    bind_kwargs = {
        "bind_name": bind_name,
        "bind_employer": bind_employer,
        "bind_has_employer": bind_has_employer,
    }

    system_tpl = env.get_template("research/_system.j2")
    system = system_tpl.render(
        category=category,
        specialist_name=specialist_name,
        min_confidence=min_conf,
        **bind_kwargs,
    )

    fragment_name = f"research/{category.strip().lower()}.md.j2"
    try:
        fragment = env.get_template(fragment_name).render(**bind_kwargs).strip()
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
    if bind_has_employer:
        disambiguation = env.get_template("research/_disambiguation.j2").render(**bind_kwargs).strip()
        user_parts.insert(0, disambiguation)
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
) -> tuple[dict[str, Any] | None, str | None]:
    """Return (storage record, error message)."""
    field = proposal.field.strip().lower()
    if field not in allowed:
        return None, f"rejected field not in target_fields: {proposal.field!r}"

    now = datetime.now(timezone.utc).isoformat()
    conf = float(proposal.confidence)
    sources = [s.strip() for s in proposal.sources if s and str(s).strip()]

    if proposal.status == "found":
        value = (proposal.value or "").strip()
        if not value:
            return {
                "status": "na",
                "reason": "Model returned found but value was empty",
                "researched_at": now,
            }, None
        if conf < min_confidence:
            reason = proposal.reason or (
                f"Confidence {conf:.2f} below threshold {min_confidence}"
            )
            return {"status": "na", "reason": reason, "researched_at": now}, None
        if not sources:
            return {
                "status": "na",
                "reason": "found status requires at least one source URL",
                "researched_at": now,
            }, None
        return {
            "status": "found",
            "value": value,
            "confidence": conf,
            "sources": sources,
            "researched_at": now,
        }, None

    reason = (proposal.reason or "").strip()
    if not reason:
        if conf < min_confidence:
            reason = f"Confidence {conf:.2f} below threshold {min_confidence}"
        else:
            reason = "Insufficient evidence from search results"
    return {"status": "na", "reason": reason, "researched_at": now}, None


def _mark_pending(
    storage: SpecialistStorage,
    person_id: str,
    fields: list[str],
    *,
    last_error: str,
) -> None:
    data = storage.load()
    records = data.setdefault("records", {})
    rec = records.setdefault(person_id, {})
    now = datetime.now(timezone.utc).isoformat()
    for fld in fields:
        existing = rec.get(fld)
        if isinstance(existing, dict) and existing.get("status") == "found":
            continue
        rec[fld] = {
            "status": "pending",
            "started_at": existing.get("started_at", now) if isinstance(existing, dict) else now,
            "last_error": last_error,
        }
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


def _pending_record(
    *,
    last_error: str,
    started_at: str | None = None,
) -> dict[str, Any]:
    now = datetime.now(timezone.utc).isoformat()
    return {
        "status": "pending",
        "started_at": started_at or now,
        "last_error": last_error,
    }


def _persist_proposal(
    storage: SpecialistStorage,
    person_id: str,
    proposal: ResearchProposal,
    *,
    allowed: set[str],
    min_confidence: float,
) -> tuple[list[str], list[str]]:
    data = storage.load()
    records = data.setdefault("records", {})
    rec = records.setdefault(person_id, {})
    updated: list[str] = []
    errors: list[str] = []

    proposals_by_field = {p.field.strip().lower(): p for p in proposal.fields}
    for fld in sorted(allowed):
        existing = rec.get(fld)
        started = (
            existing.get("started_at")
            if isinstance(existing, dict)
            else None
        )
        fp = proposals_by_field.get(fld)
        if fp is None:
            msg = f"No proposal returned for field {fld!r}"
            errors.append(msg)
            rec[fld] = _pending_record(last_error=msg, started_at=started)
            continue
        record, err = _validate_and_build_record(
            fp, allowed=allowed, min_confidence=min_confidence,
        )
        if err:
            errors.append(err)
            rec[fld] = _pending_record(
                last_error=err,
                started_at=started,
            )
            continue
        if record is not None:
            rec[fld] = record
            updated.append(fld)

    for fld in sorted(allowed):
        entry = rec.get(fld)
        if isinstance(entry, dict) and entry.get("status") in ("found", "na"):
            continue
        if isinstance(entry, dict) and entry.get("status") == "pending":
            if entry.get("last_error"):
                continue
        msg = f"Field {fld!r} missing after research persist"
        errors.append(msg)
        started = entry.get("started_at") if isinstance(entry, dict) else None
        rec[fld] = _pending_record(last_error=msg, started_at=started)

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
        )
        return ResearchRunResult(errors=errors, tool_calls_count=tool_calls_count)

    updated, persist_errors = _persist_proposal(
        storage,
        person_id,
        proposal,
        allowed=set(allowed_list),
        min_confidence=min_conf,
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
        context_bind=_context_bind_snapshot(context),
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
            _mark_pending(storage, person_id, allowed, last_error=msg)
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
                _mark_pending(storage, person_id, allowed, last_error=msg)
            return ResearchRunResult(errors=[msg])
