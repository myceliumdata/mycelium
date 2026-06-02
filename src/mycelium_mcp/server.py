"""Mycelium MCP server for external AI agents (package: ``mycelium_mcp``)."""

from __future__ import annotations

import json
import os
import uuid
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastmcp import FastMCP

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
        "Use submit_person_data to add a missing person (provided_data with name and employer). "
        "All payloads are JSON. "
        "To get a direct link to the trace in LangSmith, use the get_langsmith_trace_url helper "
        "from the mycelium package (or implement equivalent from utils.langsmith) with the trace_id."
    ),
)


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
    response = run_query(query, thread_id=thread_id)
    return _serialize_response(response)


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
def submit_person_data(query_json: str) -> str:
    """
    Add a new core person using minimum viable fields in provided_data.

    Note: even though this is an "add", the wire format is still a full
    PersonQuery (with person_key + provided_data). This is why the
    graph trace Input always contains a "query" object, even for
    pure ingestion runs. The provided_data presence triggers the
    enrich/validator path inside the supervisor.

    Request JSON example:
    {
      "person_key": "new.person@example.com",
      "thread_id": "optional-conversation-id",
      "provided_data": {
        "id": "",
        "name": "New Person",
        "employer": "Example Corp"
      }
    }

    Response JSON includes results, message, debug, trace_id, and thread_id.
    """
    _bootstrap()
    query, thread_id = _parse_query_payload(query_json)
    if query.provided_data is None:
        return json.dumps(
            {
                "error": "provided_data is required for submit_person_data",
            },
            indent=2,
        )
    response = run_query(query, thread_id=thread_id)
    return _serialize_response(response)


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
