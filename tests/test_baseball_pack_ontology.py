"""Smoke tests for committed baseball pack ontology install and classification routing."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from agents.classification import get_category_tree, reset_category_tree
from agents.classification.models import CategoryTreeData
from network.example import refresh_example_network
from network.pack_ontology import install_pack_ontology_from_example, is_pack_ontology
from network.paths import NetworkPaths, apply_network_paths

REPO_ROOT = Path(__file__).resolve().parent.parent
BASEBALL_PACK = REPO_ROOT / "examples" / "networks" / "baseball" / "categories.json"
EXAMPLE_CRM = REPO_ROOT / "examples" / "networks" / "crm-seeded"


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
        "aaronha01,1957,1,BRO,NL,1,4,0,2,0,0,1,1,0,0,0,0,0,0,0,0,0\n"
        "aaronha01,1958,1,LAN,NL,1,4,0,2,0,0,2,2,0,0,0,0,0,0,0,0,0\n",
        encoding="utf-8",
    )


@pytest.mark.smoke
def test_baseball_pack_categories_validates() -> None:
    raw = json.loads(BASEBALL_PACK.read_text(encoding="utf-8"))
    tree = CategoryTreeData.model_validate(raw)
    assert tree.ontology_pack == "baseball"
    assert tree.attribute_map["career_hr"] == "batting"
    assert tree.attribute_map["team"] == "team_identity"


@pytest.mark.smoke
def test_refresh_baseball_installs_pack_ontology(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture_csv = tmp_path / "lahman-fixture" / "lahman_1871-2025_csv"
    _write_minimal_lahman_fixture(fixture_csv)
    target = tmp_path / "baseball-live"

    def fake_fetch(network_root: Path, *, progress=None) -> str:
        dest = network_root / "seed" / "lahman_1871-2025_csv"
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(fixture_csv, dest)
        return "lahman-seed@v2025.1"

    monkeypatch.setattr("network.example.fetch_example_seed", fake_fetch)
    refresh_example_network("baseball", root=target, register=False, yes=True)

    categories_path = target / "categories.json"
    assert categories_path.is_file()
    assert is_pack_ontology(categories_path)
    data = json.loads(categories_path.read_text(encoding="utf-8"))
    assert data.get("ontology_pack") == "baseball"
    assert data["attribute_map"]["team"] == "team_identity"


@pytest.mark.smoke
def test_baseball_attribute_classification_routing(tmp_path: Path) -> None:
    target = tmp_path / "baseball-root"
    shutil.copytree(
        REPO_ROOT / "examples" / "networks" / "baseball",
        target,
        ignore=shutil.ignore_patterns("seed", "bootstrap_handlers"),
    )
    paths = NetworkPaths.from_root(target)
    apply_network_paths(paths)
    assert install_pack_ontology_from_example("baseball", paths)

    reset_category_tree()
    tree = get_category_tree()

    career = tree.classify("career_hr")
    assert career.category == "batting"
    assert career.assigned_agent == "batting_specialist"

    birth = tree.classify("birth_date")
    assert birth.category == "bio"
    assert birth.assigned_agent == "bio_specialist"

    team = tree.classify("team")
    assert team.category == "team_identity"
    assert team.assigned_agent == "team_identity_specialist"
    assert team.category != "professional"


@pytest.mark.smoke
def test_crm_refresh_still_uses_crm_taxonomy(tmp_path: Path) -> None:
    target = tmp_path / "crm-live"
    refresh_example_network("crm-seeded", root=target, register=False, yes=True)
    categories_path = target / "categories.json"
    assert categories_path.is_file()
    assert not is_pack_ontology(categories_path)
    data = json.loads(categories_path.read_text(encoding="utf-8"))
    assert data.get("ontology_pack") in (None, "")
    assert data["attribute_map"]["employer"] == "professional"
    assert "team_identity" not in data.get("categories", {})
