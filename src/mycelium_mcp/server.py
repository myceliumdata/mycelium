"""Mycelium MCP server for external AI agents (package: ``mycelium_mcp``)."""

from __future__ import annotations

import json
import os
import uuid
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastmcp import FastMCP

# Force the sync checkpointer path for the long-running MCP stdio server.
# This avoids event-loop and aiosqlite connection contention that can occur
# with repeated asyncio.run() calls against the async checkpointer
# (used primarily for LangGraph Studio / ASGI).
os.environ["MYCELIUM_USE_SYNC_CHECKPOINTER"] = "1"

from graphs.core import run_query
from models.state import Person, PersonQuery, PersonResponse
from storage.core import get_storage

mcp = FastMCP(
    "Mycelium",
    instructions=(
        "Mycelium manages AI-native CRM person data (core fields: id, name, employer). "
        "Use query_person for lookups. Responses are PersonResponse JSON with results, "
        "message, debug, trace_id (LangSmith when tracing is on), and thread_id. "
        "Optional thread_id in the request JSON is echoed in the response. "
        "Non-core attribute requests return core results plus a researching narrative in message. "
        "All payloads are JSON. "
        "Use health_check() to verify the server is responsive and to inspect internal stabilization "
        "(sync checkpointer, automatic recovery after query issues). "
        "To get a direct link to the trace in LangSmith, use the get_langsmith_trace_url helper "
        "from the mycelium package (or implement equivalent from utils.langsmith) with the trace_id."
    ),
)

# Seed person used for optional internal ping in health_check (no caller input).
_HEALTH_PING_PERSON_KEY = "Nichanan Kesonpat"


def _bootstrap() -> None:
    load_dotenv()
    get_storage(
        db_path=Path(os.getenv("MYCELIUM_DB_PATH", "data/mycelium.db")),
        seed_path=Path(os.getenv("MYCELIUM_SEED_PATH", "data/seed_crm.json")),
    )


def _parse_query_payload(query_json: str) -> tuple[PersonQuery, str]:
    """
    Parse MCP query JSON into a PersonQuery and thread id.

    Accepts an optional top-level ``thread_id`` (not part of PersonQuery). When omitted,
    a new UUID is generated for this invocation.
    """
    data: Any = json.loads(query_json)
    if not isinstance(data, dict):
        msg = "query JSON must be an object"
        raise ValueError(msg)

    thread_id = data.pop("thread_id", None)
    query = PersonQuery.model_validate(data)
    resolved_thread = thread_id if isinstance(thread_id, str) and thread_id else str(uuid.uuid4())
    return query, resolved_thread


def _serialize_response(response: PersonResponse) -> str:
    """Return PersonResponse JSON including trace_id and thread_id."""
    return response.model_dump_json(indent=2)


def _run_mcp_query(query_json: str) -> str:
    _bootstrap()
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
        # Return a valid PersonResponse-shaped JSON so the MCP protocol
        # doesn't see a hard tool failure.
        return json.dumps(
            {
                "results": [],
                "message": f"Query failed internally: {exc}",
                "debug": f"error_type={type(exc).__name__}; person_key={query.person_key!r}",
                "trace_id": None,
                "thread_id": thread_id,
            },
            indent=2,
        )


@mcp.tool
def query_person(query_json: str) -> str:
    """
    Query a person by id or name.

    Request JSON (PersonQuery fields plus optional thread_id):
    {
      "person_key": "Nichanan Kesonpat",
      "requested_attributes": ["email"],
      "thread_id": "optional-conversation-id"
    }

    Response JSON includes results, message, debug, trace_id, and thread_id.
    """
    return _run_mcp_query(query_json)


@mcp.tool
def list_specialist_routing() -> str:
    """Phase 1 stub: lists specialist routing status (no persisted specialist registry)."""
    _bootstrap()
    return json.dumps(
        {
            "message": (
                "Specialist agent routing is coordinated by the supervisor. "
                "Phase 1 does not persist a specialist registry in core storage."
            ),
            "datasets": [],
        },
        indent=2,
    )


def _health_check_status(check_result: str) -> bool:
    """Return True when a single check result counts as healthy."""
    return check_result == "ok"


@mcp.tool
def health_check() -> str:
    """
    Lightweight diagnostics for the long-running MCP server.

    Verifies storage bootstrap, graph singleton, list_specialist_routing, and an
    internal ping query against seed data. Always returns parseable JSON (never
    raises to the MCP client).
    """
    try:
        _bootstrap()
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
            routing_raw = list_specialist_routing()
            routing = json.loads(routing_raw)
            if isinstance(routing, dict) and routing.get("message"):
                checks["lightweight_tool"] = "ok"
            else:
                checks["lightweight_tool"] = "degraded"
        except Exception as exc:
            checks["lightweight_tool"] = f"error: {exc}"

        try:
            ping_raw = _run_mcp_query(
                json.dumps({"person_key": _HEALTH_PING_PERSON_KEY}),
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

        payload = {
            "status": "ok" if all_ok else "degraded",
            "checks": checks,
            "info": {
                "checkpointer": (
                    "sync (forced for MCP)"
                    if sync_forced
                    else f"env={os.environ.get('MYCELIUM_USE_SYNC_CHECKPOINTER', 'unset')!r}"
                ),
                "recovery_wrapper": "active",
                "server": "mycelium-mcp",
            },
            "message": (
                "Mycelium MCP server is responsive."
                if all_ok
                else "Mycelium MCP server is responsive but one or more checks are degraded."
            ),
        }
        return json.dumps(payload, indent=2)
    except Exception as exc:
        return json.dumps(
            {
                "status": "degraded",
                "checks": {},
                "info": {
                    "checkpointer": "sync (forced for MCP)"
                    if os.environ.get("MYCELIUM_USE_SYNC_CHECKPOINTER") == "1"
                    else "unknown",
                    "recovery_wrapper": "active",
                    "server": "mycelium-mcp",
                },
                "message": f"health_check encountered an error: {exc}",
            },
            indent=2,
        )


@mcp.resource("mycelium://schema/person")
def person_schema() -> str:
    """JSON schema for core Person records."""
    return json.dumps(Person.model_json_schema(), indent=2)


@mcp.resource("mycelium://schema/person-response")
def person_response_schema() -> str:
    """JSON schema for PersonResponse (includes trace_id and thread_id)."""
    return json.dumps(PersonResponse.model_json_schema(), indent=2)


def run_server() -> None:
    """Entry point for `mycelium-mcp` script."""
    _bootstrap()
    mcp.run()


if __name__ == "__main__":
    run_server()
