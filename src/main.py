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
from models.state import Person, PersonQuery
from storage.core import get_storage, reset_storage

console = Console()


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
    query_cmd.add_argument("--thread-id", default=None)

    ingest_cmd = sub.add_parser("ingest", help="Ingest person with provided JSON file or inline")
    ingest_cmd.add_argument("--person-key", required=True)
    ingest_cmd.add_argument(
        "--data",
        required=True,
        help="Path to JSON file or inline JSON with Person fields",
    )
    ingest_cmd.add_argument("--thread-id", default=None)

    seed_cmd = sub.add_parser("seed", help="Reload seed CRM data into SQLite")
    seed_cmd.add_argument(
        "--seed-path",
        default="data/seed_crm.json",
        help="Path to seed JSON file",
    )

    return parser.parse_args(argv)


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

    thread_id = getattr(args, "thread_id", None) or str(uuid.uuid4())

    if args.command == "query":
        query = PersonQuery(
            person_key=args.person_key,
            requested_attributes=list(args.attributes),
        )
        response = run_query(query, thread_id=thread_id)
        console.print(JSON(response.model_dump_json(indent=2)))
        return 0 if response.results else 1

    if args.command == "ingest":
        person = _load_person_data(args.data)
        query = PersonQuery(person_key=args.person_key, provided_data=person)
        response = run_query(query, thread_id=thread_id)
        console.print(JSON(response.model_dump_json(indent=2)))
        return 0 if response.results else 1

    return 1


if __name__ == "__main__":
    sys.exit(main())
