"""CLI for local testing of the Mycelium core graph."""

from __future__ import annotations

import argparse
import atexit
import sys
import uuid
from pathlib import Path

from dotenv import load_dotenv
from rich.console import Console
from rich.json import JSON

from graphs.core import reset_core_graph, run_query
from models.state import PersonQuery, PersonResponse
from storage.core import get_storage, reset_storage
from utils.langsmith import get_langsmith_trace_url

console = Console()


def _cleanup_resources() -> None:
    """Defensively close async checkpointer and storage resources.

    Swallows all errors so that cleanup never prevents the process from exiting.
    Used both in finally blocks and as an atexit handler (belt-and-suspenders).
    """
    for closer in (reset_core_graph, reset_storage):
        try:
            closer()
        except Exception:
            # Never let cleanup errors (e.g. closed loop, double-close, etc.)
            # prevent the CLI from terminating.
            pass


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


def main(argv: list[str] | None = None) -> int:
    load_dotenv()
    args = _parse_args(argv)

    # Register atexit handler as belt-and-suspenders so resources are cleaned
    # even on unexpected exits (signals, uncaught exceptions in some paths, etc.).
    atexit.register(_cleanup_resources)

    reset_storage()
    reset_core_graph()
    get_storage()

    try:
        if args.command == "seed":
            storage = get_storage()
            count = storage.seed_from_file(Path(args.seed_path))
            console.print(f"Seeded {count} new records from {args.seed_path}")
            return 0

        thread_id = _resolve_thread_id(args.thread_id)

        query = PersonQuery(
            person_key=args.person_key,
            requested_attributes=list(args.attributes),
        )
        response = run_query(query, thread_id=thread_id)
        _print_response(response)
        return 0 if response.results else 1
    finally:
        _cleanup_resources()


if __name__ == "__main__":
    sys.exit(main())
