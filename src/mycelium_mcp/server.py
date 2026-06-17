"""Mycelium MCP server for external AI agents (package: ``mycelium_mcp``)."""

from __future__ import annotations

import json
import os
import uuid
from typing import Any

from dotenv import load_dotenv
from fastmcp import FastMCP

# Force the sync checkpointer path for the long-running MCP stdio server.
# This avoids event-loop and aiosqlite connection contention that can occur
# with repeated asyncio.run() calls against the async checkpointer
# (used primarily for LangGraph Studio / ASGI).
os.environ["MYCELIUM_USE_SYNC_CHECKPOINTER"] = "1"

from agents.runtime import refresh_runtime_from_disk
from graphs.core import run_query
from models.state import BillingPrincipal, EntityQuery, IdentityRecord, QueryResponse
from network.introspection import build_network_capabilities, format_mcp_instructions
from storage.core import get_storage

mcp = FastMCP("Mycelium", instructions="")

# Health ping: two-step target resolve for a known CRM seed row.
_HEALTH_PING_LOOKUP = {"name": "Nichanan Kesonpat", "employer": "1k(x)"}


def _network_health_info() -> dict[str, str | None]:
    from network.paths import NO_NETWORK_CONFIGURED_MSG, network_metadata

    try:
        return network_metadata()
    except Exception:
        env_name = os.environ.get("MYCELIUM_NETWORK", "").strip()
        return {
            "network_root": None,
            "network_name": env_name or None,
            "network_display_name": None,
            "network_configure_hint": NO_NETWORK_CONFIGURED_MSG,
        }


def _apply_mcp_instructions() -> None:
    try:
        capabilities = build_network_capabilities()
    except Exception:
        capabilities = {
            "display_name": None,
            "network_name": None,
        }
    instructions = format_mcp_instructions(capabilities)
    if getattr(mcp, "instructions", None) != instructions:
        mcp.instructions = instructions


def _bootstrap() -> None:
    load_dotenv()
    from network.paths import NetworkPaths, apply_network_paths, resolve_network_root

    paths = NetworkPaths.from_root(resolve_network_root())
    apply_network_paths(paths)
    _apply_mcp_instructions()
    get_storage(db_path=paths.db_path)


def _parse_query_payload(query_json: str) -> tuple[EntityQuery, str]:
    """
    Parse MCP query JSON into an EntityQuery and thread id.

    Accepts an optional top-level ``thread_id`` (not part of EntityQuery). When omitted,
    a new UUID is generated for this invocation.
    """
    data: Any = json.loads(query_json)
    if not isinstance(data, dict):
        msg = "query JSON must be an object"
        raise ValueError(msg)

    thread_id = data.pop("thread_id", None)
    if (data.get("entity_key") or data.get("binding")) and not (
        data.get("id") or data.get("lookup") or data.get("delivery_id")
    ):
        msg = (
            "entity_key/binding removed from public API (MVR redesign M9). "
            "Use id or lookup on step 1, or delivery_id on step 2."
        )
        raise ValueError(msg)
    query = EntityQuery.model_validate(data)
    resolved_thread = thread_id if isinstance(thread_id, str) and thread_id else str(uuid.uuid4())
    return query, resolved_thread


def _serialize_response(response: QueryResponse) -> str:
    """Return QueryResponse JSON including trace_id and thread_id."""
    return response.public_json()


def _neutral_json_schema(model: type[EntityQuery] | type[QueryResponse] | type[IdentityRecord]) -> dict[str, Any]:
    """Export JSON Schema with network-neutral titles for MCP schema resources."""
    schema = model.model_json_schema()
    schema["title"] = model.__name__
    if model is EntityQuery:
        schema["description"] = (
            "Target two-step protocol: step 1 — id or lookup (AND), optional "
            "requested_attributes, provenance, confirm_new_entity (after "
            "lookup_suggested). Multi-grain networks infer grain from lookup "
            "key shape (disjoint bind_fields per grain). Baseball: "
            "{player, team} → player grain; {team} → team grain. "
            "Step 2 — delivery_id plus optional quote_id. "
            "Public clients must not send entity_key or binding (removed M9)."
        )
        props = schema.setdefault("properties", {})
        for legacy_field in ("entity_key", "binding"):
            field_schema = props.get(legacy_field)
            if isinstance(field_schema, dict):
                desc = field_schema.get("description") or ""
                if "Deprecated" not in desc and "Internal" not in desc:
                    field_schema["description"] = (
                        f"Internal/tests only — not accepted via MCP/CLI/admin (M9). {desc}"
                    )
    elif model is QueryResponse:
        schema["description"] = (
            "Query outcome: outcome (machine-readable — lookup_resolved, "
            "lookup_incomplete, lookup_suggested, quote_required, found, assembled, …), "
            "total_matches and delivery (step-1 only, when applicable), suggestions "
            "(same-name or fuzzy near-miss retries; merge suggestions[].suggested_lookup "
            "into step-1 lookup; suggestions may include grain when tagged), "
            "required_fields (missing MVR bind fields on lookup_incomplete), results "
            "(attribute values), message (status "
            "narrative), provenance (version history when request provenance=true and "
            "present), quote (when quote_required/payment_required), debug, trace_id, "
            "thread_id. Optional fields are omitted when not applicable — not emitted "
            "as null."
        )
    elif model is IdentityRecord:
        schema.setdefault("description", "Registry identity record (id + bind_values map).")
    return schema


def _execute_mcp_query(query_json: str) -> str:
    """Run a query and serialize QueryResponse JSON (no bootstrap or runtime refresh)."""
    query, thread_id = _parse_query_payload(query_json)
    try:
        response = run_query(query, thread_id=thread_id)
        return _serialize_response(response)
    except Exception as exc:
        # Attempt to recover the graph/checkpointer so subsequent tool calls
        # in this long-lived MCP server process can succeed. A single bad
        # query (e.g. checkpoint contention, serialization edge case) should
        # not permanently kill the server for Claude Desktop or other clients.
        try:
            from graphs.core import reset_core_graph
            reset_core_graph()
        except Exception:
            pass
        # Return a valid QueryResponse-shaped JSON so the MCP protocol
        # doesn't see a hard tool failure.
        return json.dumps(
            {
                "results": [],
                "message": f"Query failed internally: {exc}",
                "debug": (
                    f"outcome='error'; error_type={type(exc).__name__}; "
                    f"delivery_id={query.delivery_id!r}; id={query.id!r}"
                ),
                "outcome": "error",
                "suggestions": [],
                "trace_id": None,
                "thread_id": thread_id,
            },
            indent=2,
        )


def _run_mcp_query(query_json: str) -> str:
    _bootstrap()
    refresh_runtime_from_disk()
    return _execute_mcp_query(query_json)


def _routing_payload() -> dict[str, Any]:
    """Build specialist routing dict (internal; health_check only)."""
    from agents.registry import get_agent_registry

    reg = get_agent_registry()
    specialists = [
        {
            "name": agent["name"],
            "category": agent.get("category"),
            "is_generated": agent.get("is_generated"),
            "storage_path": agent.get("storage_path"),
        }
        for agent in reg.list_agents()
    ]
    return {
        "message": (
            "Specialist agent routing is coordinated by the supervisor "
            "via the Agent Registry (Phase 2)."
        ),
        "specialists": specialists,
    }


@mcp.tool
def query_entity(query_json: str) -> str:
    """
    Query entities via the target two-step protocol.

    Step 1 — resolve (returns delivery_id, empty results[]):
    {
      "lookup": {"employer": "645 Ventures"},
      "requested_attributes": ["email"],
      "provenance": false,
      "thread_id": "optional-conversation-id"
    }
    Or: {"id": "<registry-uuid>"} with optional attrs on step 1 only.

    Step 2 — deliver (full results[]):
    {
      "delivery_id": "d_…",
      "quote_id": "q_… (when metering accepted)"
    }

    Response JSON includes outcome (lookup_resolved, lookup_incomplete, lookup_suggested,
    quote_required, found, assembled, …), delivery, quote, total_matches, suggestions
    (with suggested_lookup retry maps), required_fields, results, message, provenance,
    debug, trace_id, thread_id. On lookup_suggested, merge suggestions[].suggested_lookup
    into step-1 lookup (or use suggestions[].id). When metering.payment.enabled:
    quote_required → pay_quote → step 2 with quote_id.
    """
    return _run_mcp_query(query_json)


@mcp.tool
def pay_quote(payment_json: str) -> str:
    """
    Settle a metering quote before query_entity can accept it (Slice 11).

    Request JSON:
    {
      "quote_id": "q_abc",
      "proof": "optional (x402:test:… for x402 stub)",
      "principal": {"kind": "tenant", "id": "acme"}
    }

    Returns JSON: {"status": "paid", "receipt": {...}} or {"status": "error", "message": "..."}.
    """
    _bootstrap()
    refresh_runtime_from_disk()
    try:
        data: Any = json.loads(payment_json)
        if not isinstance(data, dict):
            msg = "payment JSON must be an object"
            raise ValueError(msg)
        quote_id = data.get("quote_id")
        if not isinstance(quote_id, str) or not quote_id.strip():
            msg = "quote_id is required"
            raise ValueError(msg)
        proof = data.get("proof")
        if proof is not None and not isinstance(proof, str):
            msg = "proof must be a string when provided"
            raise ValueError(msg)
        principal_raw = data.get("principal")
        principal = (
            BillingPrincipal.model_validate(principal_raw)
            if isinstance(principal_raw, dict)
            else None
        )
        from network.payment import PaymentError, settle_quote

        receipt = settle_quote(
            quote_id.strip(),
            proof=proof,
            principal=principal,
        )
        return json.dumps(
            {"status": "paid", "receipt": receipt.model_dump()},
            indent=2,
        )
    except (PaymentError, ValueError) as exc:
        return json.dumps({"status": "error", "message": str(exc)}, indent=2)
    except Exception as exc:
        return json.dumps(
            {"status": "error", "message": f"pay_quote failed: {exc}"},
            indent=2,
        )


@mcp.tool
def describe_network() -> str:
    """
    Return the author guide, ontology summary, and usage policy for this network.

    Call at connect time before querying. Includes full ``guide.md`` text when
    present, category descriptions/examples from ``categories.json``, and
    framework policy strings for extensibility and out-of-scope handling.
    """
    _bootstrap()
    refresh_runtime_from_disk()
    return json.dumps(build_network_capabilities(), indent=2)


def _health_check_status(check_result: str) -> bool:
    """Return True when a single check result counts as healthy."""
    return check_result == "ok"


@mcp.tool
def health_check() -> str:
    """
    Lightweight diagnostics for the long-running MCP server.

    Verifies storage bootstrap, graph singleton, internal routing payload, and an
    internal ping query against registry data. Always returns parseable JSON (never
    raises to the MCP client).
    """
    try:
        _bootstrap()
        refresh_runtime_from_disk()
        checks: dict[str, str] = {}

        try:
            get_storage()
            checks["storage"] = "ok"
        except Exception as exc:
            checks["storage"] = f"error: {exc}"

        try:
            from graphs.core import get_core_graph

            get_core_graph()
            checks["graph"] = "ok"
        except Exception as exc:
            checks["graph"] = f"error: {exc}"

        try:
            routing = _routing_payload()
            if isinstance(routing, dict) and routing.get("message"):
                checks["lightweight_tool"] = "ok"
            else:
                checks["lightweight_tool"] = "degraded"
        except Exception as exc:
            checks["lightweight_tool"] = f"error: {exc}"

        try:
            ping_step1_raw = _execute_mcp_query(
                json.dumps({"lookup": _HEALTH_PING_LOOKUP}),
            )
            ping_step1 = json.loads(ping_step1_raw)
            delivery = ping_step1.get("delivery") or {}
            delivery_id = delivery.get("delivery_id") if isinstance(delivery, dict) else None
            if ping_step1.get("outcome") == "lookup_resolved" and delivery_id:
                ping_raw = _execute_mcp_query(json.dumps({"delivery_id": delivery_id}))
                ping = json.loads(ping_raw)
            else:
                ping = ping_step1
            if ping.get("results"):
                checks["ping_query"] = "ok"
            elif "Query failed internally" in str(ping.get("message", "")):
                checks["ping_query"] = "degraded"
            else:
                checks["ping_query"] = "degraded"
        except Exception as exc:
            checks["ping_query"] = f"error: {exc}"

        all_ok = all(_health_check_status(v) for v in checks.values())
        sync_forced = os.environ.get("MYCELIUM_USE_SYNC_CHECKPOINTER") == "1"

        network_info = _network_health_info()
        info = {
            "checkpointer": (
                "sync (forced for MCP)"
                if sync_forced
                else f"env={os.environ.get('MYCELIUM_USE_SYNC_CHECKPOINTER', 'unset')!r}"
            ),
            "network_root": network_info["network_root"],
            "network_name": network_info["network_name"],
            "network_display_name": network_info["network_display_name"],
            "recovery_wrapper": "active",
            "server": "mycelium-mcp",
        }
        if network_info.get("network_configure_hint"):
            info["network_configure_hint"] = network_info["network_configure_hint"]
        payload = {
            "status": "ok" if all_ok else "degraded",
            "checks": checks,
            "info": info,
            "message": (
                "Mycelium MCP server is responsive."
                if all_ok
                else "Mycelium MCP server is responsive but one or more checks are degraded."
            ),
        }
        return json.dumps(payload, indent=2)
    except Exception as exc:
        network_info = _network_health_info()
        info = {
            "checkpointer": "sync (forced for MCP)"
            if os.environ.get("MYCELIUM_USE_SYNC_CHECKPOINTER") == "1"
            else "unknown",
            "network_root": network_info["network_root"],
            "network_name": network_info["network_name"],
            "network_display_name": network_info["network_display_name"],
            "recovery_wrapper": "active",
            "server": "mycelium-mcp",
        }
        if network_info.get("network_configure_hint"):
            info["network_configure_hint"] = network_info["network_configure_hint"]
        return json.dumps(
            {
                "status": "degraded",
                "checks": {},
                "info": info,
                "message": f"health_check encountered an error: {exc}",
            },
            indent=2,
        )


@mcp.resource("mycelium://schema/identity-record")
def identity_record_schema() -> str:
    """JSON schema for core IdentityRecord fields."""
    return json.dumps(_neutral_json_schema(IdentityRecord), indent=2)


@mcp.resource("mycelium://schema/entity-query")
def entity_query_schema() -> str:
    """JSON schema for EntityQuery (public lookup request)."""
    return json.dumps(_neutral_json_schema(EntityQuery), indent=2)


@mcp.resource("mycelium://schema/query-response")
def query_response_schema() -> str:
    """JSON schema for QueryResponse (includes trace_id and thread_id)."""
    return json.dumps(_neutral_json_schema(QueryResponse), indent=2)


def run_server() -> None:
    """Entry point for `mycelium-mcp` script."""
    _bootstrap()
    mcp.run()


if __name__ == "__main__":
    run_server()
