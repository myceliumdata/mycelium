"""Smoke tests for composite fuzzy bind-field similarity scoring."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from agents.entity_registry import RegistryEntity, get_entity_registry, reset_entity_registry
from agents.entity_resolution import (
    PREFIX_SHORTHAND_SCORE,
    SUGGESTION_MIN_SCORE,
    _LAST_TOKEN_ANCHOR_MIN_SCORE,
    _rank_bind_field_fuzzy_suggestions,
    fuzzy_bind_field_similarity,
    normalize_name_for_comparison,
)
from agents.target_resolve import resolve_target_step1
from models.state import EntityQuery
from network.paths import NetworkPaths
from network_helpers import apply_network_paths_monkeypatch, clear_network_path_env

REPO_ROOT = Path(__file__).resolve().parent.parent
BASEBALL_MANIFEST = REPO_ROOT / "examples" / "networks" / "baseball" / "network.json"


@pytest.mark.smoke
@pytest.mark.parametrize(
    ("query", "candidate", "expected_min"),
    [
        ("andrea kalman", "andrea kalmans", 0.85),
        ("645 ventures", "645 ventures", 1.0),
        ("645 venture", "645 ventures", 0.85),
        ("645", "645 ventures", PREFIX_SHORTHAND_SCORE),
        ("ibm", "ibm corporation", PREFIX_SHORTHAND_SCORE),
        ("tie cobb", "ty cobb", 0.85),
    ],
)
def test_fuzzy_bind_field_similarity_positive(
    query: str,
    candidate: str,
    expected_min: float,
) -> None:
    score = fuzzy_bind_field_similarity(query, candidate)
    assert score is not None
    assert score >= expected_min


@pytest.mark.smoke
@pytest.mark.parametrize(
    ("query", "candidate"),
    [
        ("john cobb", "ty cobb"),
        ("dodgers", "brooklyn dodgers"),
    ],
)
def test_fuzzy_bind_field_similarity_rejects(query: str, candidate: str) -> None:
    score = fuzzy_bind_field_similarity(query, candidate)
    if score is not None:
        assert score < SUGGESTION_MIN_SCORE


@pytest.mark.smoke
def test_prefix_shorthand_returns_fixed_score() -> None:
    score = fuzzy_bind_field_similarity("645", "645 Ventures")
    assert score == PREFIX_SHORTHAND_SCORE


@pytest.mark.smoke
def test_last_token_anchor_accepts_levenshtein_two() -> None:
    score = fuzzy_bind_field_similarity("Tie Cobb", "Ty Cobb")
    assert score is not None
    assert score >= _LAST_TOKEN_ANCHOR_MIN_SCORE


@pytest.mark.smoke
def test_last_token_anchor_rejects_levenshtein_three() -> None:
    score = fuzzy_bind_field_similarity("Tie Coebb", "Ty Cobb")
    assert score is None or score < SUGGESTION_MIN_SCORE


@pytest.mark.smoke
def test_normalize_name_for_comparison_matches_field_index() -> None:
    from agents.field_index import normalize_field_index_value

    raw = "  O'Brien-Smith  "
    assert normalize_name_for_comparison(raw) == normalize_field_index_value(raw)


@pytest.mark.smoke
def test_rank_bind_field_fuzzy_suggestions_645_prefix(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import shutil

    repo = Path(__file__).resolve().parent.parent
    root = tmp_path / "crm-fuzzy"
    root.mkdir()
    shutil.copy(repo / "examples" / "networks" / "crm" / "network.json", root / "network.json")
    paths = NetworkPaths.from_root(root)
    clear_network_path_env(monkeypatch)
    apply_network_paths_monkeypatch(paths, monkeypatch)
    reset_entity_registry()

    registry = get_entity_registry()
    row = RegistryEntity(
        id="emp-645",
        bind_values={"name": "Jane Doe", "employer": "645 Ventures"},
        source="test",
        created_at="2026-06-18T12:00:00+00:00",
    )
    registry.register_entity(row)
    registry.assign_bind_index(row.id, row.bind_values)
    registry.save_entity(row)

    suggestions = _rank_bind_field_fuzzy_suggestions("employer", "645")
    assert suggestions
    assert suggestions[0].suggested_lookup == {"employer": "645 Ventures"}
    assert suggestions[0].reason == "fuzzy_bind_field_match"
    assert suggestions[0].score == PREFIX_SHORTHAND_SCORE


@pytest.mark.smoke
def test_tie_cobb_partial_player_lookup_suggested(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "baseball"
    root.mkdir()
    shutil.copy(BASEBALL_MANIFEST, root / "network.json")
    shutil.copy(REPO_ROOT / "examples" / "networks" / "baseball" / "guide.md", root / "guide.md")
    paths = NetworkPaths.from_root(root)
    clear_network_path_env(monkeypatch)
    apply_network_paths_monkeypatch(paths, monkeypatch)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    reset_entity_registry()

    player = get_entity_registry(record_type="player")
    row = RegistryEntity(
        id="player-cobb",
        bind_values={
            "player": "Ty Cobb",
            "debut_team": "Detroit Tigers",
            "debut_year": "1905",
        },
        source="test",
        created_at="2026-06-17T12:00:00+00:00",
    )
    player.register_entity(row)
    player.assign_bind_index(row.id, row.bind_values)
    player.save_entity(row)

    result = resolve_target_step1(EntityQuery(lookup={"player": "Tie Cobb"}))
    assert result.kind == "lookup_suggested"
    assert result.suggestions
    assert result.suggestions[0].suggested_lookup == {"player": "Ty Cobb"}
    assert result.suggestions[0].reason == "fuzzy_bind_field_match"


@pytest.mark.smoke
def test_john_cobb_partial_player_not_suggested(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "baseball"
    root.mkdir()
    shutil.copy(BASEBALL_MANIFEST, root / "network.json")
    shutil.copy(REPO_ROOT / "examples" / "networks" / "baseball" / "guide.md", root / "guide.md")
    paths = NetworkPaths.from_root(root)
    clear_network_path_env(monkeypatch)
    apply_network_paths_monkeypatch(paths, monkeypatch)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    reset_entity_registry()

    player = get_entity_registry(record_type="player")
    row = RegistryEntity(
        id="player-cobb",
        bind_values={
            "player": "Ty Cobb",
            "debut_team": "Detroit Tigers",
            "debut_year": "1905",
        },
        source="test",
        created_at="2026-06-17T12:00:00+00:00",
    )
    player.register_entity(row)
    player.assign_bind_index(row.id, row.bind_values)
    player.save_entity(row)

    result = resolve_target_step1(EntityQuery(lookup={"player": "John Cobb"}))
    assert result.kind == "not_found"
