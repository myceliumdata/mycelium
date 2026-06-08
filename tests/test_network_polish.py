"""Smoke tests for Networks polish (health_check metadata, missing seed, etc.)."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from agents.seed import get_seed_data, reset_seed_data
from network.paths import NetworkPaths, apply_network_paths, legacy_network_root, network_metadata

REPO_ROOT = Path(__file__).resolve().parent.parent
EXAMPLE_CRM = REPO_ROOT / "examples" / "networks" / "crm"


@pytest.mark.smoke
def test_network_metadata_from_example_crm() -> None:
    meta = network_metadata(root=EXAMPLE_CRM)
    assert meta["network_root"] == str(EXAMPLE_CRM.resolve())
    assert meta["network_name"] == "crm"
    assert meta["network_display_name"] == "CRM example"


@pytest.mark.smoke
def test_legacy_network_root_uses_framework_root(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    framework = tmp_path / "framework"
    framework.mkdir()
    monkeypatch.setenv("MYCELIUM_FRAMEWORK_ROOT", str(framework))
    assert legacy_network_root() == (framework / "data").resolve()


@pytest.mark.smoke
def test_network_health_info_unconfigured_hint(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    framework = tmp_path / "framework"
    framework.mkdir()
    monkeypatch.delenv("MYCELIUM_NETWORK_ROOT", raising=False)
    monkeypatch.delenv("MYCELIUM_NETWORK", raising=False)
    monkeypatch.setenv("MYCELIUM_FRAMEWORK_ROOT", str(framework))
    monkeypatch.setenv("MYCELIUM_NETWORKS_CONFIG", str(tmp_path / "missing.json"))

    from mycelium_mcp.server import _network_health_info

    info = _network_health_info()
    assert info["network_root"] is None
    assert info["network_display_name"] is None
    assert "refresh-example-network" in (info.get("network_configure_hint") or "")


@pytest.mark.smoke
def test_health_check_includes_configure_hint_when_unconfigured(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    framework = tmp_path / "framework"
    framework.mkdir()
    monkeypatch.delenv("MYCELIUM_NETWORK_ROOT", raising=False)
    monkeypatch.delenv("MYCELIUM_NETWORK", raising=False)
    monkeypatch.setenv("MYCELIUM_FRAMEWORK_ROOT", str(framework))
    monkeypatch.setenv("MYCELIUM_NETWORKS_CONFIG", str(tmp_path / "missing.json"))

    from mycelium_mcp.server import health_check

    payload = json.loads(health_check())
    hint = payload["info"].get("network_configure_hint") or ""
    assert payload["info"]["network_root"] is None
    assert "refresh-example-network" in hint


@pytest.mark.smoke
def test_health_check_includes_network_metadata(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    net_root = tmp_path / "crm_copy"
    shutil.copytree(
        EXAMPLE_CRM,
        net_root,
        ignore=shutil.ignore_patterns("prepare_seed.py"),
    )
    monkeypatch.setenv("MYCELIUM_NETWORK_ROOT", str(net_root))
    monkeypatch.delenv("MYCELIUM_NETWORK", raising=False)
    monkeypatch.setenv("MYCELIUM_NETWORKS_CONFIG", str(tmp_path / "missing.json"))

    from mycelium_mcp.server import health_check

    payload = json.loads(health_check())
    info = payload["info"]
    assert info["network_root"] == str(net_root.resolve())
    assert info["network_name"] == "crm"
    assert info["network_display_name"] == "CRM example"


@pytest.mark.smoke
def test_missing_seed_raises_file_not_found(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    empty_root = tmp_path / "empty_data"
    empty_root.mkdir()
    monkeypatch.setenv("MYCELIUM_NETWORKS_CONFIG", str(tmp_path / "missing.json"))
    paths = NetworkPaths.from_root(empty_root)
    apply_network_paths(paths)
    reset_seed_data()
    with pytest.raises(FileNotFoundError, match="Seed file not found"):
        get_seed_data()


@pytest.mark.smoke
def test_example_crm_seed_has_sanitized_employers() -> None:
    payload = json.loads((EXAMPLE_CRM / "seed.json").read_text(encoding="utf-8"))
    for person in payload["people"]:
        employer = person.get("employer") or ""
        assert "[" not in employer
        assert "Contacts Valuable" not in employer
