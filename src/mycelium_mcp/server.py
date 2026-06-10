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
from models.state import BillingPrincipal, EntityQuery, QueryResponse, SeedRecord
from network.introspection import build_network_capabilities, format_mcp_instructions
from storage.core import get_storage

mcp = FastMCP("Mycelium", instructions="")

# Seed record used for optional internal ping in health_check (no caller input).
_HEALTH_PING_ENTITY_KEY = "Nichanan Kesonpat"


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
    get_storage(
        db_path=paths.db_path,
        seed_path=paths.seed_path,
    )


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
    query = EntityQuery.model_validate(data)
    resolved_thread = thread_id if isinstance(thread_id, str) and thread_id else str(uuid.uuid4())
    return query, resolved_thread


def _serialize_response(response: QueryResponse) -> str:
    """Return QueryResponse JSON including trace_id and thread_id."""
    return response.model_dump_json(indent=2)


def _neutral_json_schema(model: type[EntityQuery] | type[QueryResponse] | type[SeedRecord]) -> dict[str, Any]:
    """Export JSON Schema with network-neutral titles for MCP schema resources."""
    schema = model.model_json_schema()
    schema["title"] = model.__name__
    if model is EntityQuery:
        schema.setdefault("description", "Lookup request: entity_key plus optional requested_attributes.")
    elif model is QueryResponse:
        schema["description"] = (
            "Query outcome: outcome (machine-readable), suggestions (near-miss retries), "
            "required_fields (MVR gaps when entity_unknown), results (attribute values), "
            "message (status narrative), debug, trace_id, thread_id."
        )
    elif model is SeedRecord:
        schema.setdefault("description", "Seed identity record (id, name, employer).")
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
                    f"entity_key={query.entity_key!r}"
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
    Query a seed record by id or name.

    Request JSON (EntityQuery fields plus optional thread_id):
    {
      "entity_key": "Nichanan Kesonpat",
      "requested_attributes": ["email"],
      "thread_id": "optional-conversation-id",
      "quote_id": "q_abc (retry after quote_required / payment_required)"
    }

    Response JSON includes outcome, suggestions (when near-miss), required_fields
    (when entity_unknown), quote (when quote_required or payment_required), results,
    message, debug, trace_id, and thread_id.
    On outcome entity_key_unresolved, re-query with a suggestions[].entity_key.
    On outcome entity_unknown, gather required_fields from MVR policy (see
    describe_network) before re-querying — no research until bound.
    When metering.payment.enabled: quote_required → pay_quote → retry with quote_id.
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
    internal ping query against seed data. Always returns parseable JSON (never
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
            ping_raw = _execute_mcp_query(
                json.dumps({"entity_key": _HEALTH_PING_ENTITY_KEY}),
            )
            ping = json.loads(ping_raw)
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


@mcp.resource("mycelium://schema/seed-record")
def seed_record_schema() -> str:
    """JSON schema for core SeedRecord identity fields."""
    return json.dumps(_neutral_json_schema(SeedRecord), indent=2)


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
