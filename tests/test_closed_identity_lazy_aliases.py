"""Smoke tests for bootstrap-only record types and lazy field alias expansion."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from agents.bind_alias_expansion import _alias_expansion_example_lines
from agents.entity_registry import RegistryEntity, get_entity_registry, reset_entity_registry
from agents.target_resolve import resolve_target_step1
from models.state import EntityQuery
from network.mvr import is_bootstrap_only_record_type
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

    team = get_entity_registry(record_type="team")
    yankees = RegistryEntity(
        id="team-yankees",
        bind_values={"team": "New York Yankees"},
        source="test",
        created_at="2026-06-17T12:00:00+00:00",
    )
    brooklyn = RegistryEntity(
        id="team-brooklyn",
        bind_values={"team": "Brooklyn Dodgers"},
        source="test",
        created_at="2026-06-17T12:00:00+00:00",
    )
    los_angeles = RegistryEntity(
        id="team-la",
        bind_values={"team": "Los Angeles Dodgers"},
        source="test",
        created_at="2026-06-17T12:00:00+00:00",
    )
    boston = RegistryEntity(
        id="team-bos",
        bind_values={"team": "Boston Red Sox"},
        source="test",
        created_at="2026-06-17T12:00:00+00:00",
    )
    cleveland = RegistryEntity(
        id="team-cle",
        bind_values={"team": "Cleveland Red Sox"},
        source="test",
        created_at="2026-06-17T12:00:00+00:00",
    )
    nationals = RegistryEntity(
        id="team-was",
        bind_values={"team": "Washington Nationals"},
        source="test",
        created_at="2026-06-17T12:00:00+00:00",
    )
    mets = RegistryEntity(
        id="team-nym",
        bind_values={"team": "New York Mets"},
        source="test",
        created_at="2026-06-17T12:00:00+00:00",
    )
    for entity in (yankees, brooklyn, los_angeles, boston, cleveland, nationals, mets):
        team.register_entity(entity)
        team.assign_bind_index(entity.id, entity.bind_values)
        team.save_entity(entity)
    return paths


def _mock_team_alias_expander(
    record_type: str,
    field: str,
    query_value: str,
    registry,
    guide_text: str | None,
) -> list[str]:
    _ = record_type, field, registry, guide_text
    if query_value == "Bronx Bombers":
        return ["New York Yankees"]
    if query_value == "Dodgers":
        return ["Brooklyn Dodgers", "Los Angeles Dodgers"]
    if query_value == "The Miracle Mets":
        return ["New York Mets"]
    return []


@pytest.mark.smoke
def test_alias_expansion_example_lines_vary_by_record_type() -> None:
    team_examples = "\n".join(_alias_expansion_example_lines("team", "team"))
    player_examples = "\n".join(_alias_expansion_example_lines("player", "player"))
    assert "Dodgers" in team_examples
    assert "Washington Red Sox" in team_examples
    assert "Dodgers" not in player_examples
    assert "Say Hey Kid" in player_examples
    assert _alias_expansion_example_lines("person", "name") == []


@pytest.mark.smoke
def test_baseball_manifest_declares_bootstrap_only_record_types(tmp_path: Path) -> None:
    shutil.copy(BASEBALL_MANIFEST, tmp_path / "network.json")
    paths = NetworkPaths.from_root(tmp_path)
    assert is_bootstrap_only_record_type("team", paths=paths)
    assert is_bootstrap_only_record_type("player", paths=paths)
    assert not is_bootstrap_only_record_type("person", paths=paths)


@pytest.mark.smoke
def test_closed_team_bronx_bombers_resolves_via_mock_expander(tmp_path: Path) -> None:
    _prepare_baseball_team_registry(tmp_path)
    result = resolve_target_step1(
        EntityQuery(lookup={"team": "Bronx Bombers"}),
        alias_expander=_mock_team_alias_expander,
    )
    assert result.kind == "resolved"
    assert result.entity_ids == ["team-yankees"]
    assert result.create_on_deliver is False

    team = get_entity_registry(record_type="team")
    assert team.lookup_by_target_lookup({"team": "Bronx Bombers"}) == ["team-yankees"]


@pytest.mark.smoke
def test_closed_team_dodgers_mock_returns_multi_match(tmp_path: Path) -> None:
    _prepare_baseball_team_registry(tmp_path)
    result = resolve_target_step1(
        EntityQuery(lookup={"team": "Dodgers"}),
        alias_expander=_mock_team_alias_expander,
    )
    assert result.kind == "resolved"
    assert sorted(result.entity_ids) == ["team-brooklyn", "team-la"]


@pytest.mark.smoke
def test_closed_team_unknown_nickname_not_create_pending(tmp_path: Path) -> None:
    _prepare_baseball_team_registry(tmp_path)
    result = resolve_target_step1(
        EntityQuery(lookup={"team": "XYZZY"}),
        alias_expander=_mock_team_alias_expander,
    )
    assert result.kind != "create_pending"
    assert result.create_on_deliver is False
    assert result.kind in {"not_found", "lookup_suggested"}


@pytest.mark.smoke
def test_closed_team_mashup_writes_no_aliases(tmp_path: Path) -> None:
    _prepare_baseball_team_registry(tmp_path)
    result = resolve_target_step1(
        EntityQuery(lookup={"team": "Washington Red Sox"}),
        alias_expander=_mock_team_alias_expander,
    )
    assert result.kind == "not_found"
    team = get_entity_registry(record_type="team")
    for entity_id in ("team-cle", "team-was"):
        entity = team.lookup_by_id(entity_id)
        assert entity is not None
        assert "Washington Red Sox" not in (entity.field_aliases.get("team") or [])


@pytest.mark.smoke
def test_closed_team_boston_red_sox_exact_without_expander(tmp_path: Path) -> None:
    _prepare_baseball_team_registry(tmp_path)

    def _fail_if_called(*_args, **_kwargs) -> list[str]:
        pytest.fail("alias expander must not run on exact canonical bind hit")

    result = resolve_target_step1(
        EntityQuery(lookup={"team": "Boston Red Sox"}),
        alias_expander=_fail_if_called,
    )
    assert result.kind == "resolved"
    assert result.entity_ids == ["team-bos"]


@pytest.mark.smoke
def test_closed_team_miracle_mets_resolves_via_mock_expander(tmp_path: Path) -> None:
    _prepare_baseball_team_registry(tmp_path)
    result = resolve_target_step1(
        EntityQuery(lookup={"team": "The Miracle Mets"}),
        alias_expander=_mock_team_alias_expander,
    )
    assert result.kind == "resolved"
    assert result.entity_ids == ["team-nym"]


@pytest.mark.smoke
def test_crm_query_allowed_record_type_still_create_pending(
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
