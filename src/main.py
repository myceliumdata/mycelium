"""CLI for local testing of the Mycelium core graph."""

from __future__ import annotations

import argparse
import sys
import uuid
from pathlib import Path

from dotenv import load_dotenv
from rich.console import Console
from rich.json import JSON

from graphs.core import reset_core_graph, run_query
from models.state import Person, PersonQuery, PersonResponse
from storage.core import get_storage, reset_storage
from utils.langsmith import get_langsmith_trace_url

console = Console()

_THREAD_ID_HELP = (
    "LangGraph conversation thread id (echoed in response.thread_id). "
    "Defaults to a new UUID per invocation."
)


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Mycelium core graph CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    query_cmd = sub.add_parser("query", help="Query a person (JSON response)")
    query_cmd.add_argument("--person-key", required=True, help="Id, email, or name")
    query_cmd.add_argument(
        "--attributes",
        nargs="*",
        default=[],
        help="Non-core attributes (core record returned; message describes ongoing research)",
    )
    query_cmd.add_argument(
        "--thread-id",
        default=None,
        metavar="ID",
        help=_THREAD_ID_HELP,
    )

    ingest_cmd = sub.add_parser("ingest", help="Ingest person with provided JSON file or inline. (Internally still uses a PersonQuery with provided_data set; this is why traces always show a 'query' even for adds.)")
    ingest_cmd.add_argument("--person-key", required=True)
    ingest_cmd.add_argument(
        "--data",
        required=True,
        help="Path to JSON file or inline JSON with Person fields",
    )
    ingest_cmd.add_argument(
        "--thread-id",
        default=None,
        metavar="ID",
        help=_THREAD_ID_HELP,
    )

    seed_cmd = sub.add_parser("seed", help="Reload seed CRM data into SQLite")
    seed_cmd.add_argument(
        "--seed-path",
        default="data/seed_crm.json",
        help="Path to seed JSON file",
    )

    return parser.parse_args(argv)


def _resolve_thread_id(cli_thread_id: str | None) -> str:
    """Use caller-supplied thread id or generate one for this invocation."""
    return cli_thread_id if cli_thread_id else str(uuid.uuid4())


def _print_response(response: PersonResponse) -> None:
    """Print full PersonResponse JSON including trace_id and thread_id.
    If trace_id is present, also print a direct LangSmith trace URL using the helper.
    """
    console.print(JSON(response.model_dump_json(indent=2)))
    if response.trace_id:
        try:
            url = get_langsmith_trace_url(response.trace_id)
            console.print(f"[dim]LangSmith trace: {url}[/dim]")
        except Exception:
            pass  # helper raises on empty, but we already checked


def _load_person_data(data_arg: str) -> Person:
    path = Path(data_arg)
    raw = path.read_text(encoding="utf-8") if path.exists() else data_arg
    return Person.model_validate_json(raw)


def main(argv: list[str] | None = None) -> int:
    load_dotenv()
    args = _parse_args(argv)
    reset_storage()
    reset_core_graph()
    get_storage()

    if args.command == "seed":
        storage = get_storage()
        count = storage.seed_from_file(Path(args.seed_path))
        console.print(f"Seeded {count} new records from {args.seed_path}")
        return 0

    thread_id = _resolve_thread_id(args.thread_id)

    if args.command == "query":
        query = PersonQuery(
            person_key=args.person_key,
            requested_attributes=list(args.attributes),
        )
        response = run_query(query, thread_id=thread_id)
        _print_response(response)
        return 0 if response.results else 1

    if args.command == "ingest":
        person = _load_person_data(args.data)
        query = PersonQuery(person_key=args.person_key, provided_data=person)
        response = run_query(query, thread_id=thread_id)
        _print_response(response)
        return 0 if response.results else 1

    return 1


if __name__ == "__main__":
    sys.exit(main())
