"""MCP server for external AI agents to query and ingest person data."""

from __future__ import annotations

import json
import os
from pathlib import Path

from dotenv import load_dotenv
from fastmcp import FastMCP

from graphs.core import run_query
from models.state import Person, PersonQuery
from storage.core import get_storage

mcp = FastMCP(
    "Mycelium",
    instructions=(
        "Mycelium manages AI-native CRM person data. "
        "Use query_person for lookups. Use submit_person_data to ingest missing records. "
        "All payloads are JSON."
    ),
)


def _bootstrap() -> None:
    load_dotenv()
    get_storage(
        db_path=Path(os.getenv("MYCELIUM_DB_PATH", "data/mycelium.db")),
        seed_path=Path(os.getenv("MYCELIUM_SEED_PATH", "data/seed_crm.json")),
    )


@mcp.tool
def query_person(query_json: str) -> str:
    """
    Query a person by id, email, or name.

    Input JSON example:
    {"person_key": "ada.lovelace@analytical.engine", "requested_attributes": ["age"]}
    """
    _bootstrap()
    query = PersonQuery.model_validate_json(query_json)
    response = run_query(query)
    return response.model_dump_json()


@mcp.tool
def submit_person_data(query_json: str) -> str:
    """
    Ingest or update a person using minimum viable CRM fields.

    Input JSON example:
    {
      "person_key": "new.person@example.com",
      "provided_data": {
        "id": "",
        "name": "New Person",
        "email": "new.person@example.com",
        "employer": "Example Corp"
      }
    }
    """
    _bootstrap()
    query = PersonQuery.model_validate_json(query_json)
    if query.provided_data is None:
        return json.dumps(
            {
                "error": "provided_data is required for submit_person_data",
            },
        )
    response = run_query(query)
    return response.model_dump_json()


@mcp.tool
def list_derivative_datasets() -> str:
    """List derivative dataset stubs managed by specialist agents (Phase 1)."""
    _bootstrap()
    storage = get_storage()
    datasets = storage.list_derivative_datasets()
    return json.dumps([d.model_dump() for d in datasets], indent=2)


@mcp.resource("mycelium://schema/person")
def person_schema() -> str:
    """JSON schema for core Person records."""
    return json.dumps(Person.model_json_schema(), indent=2)


def run_server() -> None:
    """Entry point for `mycelium-mcp` script."""
    _bootstrap()
    mcp.run()


if __name__ == "__main__":
    run_server()
