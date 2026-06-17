"""Smoke tests for closed-world identity grains and lazy field alias expansion."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from agents.entity_registry import RegistryEntity, get_entity_registry, reset_entity_registry
from agents.target_resolve import resolve_target_step1
from models.state import EntityQuery
from network.mvr import is_closed_identity_grain
from network.paths import NetworkPaths, apply_network_paths

REPO_ROOT = Path(__file__).resolve().parent.parent
BASEBALL_MANIFEST = REPO_ROOT / "examples" / "networks" / "baseball" / "network.json"
CRM_MANIFEST = REPO_ROOT / "examples" / "networks" / "crm" / "network.json"
CRM_SEED = REPO_ROOT / "examples" / "networks" / "crm" / "seed.json"


def _prepare_baseball_team_registry(tmp_path: Path) -> NetworkPaths:
    root = tmp_path / "baseball"
    root.mkdir()
    shutil.copy(BASEBALL_MANIFEST, root / "network.json")
    shutil.copy(REPO_ROOT / "examples" / "networks" / "baseball" / "guide.md", root / "guide.md")
    paths = NetworkPaths.from_root(root)
    apply_network_paths(paths)
    reset_entity_registry()

    team = get_entity_registry(grain="team")
    yankees = RegistryEntity(
        id="team-yankees",
        bind_values={"name": "New York Yankees"},
        source="test",
        created_at="2026-06-17T12:00:00+00:00",
    )
    brooklyn = RegistryEntity(
        id="team-brooklyn",
        bind_values={"name": "Brooklyn Dodgers"},
        source="test",
        created_at="2026-06-17T12:00:00+00:00",
    )
    los_angeles = RegistryEntity(
        id="team-la",
        bind_values={"name": "Los Angeles Dodgers"},
        source="test",
        created_at="2026-06-17T12:00:00+00:00",
    )
    for entity in (yankees, brooklyn, los_angeles):
        team.register_entity(entity)
        team.assign_bind_index(entity.id, entity.bind_values)
        team.save_entity(entity)
    return paths


def _mock_team_alias_expander(
    grain: str,
    field: str,
    query_value: str,
    registry,
    guide_text: str | None,
) -> list[str]:
    _ = grain, field, guide_text
    if query_value == "Bronx Bombers":
        entity = registry.lookup_by_bind_values({"name": "New York Yankees"})
        return [entity.id] if entity is not None else []
    if query_value == "Dodgers":
        return ["team-brooklyn", "team-la"]
    return []


@pytest.mark.smoke
def test_baseball_manifest_declares_closed_grains(tmp_path: Path) -> None:
    shutil.copy(BASEBALL_MANIFEST, tmp_path / "network.json")
    paths = NetworkPaths.from_root(tmp_path)
    assert is_closed_identity_grain("team", paths=paths)
    assert is_closed_identity_grain("player", paths=paths)
    assert not is_closed_identity_grain("person", paths=paths)


@pytest.mark.smoke
def test_closed_team_bronx_bombers_resolves_via_mock_expander(tmp_path: Path) -> None:
    _prepare_baseball_team_registry(tmp_path)
    result = resolve_target_step1(
        EntityQuery(lookup={"name": "Bronx Bombers"}),
        grain="team",
        alias_expander=_mock_team_alias_expander,
    )
    assert result.kind == "resolved"
    assert result.entity_ids == ["team-yankees"]
    assert result.create_on_deliver is False

    team = get_entity_registry(grain="team")
    assert team.lookup_by_target_lookup({"name": "Bronx Bombers"}) == ["team-yankees"]


@pytest.mark.smoke
def test_closed_team_dodgers_mock_returns_multi_match(tmp_path: Path) -> None:
    _prepare_baseball_team_registry(tmp_path)
    result = resolve_target_step1(
        EntityQuery(lookup={"name": "Dodgers"}),
        grain="team",
        alias_expander=_mock_team_alias_expander,
    )
    assert result.kind == "resolved"
    assert sorted(result.entity_ids) == ["team-brooklyn", "team-la"]


@pytest.mark.smoke
def test_closed_team_unknown_nickname_not_create_pending(tmp_path: Path) -> None:
    _prepare_baseball_team_registry(tmp_path)
    result = resolve_target_step1(
        EntityQuery(lookup={"name": "XYZZY"}),
        grain="team",
        alias_expander=_mock_team_alias_expander,
    )
    assert result.kind != "create_pending"
    assert result.create_on_deliver is False
    assert result.kind in {"not_found", "lookup_suggested"}


@pytest.mark.smoke
def test_crm_open_grain_still_create_pending(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from network_helpers import import_seed_for_test

    shutil.copy(CRM_MANIFEST, tmp_path / "network.json")
    monkeypatch.setenv("MYCELIUM_NETWORK_ROOT", str(tmp_path))
    import_seed_for_test(
        seed_src=CRM_SEED,
        tmp_path=tmp_path,
        monkeypatch=monkeypatch,
    )
    reset_entity_registry()
    result = resolve_target_step1(
        EntityQuery(lookup={"name": "Road Runner", "employer": "Acme Corp"}),
    )
    assert result.kind == "create_pending"
    assert result.create_on_deliver is True
