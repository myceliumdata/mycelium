"""Tests for warehouse capability manifest generation and introspection."""

from __future__ import annotations

import json
import shutil
import sqlite3
from pathlib import Path

import pytest

from network.example import refresh_example_network
from network.introspection import build_network_capabilities
from network.paths import NetworkPaths, apply_network_paths
from network.warehouse_manifest import (
    build_warehouse_manifest,
    introspect_warehouse_tables,
    load_warehouse_domains_config,
    load_warehouse_manifest,
    maybe_write_warehouse_manifest,
    warehouse_manifest_path,
)
from network_helpers import apply_network_paths_monkeypatch


def _write_minimal_lahman_fixture(seed_dir: Path) -> None:
    seed_dir.mkdir(parents=True, exist_ok=True)
    (seed_dir / "Teams.csv").write_text(
        "yearID,lgID,teamID,franchID,name\n"
        "1957,NL,BRO,LAD,Brooklyn Dodgers\n",
        encoding="utf-8",
    )
    (seed_dir / "People.csv").write_text(
        "ID,playerID,nameFirst,nameLast,birthYear,birthMonth,birthDay,debut\n"
        "1,aaronha01,Hank,Aaron,1934,2,5,\n",
        encoding="utf-8",
    )
    (seed_dir / "Appearances.csv").write_text(
        "yearID,teamID,playerID\n"
        "1957,BRO,aaronha01\n",
        encoding="utf-8",
    )
    (seed_dir / "Batting.csv").write_text(
        "playerID,yearID,stint,teamID,lgID,G,AB,R,H,2B,3B,HR,RBI,SB,CS,BB,SO,IBB,HBP,SH,SF,GIDP\n"
        "aaronha01,1957,1,BRO,NL,1,4,0,2,0,0,1,1,0,0,0,0,0,0,0,0,0\n",
        encoding="utf-8",
    )


def _refresh_baseball_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    fixture_csv = tmp_path / "lahman-fixture" / "lahman_1871-2025_csv"
    _write_minimal_lahman_fixture(fixture_csv)
    root = tmp_path / "baseball-live"

    def fake_fetch(network_root: Path, *, progress=None) -> str:
        dest = network_root / "seed" / "lahman_1871-2025_csv"
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(fixture_csv, dest)
        return "lahman-seed@v2025.1"

    monkeypatch.setattr("network.example.fetch_example_seed", fake_fetch)
    refresh_example_network("baseball", root=root, register=False, yes=True)
    paths = NetworkPaths.from_root(root)
    apply_network_paths_monkeypatch(paths, monkeypatch)
    return root


def test_load_warehouse_domains_config_baseball_pack() -> None:
    config = load_warehouse_domains_config("baseball")
    assert config is not None
    domains = config["domains"]
    assert set(domains) == {"batting", "bio", "pitching", "team_season"}
    assert domains["batting"]["specialist"] == "batting_specialist"
    assert domains["batting"]["tables"] == ["Batting"]


def test_introspect_warehouse_tables(tmp_path: Path) -> None:
    db = tmp_path / "test.sqlite"
    conn = sqlite3.connect(db)
    conn.execute('CREATE TABLE "Batting" (playerID TEXT, HR TEXT)')
    conn.execute('INSERT INTO "Batting" VALUES ("a", "1"), ("b", "2")')
    conn.commit()
    conn.close()

    tables = introspect_warehouse_tables(db, ["Batting", "Missing"])
    assert "Batting" in tables
    assert "Missing" not in tables
    assert tables["Batting"]["columns"] == ["playerID", "HR"]
    assert tables["Batting"]["row_count"] == 2


def test_manifest_written_on_baseball_refresh(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _refresh_baseball_root(tmp_path, monkeypatch)
    paths = NetworkPaths.from_root(root)
    manifest_path = warehouse_manifest_path(paths)
    assert manifest_path.is_file()

    manifest = load_warehouse_manifest(paths)
    assert manifest is not None
    assert manifest["version"] == "1.0"
    assert manifest["dataset"]["id"] == "lahman"
    assert manifest["dataset"]["warehouse"] == "warehouse/lahman.sqlite"
    assert manifest["dataset"]["ref"] == "v2025.1"
    assert "retrieved_from" in manifest["dataset"]

    domains = manifest["domains"]
    assert domains["batting"]["specialist"] == "batting_specialist"
    assert domains["bio"]["tables"] == ["People"]

    tables = manifest["tables"]
    assert "Batting" in tables
    assert "People" in tables
    assert "Teams" in tables
    assert "HR" in tables["Batting"]["columns"]
    assert tables["Batting"]["row_count"] == 1


def test_maybe_write_warehouse_manifest_idempotent(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _refresh_baseball_root(tmp_path, monkeypatch)
    paths = NetworkPaths.from_root(root)
    manifest_path = warehouse_manifest_path(paths)
    first = manifest_path.read_text(encoding="utf-8")

    assert maybe_write_warehouse_manifest(paths)
    second = manifest_path.read_text(encoding="utf-8")
    assert json.loads(first) == json.loads(second)


def test_build_network_capabilities_includes_manifest_summary(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _refresh_baseball_root(tmp_path, monkeypatch)
    paths = NetworkPaths.from_root(root)
    apply_network_paths(paths)

    caps = build_network_capabilities()
    summary = caps.get("warehouse_manifest")
    assert summary is not None
    assert summary["present"] is True
    assert summary["dataset_id"] == "lahman"
    assert "batting" in summary["domains"]
    assert "Batting" in summary["tables"]
    assert summary["path"] == "warehouse_manifest.json"


def test_build_warehouse_manifest_merges_domains_and_introspection(
    tmp_path: Path,
) -> None:
    root = tmp_path / "net"
    root.mkdir()
    repo_root = Path(__file__).resolve().parent.parent
    shutil.copy(repo_root / "examples/networks/baseball/network.json", root / "network.json")
    (root / "seed.source.json").write_text(
        json.dumps(
            {
                "type": "git",
                "repo": "https://github.com/myceliumdata/lahman-seed.git",
                "ref": "v2025.1",
                "dataset_id": "lahman",
            },
        )
        + "\n",
        encoding="utf-8",
    )
    warehouse = root / "warehouse" / "lahman.sqlite"
    warehouse.parent.mkdir(parents=True)
    conn = sqlite3.connect(warehouse)
    conn.execute('CREATE TABLE "People" (playerID TEXT, birthYear TEXT)')
    conn.execute('INSERT INTO "People" VALUES ("x", "2000")')
    conn.commit()
    conn.close()

    paths = NetworkPaths.from_root(root)
    domains_config = load_warehouse_domains_config("baseball")
    assert domains_config is not None
    manifest = build_warehouse_manifest(paths, domains_config=domains_config)
    assert manifest["dataset"]["version"] == "v2025.1"
    assert "People" in manifest["tables"]
    assert manifest["tables"]["People"]["row_count"] == 1
