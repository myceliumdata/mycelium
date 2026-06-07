"""Smoke tests for the committed CRM example network."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from agents.seed import find_by_key, get_seed_data, reset_seed_data
from network.paths import NetworkPaths, apply_network_paths, resolve_network_root

REPO_ROOT = Path(__file__).resolve().parent.parent
EXAMPLE_CRM = REPO_ROOT / "examples" / "networks" / "crm"
_RUNTIME_ARTIFACTS = (
    "categories.json",
    "checkpoints.sqlite",
    "mycelium.db",
    "agent_registry.json",
)


@pytest.mark.smoke
def test_example_crm_layout() -> None:
    assert (EXAMPLE_CRM / "seed.json").is_file()
    assert (EXAMPLE_CRM / "network.json").is_file()
    assert (EXAMPLE_CRM / "README.md").is_file()
    for runtime_artifact in _RUNTIME_ARTIFACTS:
        assert not (EXAMPLE_CRM / runtime_artifact).exists()


@pytest.mark.smoke
def test_example_crm_seed_has_demo_people() -> None:
    payload = json.loads((EXAMPLE_CRM / "seed.json").read_text(encoding="utf-8"))
    names = [person["name"] for person in payload["people"]]
    assert "Nichanan Kesonpat" in names
    assert "Andrea Kalmans" in names
    assert names.count("Kevin Zhang") == 2


@pytest.mark.smoke
def test_resolve_example_crm_network_dir(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.delenv("MYCELIUM_NETWORK_ROOT", raising=False)
    monkeypatch.delenv("MYCELIUM_NETWORK", raising=False)
    monkeypatch.setenv("MYCELIUM_NETWORKS_CONFIG", str(tmp_path / "missing.json"))
    monkeypatch.setenv("MYCELIUM_FRAMEWORK_ROOT", str(tmp_path / "framework"))

    root = resolve_network_root(cli_network_dir=str(EXAMPLE_CRM))
    assert root == EXAMPLE_CRM.resolve()


@pytest.mark.smoke
def test_example_crm_seed_loads_via_network_paths(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("MYCELIUM_NETWORKS_CONFIG", str(tmp_path / "missing.json"))
    paths = NetworkPaths.from_root(EXAMPLE_CRM)
    apply_network_paths(paths)
    reset_seed_data()
    _ = get_seed_data()
    matches = find_by_key("Nichanan Kesonpat")
    assert len(matches) == 1
    assert matches[0]["name"] == "Nichanan Kesonpat"


@pytest.mark.smoke
def test_copy_example_network_script(tmp_path: Path) -> None:
    target = tmp_path / "my-crm"
    script = REPO_ROOT / "bin" / "copy-example-network"
    result = subprocess.run(
        [sys.executable, str(script), "crm", "--root", str(target)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr or result.stdout
    assert (target / "seed.json").is_file()
    assert (target / "network.json").is_file()
    assert not (target / "README.md").exists()
    assert not (target / "prepare_seed.py").exists()
    for runtime_artifact in _RUNTIME_ARTIFACTS:
        assert not (target / runtime_artifact).exists()
