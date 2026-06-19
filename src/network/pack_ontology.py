"""Install committed example-pack ontologies (categories.json + agent registry + stubs)."""

from __future__ import annotations

import json
import os
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from agents.classification.models import CategoryTreeData
from agents.factory.agent_factory import AgentFactory
from agents.registry import AgentRegistryData, RegisteredAgent, reset_agent_registry
from agents.specialists.base import registry_storage_paths
from agents.specialists.protocol import dispatch_ensure_category_storage
from network.category_mvr_bootstrap import (
    _required_bind_fields,
    ensure_mvr_fields_in_category_tree,
)
from network.paths import NetworkPaths, apply_network_paths, framework_root


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


def _write_agent_registry(paths: NetworkPaths, agents: list[RegisteredAgent]) -> None:
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


def _examples_root() -> Path:
    return framework_root() / "examples" / "networks"


def example_pack_categories_path(example_name: str) -> Path:
    """Path to committed ``categories.json`` for an example network pack."""
    return _examples_root() / example_name / "categories.json"


def is_pack_ontology(categories_path: Path) -> bool:
    """True when ``categories.json`` declares a non-empty ``ontology_pack``."""
    if not categories_path.is_file():
        return False
    try:
        data = json.loads(categories_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    if not isinstance(data, dict):
        return False
    pack = data.get("ontology_pack")
    return isinstance(pack, str) and bool(pack.strip())


def _infer_example_name(paths: NetworkPaths) -> str | None:
    manifest = paths.root / "network.json"
    if not manifest.is_file():
        return None
    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict):
        return None
    raw = data.get("name")
    if isinstance(raw, str) and raw.strip():
        return raw.strip()
    return None


def _agents_from_category_tree(tree: CategoryTreeData) -> list[RegisteredAgent]:
    now_iso = datetime.now(timezone.utc).isoformat()
    agents: list[RegisteredAgent] = []
    seen: set[str] = set()
    for key, cat in tree.categories.items():
        agent_name = cat.assigned_agent
        if agent_name in seen:
            continue
        seen.add(agent_name)
        storage_path, strategy_path = registry_storage_paths(key)
        agents.append(
            RegisteredAgent(
                name=agent_name,
                category=key,
                description=cat.description,
                module_path=f"agents.specialists.{agent_name}",
                entrypoint=agent_name,
                storage_path=storage_path,
                strategy_path=strategy_path,
                is_generated=True,
                created_at=now_iso,
            ),
        )
    return agents


def _render_missing_specialists(
    tree: CategoryTreeData,
    agents: list[RegisteredAgent],
    paths: NetworkPaths,
) -> None:
    apply_network_paths(paths)
    factory = AgentFactory(specialists_dir=paths.specialists_dir)
    paths.specialists_dir.mkdir(parents=True, exist_ok=True)
    for agent in agents:
        py_path = paths.specialists_dir / f"{agent.name}.py"
        if py_path.is_file():
            continue
        dispatch_ensure_category_storage(agent.category)
        category = tree.categories[agent.category]
        factory.render_specialist_py(
            category=agent.category,
            agent_name=agent.name,
            description=agent.description,
            examples=category.examples,
            created_at=agent.created_at,
        )


def _install_pack_specialists(example_name: str, paths: NetworkPaths) -> None:
    """Copy committed pack specialist modules over factory stubs."""
    pack_dir = _examples_root() / example_name / "specialists"
    if not pack_dir.is_dir():
        return
    paths.specialists_dir.mkdir(parents=True, exist_ok=True)
    for py_file in sorted(pack_dir.glob("*.py")):
        shutil.copy2(py_file, paths.specialists_dir / py_file.name)


def install_pack_ontology_from_example(example_name: str, paths: NetworkPaths) -> bool:
    """Copy committed pack ontology into a live root; register agents and stub specialists."""
    source = example_pack_categories_path(example_name)
    if not source.is_file() or not is_pack_ontology(source):
        return False

    apply_network_paths(paths)
    paths.categories_path.parent.mkdir(parents=True, exist_ok=True)
    raw = json.loads(source.read_text(encoding="utf-8"))
    tree = CategoryTreeData.model_validate(raw)
    required = _required_bind_fields(paths)
    tree = ensure_mvr_fields_in_category_tree(tree, required)
    _atomic_write_text(
        paths.categories_path,
        tree.model_dump_json(indent=2) + "\n",
    )

    agents = _agents_from_category_tree(tree)
    _write_agent_registry(paths, agents)
    _render_missing_specialists(tree, agents, paths)
    _install_pack_specialists(example_name, paths)

    from agents.classification import get_category_tree, reset_category_tree

    reset_category_tree()
    reset_agent_registry()
    get_category_tree()
    return True


def maybe_install_pack_ontology(paths: NetworkPaths) -> bool:
    """Install pack ontology from example dir when live root lacks one."""
    if is_pack_ontology(paths.categories_path):
        return False
    example = _infer_example_name(paths)
    if example is None:
        return False
    return install_pack_ontology_from_example(example, paths)
