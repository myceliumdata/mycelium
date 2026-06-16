"""Orchestrate ``mycelium network create`` (Phase 5c)."""

from __future__ import annotations

import json
import os
import re
import shutil
import tempfile
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from agents.factory.agent_factory import AgentFactory
from agents.registry import AgentRegistryData
from agents.specialists.protocol import dispatch_ensure_category_storage
from network.category_mvr_bootstrap import ensure_mvr_fields_in_category_tree
from network.ontology import SkeletonOntologyResult, generate_skeleton_ontology
from network.paths import NetworkPaths, apply_network_paths, framework_root, _provisional_paths
from network.registry import register_network
from network.seed_import import bootstrap_seed_at_paths, count_seed_rows

_NAME_RE = re.compile(r"^[a-z][a-z0-9_]*$")
_DEFAULT_ONTOLOGY_MODEL = "gpt-4o-mini"


class CreateNetworkResult(BaseModel):
    """Outcome of ``create_network`` for CLI printing and tests."""

    name: str
    root: str
    display_name: str | None
    categories_count: int
    specialists_count: int
    dry_run: bool
    registered: bool
    entities_bootstrapped: int = 0
    ontology_json: str | None = None
    mcp_snippet: str | None = None


def validate_network_name(name: str) -> str:
    """Return a registry-safe network name (lowercase slug)."""
    clean = name.strip()
    if not clean:
        raise ValueError("Network name must not be empty")
    if not _NAME_RE.match(clean):
        raise ValueError(
            f"Invalid network name {clean!r}: use lowercase letters, digits, "
            "and underscores (e.g. wheat_farm, prm_crm)",
        )
    return clean


def validate_seed_file(seed_path: Path) -> list[dict[str, Any]]:
    """Read and validate seed JSON (``people`` list with ``name`` per row)."""
    if not seed_path.is_file():
        raise ValueError(f"Seed file not found: {seed_path}")
    try:
        payload = json.loads(seed_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Invalid seed JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError("Seed JSON must be an object with a 'people' array")
    people = payload.get("people")
    if not isinstance(people, list):
        raise ValueError("Seed JSON must contain a 'people' array")
    for index, row in enumerate(people):
        if not isinstance(row, dict):
            raise ValueError(f"Seed people[{index}] must be an object")
        name = row.get("name")
        if not isinstance(name, str) or not name.strip():
            raise ValueError(f"Seed people[{index}] must include a non-empty 'name'")
    return people


def _network_description(creation_prompt: str) -> str:
    first_line = creation_prompt.strip().splitlines()[0].strip()
    if len(first_line) <= 240:
        return first_line
    return first_line[:237] + "..."


def _build_mcp_snippet(name: str, root: Path) -> str:
    payload = {
        f"mycelium-{name}": {
            "command": "uv",
            "args": ["run", "mycelium-mcp"],
            "cwd": str(framework_root()),
            "env": {"MYCELIUM_NETWORK_ROOT": str(root.expanduser().resolve())},
        },
    }
    return json.dumps(payload, indent=2)


def _atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(content)
        os.replace(tmp_path, path)
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def _write_agent_registry(paths: NetworkPaths, agents: list[Any]) -> None:
    now = datetime.now(timezone.utc)
    registry = AgentRegistryData(
        version="1.0",
        last_updated=now,
        agents={agent.name: agent for agent in agents},
    )
    _atomic_write_text(
        paths.registry_path,
        registry.model_dump_json(indent=2) + "\n",
    )


def _write_categories(paths: NetworkPaths, tree: Any) -> None:
    _atomic_write_text(
        paths.categories_path,
        tree.model_dump_json(indent=2) + "\n",
    )


def _prune_orphan_specialists(paths: NetworkPaths, keep_names: set[str]) -> None:
    """Remove generated specialist modules not in the new registry."""
    if not paths.specialists_dir.is_dir():
        return
    for py_file in paths.specialists_dir.glob("*_specialist.py"):
        if py_file.stem not in keep_names:
            py_file.unlink(missing_ok=True)


def scaffold_guide_md(*, title: str, creation_prompt: str) -> str:
    """Scaffold ``guide.md`` for a new network (option B — no LLM)."""
    return (
        f"# {title}\n\n"
        "## About this network (draft — edit freely)\n\n"
        f"{creation_prompt.strip()}\n\n"
        "## Usage\n\n"
        "Edit this file freely. Visiting agents read it via MCP `describe_network`.\n"
    )


def _write_guide(paths: NetworkPaths, *, title: str, creation_prompt: str) -> None:
    _atomic_write_text(
        paths.root / "guide.md",
        scaffold_guide_md(title=title, creation_prompt=creation_prompt),
    )


def _unlink_entity_stores(paths: NetworkPaths) -> None:
    """Remove declared per-grain entity store files."""
    from network.mvr import load_mvr_config

    paths.entities_path.unlink(missing_ok=True)
    config = load_mvr_config(paths=paths)
    for grain in config.grains.values():
        (paths.root / grain.entities_file).unlink(missing_ok=True)


def _crm_metering_block() -> dict[str, Any]:
    return {
        "enabled": False,
        "description": (
            "When enabled: EntityQuery.provenance requests query_provenance meter; "
            "default_funding_model marginal; full_duplicate charges production on cache hits."
        ),
        "default_funding_model": "marginal",
        "meter_first_delivery": True,
        "quote_provider": "builtin",
        "principal": {
            "marginal_optional": True,
            "required_for_funding_models": ["sponsor_public", "pool"],
        },
        "payment": {
            "enabled": False,
            "provider": "mock",
            "require_paid_before_accept": True,
            "description": (
                "When enabled with metering: quote_required → pay_quote MCP → "
                "query_entity+quote_id. Settlement is separate from MCP quote negotiation."
            ),
        },
    }


def _write_network_manifest(
    paths: NetworkPaths,
    *,
    name: str,
    display_name: str | None,
    creation_prompt: str,
    ontology_model: str,
) -> None:
    now = datetime.now(timezone.utc).isoformat()
    manifest = {
        "name": name,
        "display_name": display_name or name,
        "description": _network_description(creation_prompt),
        "created_at": now,
        "creation_prompt": creation_prompt,
        "ontology_model": ontology_model,
        "bootstrap": {
            "module": "network.bootstrap.handlers.default_seed",
            "handler": "DefaultSeedHandler",
        },
        "mvr": {
            "default_grain": "person",
            "grains": {
                "person": {
                    "bind_fields": ["name", "employer"],
                    "description": (
                        "CRM people: display name plus current employer "
                        "before bind and research."
                    ),
                },
            },
        },
        "metering": _crm_metering_block(),
    }
    paths.root.mkdir(parents=True, exist_ok=True)
    (paths.root / "network.json").write_text(
        json.dumps(manifest, indent=2) + "\n",
        encoding="utf-8",
    )


def _render_specialists(
    ontology: SkeletonOntologyResult,
    paths: NetworkPaths,
) -> list[Path]:
    apply_network_paths(paths)
    factory = AgentFactory(specialists_dir=paths.specialists_dir)
    written: list[Path] = []
    for agent in ontology.agents:
        dispatch_ensure_category_storage(agent.category)
        category = ontology.categories.categories[agent.category]
        written.append(
            factory.render_specialist_py(
                category=agent.category,
                agent_name=agent.name,
                description=agent.description,
                examples=category.examples,
                created_at=agent.created_at,
            ),
        )
    return written


def create_network(
    name: str,
    root: str | Path,
    creation_prompt: str,
    *,
    seed_path: str | Path | None = None,
    display_name: str | None = None,
    default: bool = False,
    dry_run: bool = False,
    force: bool = False,
    print_mcp_snippet: bool = True,
    llm: Any | None = None,
    ontology_fn: Callable[[str], SkeletonOntologyResult] | None = None,
) -> CreateNetworkResult:
    """Stand up a custom-domain network under ``root``."""
    clean_name = validate_network_name(name)
    prompt = creation_prompt.strip()
    if not prompt:
        raise ValueError("creation_prompt must not be empty")

    resolved_root = Path(root).expanduser().resolve()
    manifest_path = resolved_root / "network.json"
    if manifest_path.exists() and not force and not dry_run:
        raise ValueError(
            f"Network already exists at {resolved_root} "
            "(network.json present). Use --force to overwrite.",
        )

    seed_file: Path | None = None
    if seed_path is not None:
        seed_file = Path(seed_path).expanduser().resolve()
        validate_seed_file(seed_file)

    generator = ontology_fn or (
        lambda p: generate_skeleton_ontology(p, llm=llm)
    )
    ontology = generator(prompt)

    entities_bootstrapped = count_seed_rows(seed_file) if seed_file is not None else 0

    if dry_run:
        return CreateNetworkResult(
            name=clean_name,
            root=str(resolved_root),
            display_name=display_name,
            categories_count=len(ontology.categories.categories),
            specialists_count=len(ontology.agents),
            dry_run=True,
            registered=False,
            entities_bootstrapped=entities_bootstrapped,
            ontology_json=ontology.categories.model_dump_json(indent=2),
            mcp_snippet=_build_mcp_snippet(clean_name, resolved_root)
            if print_mcp_snippet
            else None,
        )

    resolved_root.mkdir(parents=True, exist_ok=True)
    provisional = _provisional_paths(resolved_root)
    _write_network_manifest(
        provisional,
        name=clean_name,
        display_name=display_name,
        creation_prompt=prompt,
        ontology_model=ontology.model_used,
    )
    paths = NetworkPaths.from_root(resolved_root)
    if force:
        _prune_orphan_specialists(
            paths,
            {agent.name for agent in ontology.agents},
        )
        if seed_file is None:
            paths.seed_path.unlink(missing_ok=True)
            _unlink_entity_stores(paths)
    entities_bootstrapped = 0
    if seed_file is not None:
        shutil.copy2(seed_file, paths.seed_path)
    ontology.categories = ensure_mvr_fields_in_category_tree(ontology.categories)
    _write_categories(paths, ontology.categories)
    _write_agent_registry(paths, ontology.agents)
    _render_specialists(ontology, paths)
    if seed_file is not None:
        entities_bootstrapped = bootstrap_seed_at_paths(paths)
    _write_guide(
        paths,
        title=display_name or clean_name,
        creation_prompt=prompt,
    )
    register_network(clean_name, resolved_root, default=default)

    return CreateNetworkResult(
        name=clean_name,
        root=str(resolved_root),
        display_name=display_name,
        categories_count=len(ontology.categories.categories),
        specialists_count=len(ontology.agents),
        dry_run=False,
        registered=True,
        entities_bootstrapped=entities_bootstrapped,
        mcp_snippet=_build_mcp_snippet(clean_name, resolved_root)
        if print_mcp_snippet
        else None,
    )
