"""Smoke tests for the committed CRM example network and refresh script."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from agents.entity_registry import reset_entity_registry
from agents.entity_resolution import lookup_entities_by_key
from network.example import refresh_example_network
from network_helpers import import_seed_at_root
from network.paths import NetworkPaths, apply_network_paths, resolve_network_root
from network.registry import list_networks
from network.seed_import import import_seed_file

REPO_ROOT = Path(__file__).resolve().parent.parent
EXAMPLE_CRM = REPO_ROOT / "examples" / "networks" / "crm"
EXAMPLE_CRM_METERING = REPO_ROOT / "examples" / "networks" / "crm-metering"
_REFRESH_SCRIPT = REPO_ROOT / "bin" / "refresh-example-network"
_RUNTIME_ARTIFACTS = (
    "categories.json",
    "checkpoints.sqlite",
    "mycelium.db",
    "agent_registry.json",
)


def _run_refresh(
    *args: str,
    env: dict[str, str] | None = None,
    input_text: str | None = None,
) -> subprocess.CompletedProcess[str]:
    run_env = {**os.environ, "PYTHONPATH": str(REPO_ROOT / "src"), **(env or {})}
    return subprocess.run(
        [sys.executable, str(_REFRESH_SCRIPT), *args],
        cwd=REPO_ROOT,
        env=run_env,
        capture_output=True,
        text=True,
        input=input_text,
        check=False,
    )


@pytest.mark.smoke
def test_example_crm_layout() -> None:
    assert (EXAMPLE_CRM / "seed.json").is_file()
    assert (EXAMPLE_CRM / "network.json").is_file()
    assert (EXAMPLE_CRM / "guide.md").is_file()
    assert (EXAMPLE_CRM / "README.md").is_file()
    for runtime_artifact in _RUNTIME_ARTIFACTS:
        assert not (EXAMPLE_CRM / runtime_artifact).exists()


@pytest.mark.smoke
def test_example_crm_metering_layout() -> None:
    assert (EXAMPLE_CRM_METERING / "seed.json").is_file()
    assert (EXAMPLE_CRM_METERING / "network.json").is_file()
    assert (EXAMPLE_CRM_METERING / "queries" / "02-quote-email.json").is_file()
    meta = json.loads((EXAMPLE_CRM_METERING / "network.json").read_text(encoding="utf-8"))
    assert meta["metering"]["enabled"] is True
    assert meta["metering"]["payment"]["enabled"] is False


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
    reset_entity_registry()
    import_seed_at_root(EXAMPLE_CRM)
    matches = lookup_entities_by_key("Nichanan Kesonpat")
    assert len(matches) == 1
    assert matches[0]["name"] == "Nichanan Kesonpat"


@pytest.mark.smoke
def test_refresh_example_network_empty_root(tmp_path: Path) -> None:
    target = tmp_path / "my-crm"
    result = subprocess.run(
        [
            sys.executable,
            str(_REFRESH_SCRIPT),
            "crm",
            "--root",
            str(target),
            "--no-register",
            "--yes",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr or result.stdout
    assert "seed: seed.json → 15 entities imported" in result.stdout
    assert (target / "seed.json").is_file()
    assert (target / "network.json").is_file()
    assert not (target / "README.md").exists()
    assert not (target / "prepare_seed.py").exists()
    for runtime_artifact in _RUNTIME_ARTIFACTS:
        assert not (target / runtime_artifact).exists()


@pytest.mark.smoke
def test_refresh_empty_crm_has_no_seed_or_entities(tmp_path: Path) -> None:
    target = tmp_path / "empty-crm-live"
    result = refresh_example_network("empty-crm", root=target, register=False, yes=True)
    assert result.declined is False
    assert result.seed_bootstrap_count == 0
    assert not (target / "seed.json").exists()
    entities_path = target / "entities.json"
    if entities_path.is_file():
        payload = json.loads(entities_path.read_text(encoding="utf-8"))
        assert len(payload.get("entities", {})) == 0
    assert (target / "network.json").is_file()
    assert (target / "guide.md").is_file()


@pytest.mark.smoke
def test_refresh_crm_imports_seed_into_entities(tmp_path: Path) -> None:
    target = tmp_path / "crm-live"
    result = refresh_example_network("crm", root=target, register=False, yes=True)
    assert result.declined is False
    assert result.seed_bootstrap_count == 15

    entities_path = target / "entities.json"
    assert entities_path.is_file()
    payload = json.loads(entities_path.read_text(encoding="utf-8"))
    assert len(payload["entities"]) == 15
    assert len(payload["bind_index"]) == 15


@pytest.mark.smoke
def test_import_seed_file_idempotent(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seed = tmp_path / "seed.json"
    shutil.copy(EXAMPLE_CRM / "seed.json", seed)
    entities = tmp_path / "entities.json"
    monkeypatch.setenv("MYCELIUM_NETWORK_ROOT", str(tmp_path))
    monkeypatch.setenv("MYCELIUM_ENTITIES_PATH", str(entities))
    reset_entity_registry()

    first_count = import_seed_file(seed)
    payload_after_first = json.loads(entities.read_text(encoding="utf-8"))
    reset_entity_registry()
    second_count = import_seed_file(seed)
    payload_after_second = json.loads(entities.read_text(encoding="utf-8"))

    assert first_count == 15
    assert second_count == 15
    assert len(payload_after_first["entities"]) == 15
    assert payload_after_first == payload_after_second


@pytest.mark.smoke
def test_import_seed_file_missing_returns_zero(tmp_path: Path) -> None:
    assert import_seed_file(tmp_path / "missing-seed.json") == 0


@pytest.mark.smoke
def test_refresh_replaces_existing_root(tmp_path: Path) -> None:
    target = tmp_path / "crm-live"
    target.mkdir()
    (target / "categories.json").write_text('{"stale": true}', encoding="utf-8")
    (target / "agents").mkdir()
    (target / "agents" / "junk.json").write_text("{}", encoding="utf-8")
    (target / "specialists").mkdir()
    (target / "specialists" / "stale_specialist.py").write_text("# stale", encoding="utf-8")

    result = refresh_example_network("crm", root=target, register=False, yes=True)
    assert result.wiped is True
    assert (target / "seed.json").is_file()
    assert not (target / "categories.json").exists()
    assert not (target / "agents").exists()
    assert not (target / "specialists").exists()


@pytest.mark.smoke
def test_refresh_decline_without_yes(tmp_path: Path) -> None:
    target = tmp_path / "crm-live"
    target.mkdir()
    marker = target / "keep-me.txt"
    marker.write_text("stay", encoding="utf-8")

    result = refresh_example_network(
        "crm",
        root=target,
        register=False,
        input_fn=lambda _prompt: "n",
    )
    assert result.declined is True
    assert marker.read_text(encoding="utf-8") == "stay"
    assert not (target / "seed.json").exists()


@pytest.mark.smoke
def test_refresh_decline_via_subprocess(tmp_path: Path) -> None:
    target = tmp_path / "crm-live"
    target.mkdir()
    marker = target / "keep-me.txt"
    marker.write_text("stay", encoding="utf-8")

    result = _run_refresh(
        "crm",
        "--root",
        str(target),
        "--no-register",
        input_text="n\n",
    )
    assert result.returncode == 0, result.stderr or result.stdout
    assert marker.read_text(encoding="utf-8") == "stay"
    assert "Skipped refresh" in result.stdout


@pytest.mark.smoke
def test_refresh_crm_registers_as_default(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    config = tmp_path / "networks.json"
    monkeypatch.setenv("MYCELIUM_NETWORKS_CONFIG", str(config))
    target = tmp_path / "crm-live"

    result = refresh_example_network("crm", root=target, yes=True)
    assert result.registered is True
    assert result.is_default is True
    entries = list_networks()
    assert len(entries) == 1
    assert entries[0].name == "crm"
    assert entries[0].default is True


@pytest.mark.smoke
def test_refresh_dry_run_without_yes_leaves_root_unchanged(tmp_path: Path) -> None:
    target = tmp_path / "crm-live"
    target.mkdir()
    sentinel = target / "stale.json"
    sentinel.write_text("{}", encoding="utf-8")

    def _must_not_prompt(_prompt: str) -> str:
        raise AssertionError("should not prompt")

    result = refresh_example_network(
        "crm",
        root=target,
        register=False,
        dry_run=True,
        input_fn=_must_not_prompt,
    )
    assert result.declined is False
    assert result.dry_run is True
    assert sentinel.read_text(encoding="utf-8") == "{}"
    assert not (target / "seed.json").exists()


@pytest.mark.smoke
def test_refresh_dry_run(tmp_path: Path) -> None:
    target = tmp_path / "crm-live"
    target.mkdir()
    (target / "stale.json").write_text("{}", encoding="utf-8")

    result = _run_refresh("crm", "--root", str(target), "--dry-run", "--yes")
    assert result.returncode == 0, result.stderr or result.stdout
    assert "Would refresh" in result.stdout
    assert "Would wipe" in result.stdout
    assert (target / "stale.json").is_file()
    assert not (target / "seed.json").exists()


@pytest.mark.smoke
def test_refresh_crm_no_default_on_empty_registry(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    config = tmp_path / "networks.json"
    monkeypatch.setenv("MYCELIUM_NETWORKS_CONFIG", str(config))
    target = tmp_path / "crm-live"

    result = refresh_example_network("crm", root=target, yes=True, no_default=True)
    assert result.registered is True
    assert result.is_default is False
    entries = list_networks()
    assert len(entries) == 1
    assert entries[0].default is False


@pytest.mark.smoke
def test_refresh_non_crm_example_auto_defaults(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    framework = tmp_path / "framework"
    example = framework / "examples" / "networks" / "fleet"
    example.mkdir(parents=True)
    shutil.copy(EXAMPLE_CRM / "seed.json", example / "seed.json")
    (example / "network.json").write_text(
        json.dumps({"name": "fleet", "display_name": "Fleet example"}),
        encoding="utf-8",
    )
    monkeypatch.setenv("MYCELIUM_FRAMEWORK_ROOT", str(framework))
    config = tmp_path / "networks.json"
    monkeypatch.setenv("MYCELIUM_NETWORKS_CONFIG", str(config))
    target = tmp_path / "fleet-live"

    result = refresh_example_network("fleet", root=target, yes=True)
    assert result.registered is True
    assert result.is_default is True
    entries = list_networks()
    assert entries[0].name == "fleet"
    assert entries[0].default is True
