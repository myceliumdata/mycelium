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
from network.registry import (
    list_networks,
    network_root_status,
    register_network,
    set_default_network,
    unregister_network,
)
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

    query_cmd = sub.add_parser(
        "query",
        help="Query entities via the target two-step protocol (JSON response)",
        epilog=(
            "Target protocol (MVR redesign):\n"
            "  Step 1 — resolve: --id UUID  OR  --lookup-json '{\"employer\":\"Accel\"}'\n"
            "           optional --attributes, --provenance\n"
            "           → lookup_resolved (+ delivery_id) or quote_required\n"
            "  Step 2 — deliver: --delivery-id d_…  (+ --quote-id when metered)\n"
            "           → found / assembled with full results[]\n"
            "\n"
            "Legacy --entity-key / --employer / --binding-json removed in M9. "
            "Use lookup JSON with name + employer for full MVR bind."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    step = query_cmd.add_mutually_exclusive_group(required=True)
    step.add_argument(
        "--id",
        metavar="UUID",
        help="Step 1: resolve one entity by registry UUID",
    )
    step.add_argument(
        "--lookup-json",
        metavar="JSON",
        help='Step 1: partial lookup map, e.g. \'{"employer":"645 Ventures"}\'',
    )
    step.add_argument(
        "--delivery-id",
        metavar="ID",
        help="Step 2: deliver a prior delivery_id from lookup_resolved",
    )
    query_cmd.add_argument(
        "--confirm-new-entity",
        action="store_true",
        help=(
            "Step 1: create a new entity even when same-name rows exist under "
            "a different employer (use after lookup_suggested)"
        ),
    )
    query_cmd.add_argument(
        "--attributes",
        nargs="*",
        default=[],
        help="Non-core attributes (registry identity in results; message describes specialist status)",
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
            "Network data root (entities, registry, agents, DB). "
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
        help=argparse.SUPPRESS,
    )
    query_cmd.add_argument(
        "--binding-json",
        default=None,
        metavar="JSON",
        help=argparse.SUPPRESS,
    )
    query_cmd.add_argument(
        "--entity-key",
        default=None,
        metavar="KEY",
        help=argparse.SUPPRESS,
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

    unregister_cmd = network_sub.add_parser(
        "unregister",
        help="Remove a stale or unused network registration",
    )
    unregister_cmd.add_argument("name", help="Registered network name")

    status_cmd = network_sub.add_parser(
        "status",
        help="Read-only snapshot of entities, ontology, specialists, and storage",
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
        "--id",
        default=None,
        metavar="UUID",
        help="Drill down to one entity by registry UUID",
    )
    status_cmd.add_argument(
        "--lookup-json",
        default=None,
        metavar="JSON",
        help='Drill down via MVR lookup map, e.g. \'{"name":"Ada","employer":"Acme"}\'',
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
        default=None,
        metavar="FILE",
        help="Optional seed JSON file (rows array); imported into entities.json when provided",
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

    return parser.parse_args(argv)


def _resolve_thread_id(cli_thread_id: str | None) -> str:
    """Use caller-supplied thread id or generate one for this invocation."""
    return cli_thread_id if cli_thread_id else str(uuid.uuid4())


def _entity_query_from_args(args: argparse.Namespace) -> EntityQuery:
    """Map CLI query flags to EntityQuery (target two-step protocol)."""
    if getattr(args, "entity_key", None) or getattr(args, "employer", None) or getattr(
        args, "binding_json", None
    ):
        msg = (
            "Legacy --entity-key / --employer / --binding-json removed. "
            "Use --lookup-json with MVR fields or --id / --delivery-id."
        )
        raise ValueError(msg)

    delivery_id = (getattr(args, "delivery_id", None) or "").strip() or None
    entity_id = (getattr(args, "id", None) or "").strip() or None
    lookup: dict[str, str] = {}
    if getattr(args, "lookup_json", None):
        raw = json.loads(args.lookup_json)
        if not isinstance(raw, dict):
            msg = "--lookup-json must be a JSON object"
            raise ValueError(msg)
        lookup = {str(key): str(value) for key, value in raw.items()}

    return EntityQuery(
        id=entity_id,
        lookup=lookup,
        delivery_id=delivery_id,
        requested_attributes=list(args.attributes),
        quote_id=args.quote_id,
        provenance=bool(args.provenance),
        confirm_new_entity=bool(getattr(args, "confirm_new_entity", False)),
    )


def _print_response(response: QueryResponse) -> None:
    """Print full QueryResponse JSON including trace_id and thread_id.
    If trace_id is present, also print a direct LangSmith trace URL using the helper.
    """
    console.print(JSON(response.public_json()))
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
            stale = 0
            for entry in entries:
                markers: list[str] = []
                if entry.default:
                    markers.append("default")
                status = network_root_status(entry.root)
                if status != "ok":
                    markers.append(status)
                    stale += 1
                suffix = f" ({', '.join(markers)})" if markers else ""
                line = f"{entry.name}\t{entry.root}{suffix}"
                if status == "missing":
                    console.print(f"[dim]{line}[/dim]")
                elif status == "uninitialized":
                    console.print(f"[yellow]{line}[/yellow]")
                else:
                    console.print(line)
            if stale:
                console.print(
                    "[dim]Stale entries: mycelium network unregister <name> "
                    "or re-register with --root[/dim]",
                )
            return 0

        if args.network_command == "unregister":
            removed = unregister_network(args.name)
            if removed is None:
                console.print(f"[red]Unknown network:[/red] {args.name}")
                return 1
            console.print(
                f"Unregistered [bold]{removed.name}[/bold] → {removed.root}",
            )
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
                resolve_id = (args.id or "").strip() or None
                resolve_lookup: dict[str, str] | None = None
                if args.lookup_json:
                    raw = json.loads(args.lookup_json)
                    if not isinstance(raw, dict):
                        raise ValueError("--lookup-json must be a JSON object")
                    resolve_lookup = {
                        str(key): str(value)
                        for key, value in raw.items()
                        if str(value).strip()
                    } or None
                if resolve_id and resolve_lookup:
                    raise ValueError(
                        "Use --id or --lookup-json for drill-down, not both",
                    )
                summary = build_network_status(
                    category_filter=args.category,
                    resolve_id=resolve_id,
                    resolve_lookup=resolve_lookup,
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
                prompt or "",
                seed_path=args.seed,
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
            if result.entities_bootstrapped > 0:
                console.print(
                    f"Seed bootstrap: {result.entities_bootstrapped} entities imported",
                )
            elif not result.dry_run:
                console.print(
                    "[dim]No seed bootstrap — registry empty until first bind[/dim]",
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

    if args.command == "query":
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
        thread_id = _resolve_thread_id(args.thread_id)

        try:
            query = _entity_query_from_args(args)
        except (ValueError, json.JSONDecodeError) as exc:
            console.print(f"[red]Error:[/red] {exc}")
            return 2

        response = run_query(query, thread_id=thread_id)
        _print_response(response)
        if response.outcome in {"lookup_resolved", "quote_required", "payment_required"}:
            return 0
        return 0 if response.results else 1
    finally:
        _cleanup_resources()


if __name__ == "__main__":
    sys.exit(main())
