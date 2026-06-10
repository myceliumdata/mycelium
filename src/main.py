"""CLI for local testing of the Mycelium core graph."""

from __future__ import annotations

import argparse
import atexit
import json
import os
import sys
import uuid
from pathlib import Path

from dotenv import load_dotenv
from rich.console import Console
from rich.json import JSON

# Use the stable sync checkpointer path for the one-shot CLI as well.
# (The MCP server does the same; Studio keeps the async path via default.)
os.environ["MYCELIUM_USE_SYNC_CHECKPOINTER"] = "1"

from graphs.core import reset_core_graph, run_query
from models.state import EntityQuery, QueryResponse
from network.create import create_network
from network.ontology import OntologyGenerationError
from network.introspection import (
    build_network_status,
    format_status_demo,
    format_status_verbose,
    status_to_dict,
)
from network.paths import NetworkPaths, apply_network_paths, resolve_network_root
from network.registry import list_networks, register_network, set_default_network
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

    query_cmd = sub.add_parser("query", help="Query a seed record (JSON response)")
    query_cmd.add_argument("--entity-key", required=True, help="Id, email, or name")
    query_cmd.add_argument(
        "--attributes",
        nargs="*",
        default=[],
        help="Non-core attributes (seed identity in results; message describes specialist status)",
    )
    query_cmd.add_argument(
        "--thread-id",
        default=None,
        metavar="ID",
        help=_THREAD_ID_HELP,
    )
    query_cmd.add_argument(
        "--network-dir",
        default=None,
        metavar="DIR",
        help=(
            "Network data root (seed, registry, agents, DB). "
            "Highest precedence; overrides --network and env selectors"
        ),
    )
    query_cmd.add_argument(
        "--network",
        default=None,
        metavar="NAME",
        help="Registered network name (see: mycelium network list)",
    )
    query_cmd.add_argument(
        "--employer",
        default=None,
        metavar="NAME",
        help="MVR bind field: sets binding.employer on EntityQuery",
    )
    query_cmd.add_argument(
        "--binding-json",
        default=None,
        metavar="JSON",
        help='Full binding object as JSON (overrides --employer), e.g. \'{"employer":"Acme Corp"}\'',
    )
    query_cmd.add_argument(
        "--quote-id",
        default=None,
        metavar="ID",
        help="Accepted quote id from a prior quote_required response (metering retry)",
    )
    query_cmd.add_argument(
        "--provenance",
        action="store_true",
        help="Request query delivery with sources/audit trail (query_provenance meter)",
    )

    network_cmd = sub.add_parser("network", help="Manage registered networks")
    network_sub = network_cmd.add_subparsers(dest="network_command", required=True)

    register_cmd = network_sub.add_parser(
        "register",
        help="Register or update a network name → root path",
    )
    register_cmd.add_argument("name", help="Short network alias (e.g. prm_crm)")
    register_cmd.add_argument(
        "--root",
        required=True,
        metavar="PATH",
        help="Absolute path to network_root",
    )
    register_cmd.add_argument(
        "--default",
        action="store_true",
        help="Mark as default network (auto-set when first registered)",
    )

    network_sub.add_parser("list", help="List registered networks")

    status_cmd = network_sub.add_parser(
        "status",
        help="Read-only snapshot of seed, ontology, specialists, and storage",
    )
    status_cmd.add_argument(
        "--network-dir",
        default=None,
        metavar="DIR",
        help="Network data root (highest precedence)",
    )
    status_cmd.add_argument(
        "--network",
        default=None,
        metavar="NAME",
        help="Registered network name",
    )
    status_cmd.add_argument(
        "--json",
        action="store_true",
        help="Machine-readable JSON output",
    )
    status_cmd.add_argument(
        "--category",
        default=None,
        metavar="NAME",
        help="Filter to one ontology category",
    )
    status_cmd.add_argument(
        "--entity",
        default=None,
        metavar="KEY",
        help="Drill down to one seed record (name or id)",
    )
    status_cmd.add_argument(
        "--verbose",
        action="store_true",
        help="Debug-oriented status layout (includes root path and agent details)",
    )

    use_cmd = network_sub.add_parser("use", help="Set the default network")
    use_cmd.add_argument("name", help="Registered network name")

    create_cmd = network_sub.add_parser(
        "create",
        help="Create a new network with custom ontology from a creation prompt",
    )
    create_cmd.add_argument("name", help="Registry name (lowercase slug, e.g. wheat_farm)")
    create_cmd.add_argument(
        "--root",
        required=True,
        metavar="PATH",
        help="Absolute path to network_root (created if missing)",
    )
    create_cmd.add_argument(
        "--seed",
        required=True,
        metavar="FILE",
        help="Seed JSON file (must contain a 'people' array)",
    )
    prompt_group = create_cmd.add_mutually_exclusive_group(required=True)
    prompt_group.add_argument(
        "--prompt",
        metavar="TEXT",
        help="Inline creation prompt describing what data the network manages",
    )
    prompt_group.add_argument(
        "--prompt-file",
        metavar="FILE",
        help="Path to a creation prompt text file",
    )
    create_cmd.add_argument(
        "--display-name",
        default=None,
        metavar="NAME",
        help="Human-readable network label for network.json",
    )
    create_cmd.add_argument(
        "--default",
        action="store_true",
        help="Register as the default network",
    )
    create_cmd.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and print ontology JSON without writing files",
    )
    create_cmd.add_argument(
        "--force",
        action="store_true",
        help="Overwrite an existing network_root that already has network.json",
    )
    create_cmd.add_argument(
        "--no-mcp-snippet",
        action="store_true",
        help="Suppress MCP client JSON snippet on success",
    )

    seed_cmd = sub.add_parser(
        "seed",
        help=(
            "Legacy: load a JSON people file into SQLite at the resolved network_root DB. "
            "Uses the same network selection as query "
            "(--network-dir, --network, env, or registry default). "
            "Queries read seed.json via agents.seed, not SQLite."
        ),
    )
    seed_cmd.add_argument(
        "--network-dir",
        default=None,
        metavar="DIR",
        help=(
            "Network data root for SQLite DB path. "
            "Highest precedence; overrides --network and env selectors"
        ),
    )
    seed_cmd.add_argument(
        "--network",
        default=None,
        metavar="NAME",
        help="Registered network name (see: mycelium network list)",
    )
    seed_cmd.add_argument(
        "--seed-path",
        default="examples/networks/crm/seed.json",
        help="JSON people file to load into the resolved network SQLite DB",
    )

    return parser.parse_args(argv)


def _resolve_thread_id(cli_thread_id: str | None) -> str:
    """Use caller-supplied thread id or generate one for this invocation."""
    return cli_thread_id if cli_thread_id else str(uuid.uuid4())


def _binding_from_args(args: argparse.Namespace) -> dict[str, str]:
    """Build EntityQuery.binding from --binding-json or --employer."""
    if args.binding_json:
        raw = json.loads(args.binding_json)
        if not isinstance(raw, dict):
            msg = "--binding-json must be a JSON object"
            raise ValueError(msg)
        return {str(key): str(value) for key, value in raw.items()}
    if args.employer:
        return {"employer": str(args.employer).strip()}
    return {}


def _entity_query_from_args(args: argparse.Namespace) -> EntityQuery:
    """Map CLI query flags to EntityQuery."""
    binding = _binding_from_args(args)
    return EntityQuery(
        entity_key=args.entity_key,
        requested_attributes=list(args.attributes),
        binding=binding,
        quote_id=args.quote_id,
        provenance=bool(args.provenance),
    )


def _print_response(response: QueryResponse) -> None:
    """Print full QueryResponse JSON including trace_id and thread_id.
    If trace_id is present, also print a direct LangSmith trace URL using the helper.
    """
    console.print(JSON(response.model_dump_json(indent=2)))
    if response.trace_id:
        try:
            url = get_langsmith_trace_url(response.trace_id)
            console.print(f"[dim]LangSmith trace: {url}[/dim]")
        except Exception:
            pass  # helper raises on empty, but we already checked


def _configure_network_paths(
    *,
    cli_network_dir: str | None = None,
    cli_network_name: str | None = None,
) -> Path:
    """Resolve network_root and export derived paths via MYCELIUM_* env vars."""
    root = resolve_network_root(
        cli_network_dir=cli_network_dir,
        cli_network_name=cli_network_name,
    )
    apply_network_paths(NetworkPaths.from_root(root))
    return root


def _run_network_command(args: argparse.Namespace) -> int:
    """Handle ``mycelium network`` subcommands."""
    try:
        if args.network_command == "register":
            entry = register_network(
                args.name,
                args.root,
                default=args.default,
            )
            suffix = " (default)" if entry.default else ""
            console.print(f"Registered [bold]{entry.name}[/bold] → {entry.root}{suffix}")
            return 0

        if args.network_command == "list":
            entries = list_networks()
            if not entries:
                console.print("No networks registered.")
                console.print(
                    "Register one: [dim]mycelium network register <name> --root <path>[/dim]",
                )
                return 0
            for entry in entries:
                marker = " (default)" if entry.default else ""
                console.print(f"{entry.name}\t{entry.root}{marker}")
            return 0

        if args.network_command == "use":
            entry = set_default_network(args.name)
            console.print(f"Default network: [bold]{entry.name}[/bold] → {entry.root}")
            return 0

        if args.network_command == "status":
            try:
                _configure_network_paths(
                    cli_network_dir=args.network_dir,
                    cli_network_name=args.network,
                )
                summary = build_network_status(
                    category_filter=args.category,
                    entity_key=args.entity,
                )
            except (ValueError, FileNotFoundError) as exc:
                console.print(f"[red]Error:[/red] {exc}")
                return 2
            if args.json:
                print(json.dumps(status_to_dict(summary), indent=2))
            elif args.verbose:
                console.print(format_status_verbose(summary))
            else:
                console.print(format_status_demo(summary))
            return 0

        if args.network_command == "create":
            prompt = args.prompt
            if args.prompt_file:
                prompt = Path(args.prompt_file).expanduser().read_text(encoding="utf-8")
            result = create_network(
                args.name,
                args.root,
                args.seed,
                prompt or "",
                display_name=args.display_name,
                default=args.default,
                dry_run=args.dry_run,
                force=args.force,
                print_mcp_snippet=not args.no_mcp_snippet,
            )
            if result.dry_run:
                console.print("[yellow]Dry run[/yellow] — no files written.")
                console.print(
                    "[dim]On create, guide.md will be scaffolded at the network root.[/dim]",
                )
            else:
                console.print(
                    f"Created network [bold]{result.name}[/bold] at {result.root}",
                )
            console.print(
                f"Categories: {result.categories_count} · "
                f"Specialists: {result.specialists_count}",
            )
            if result.registered:
                suffix = " (default)" if args.default else ""
                console.print(f"Registered [bold]{result.name}[/bold]{suffix}")
            if result.ontology_json:
                console.print("[dim]Ontology preview:[/dim]")
                console.print(JSON(result.ontology_json))
            if result.mcp_snippet:
                console.print("[dim]MCP client snippet (add under mcpServers):[/dim]")
                console.print(result.mcp_snippet)
            return 0
    except (ValueError, OntologyGenerationError) as exc:
        console.print(f"[red]Error:[/red] {exc}")
        return 2

    console.print(f"[red]Unknown network command:[/red] {args.network_command}")
    return 2


def main(argv: list[str] | None = None) -> int:
    load_dotenv()
    args = _parse_args(argv)

    # Register atexit handler as belt-and-suspenders so resources are cleaned
    # even on unexpected exits (signals, uncaught exceptions in some paths, etc.).
    atexit.register(_cleanup_resources)

    if args.command == "network":
        return _run_network_command(args)

    if args.command in ("query", "seed"):
        try:
            _configure_network_paths(
                cli_network_dir=getattr(args, "network_dir", None),
                cli_network_name=getattr(args, "network", None),
            )
        except ValueError as exc:
            console.print(f"[red]Error:[/red] {exc}")
            return 2

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

        try:
            query = _entity_query_from_args(args)
        except (ValueError, json.JSONDecodeError) as exc:
            console.print(f"[red]Error:[/red] {exc}")
            return 2

        response = run_query(query, thread_id=thread_id)
        _print_response(response)
        return 0 if response.results else 1
    finally:
        _cleanup_resources()


if __name__ == "__main__":
    sys.exit(main())
