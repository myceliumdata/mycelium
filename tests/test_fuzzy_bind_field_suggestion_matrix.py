"""Parametric mistake matrix for fuzzy bind-field suggestions (CRM + baseball).

Contract for slice ``2026-06-18-2100-fuzzy-bind-field-suggestion-upgrade``.
Rows document expected step-1 / scorer behavior from hand tests and policy docs.
Shipped — green rows are the regression gate for scorer and resolve changes.
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

import pytest

from agents import entity_resolution
from agents.classification import get_category_tree, reset_category_tree
from agents.context import reset_context_builder
from agents.entity_registry import RegistryEntity, get_entity_registry, reset_entity_registry
from agents.factory.agent_factory import reset_agent_factory
from agents.registry import reset_agent_registry
from agents.target_resolve import resolve_target_step1
from graphs.core import reset_core_graph, run_query
from models.state import EntityQuery
from network.delivery import reset_delivery_store
from network.paths import NetworkPaths, apply_network_paths
from network_helpers import import_seed_for_test
from storage.core import CoreStorage, get_storage, reset_storage

REPO_ROOT = Path(__file__).resolve().parent.parent
SAMPLE_CATEGORIES = REPO_ROOT / "docs" / "examples" / "sample-categories.json"
EXAMPLE_CRM = REPO_ROOT / "examples" / "networks" / "crm-seeded"
EXAMPLE_CRM_SEED = EXAMPLE_CRM / "seed.json"
BASEBALL_MANIFEST = REPO_ROOT / "examples" / "networks" / "baseball" / "network.json"


def _require_scorer():
    fn = getattr(entity_resolution, "fuzzy_bind_field_similarity", None)
    if fn is None:
        pytest.fail(
            "fuzzy_bind_field_similarity not implemented — "
            "complete slice 2026-06-18-2100-fuzzy-bind-field-suggestion-upgrade",
        )
    return fn


@dataclass(frozen=True)
class ScorerMistakeCase:
    """Pair-level scorer contract (normalized strings compared inside helper)."""

    id: str
    query: str
    candidate: str
    should_suggest: bool
    min_score: float | None = None


@dataclass(frozen=True)
class Step1MistakeCase:
    """End-to-end step-1 outcome for a mistaken lookup."""

    id: str
    network: Literal["crm-seeded", "baseball"]
    lookup: dict[str, str]
    expected_kind: str
    expected_outcome: str | None = None
    expected_suggested_lookup: dict[str, str] | None = None
    suggestion_contains: dict[str, str] | None = None
    min_suggestions: int | None = None
    max_suggestions: int | None = None
    use_team_alias_mock: bool = False


# --- Scorer pairs (typos, shorthand, negatives) --------------------------------

SCORER_MISTAKE_CASES: tuple[ScorerMistakeCase, ...] = (
    ScorerMistakeCase("typos.tie_cobb_ty_cobb", "Tie Cobb", "Ty Cobb", True, 0.85),
    ScorerMistakeCase("typos.andrea_kalman", "Andrea Kalman", "Andrea Kalmans", True, 0.85),
    ScorerMistakeCase("typos.hank_aron", "Hank Aron", "Hank Aaron", True, 0.85),
    ScorerMistakeCase("typos.ty_cob", "Ty Cob", "Ty Cobb", True, 0.85),
    ScorerMistakeCase("typos.654_ventures", "654 Ventures", "645 Ventures", True, 0.85),
    ScorerMistakeCase("typos.645_venture", "645 Venture", "645 Ventures", True, 0.85),
    ScorerMistakeCase("prefix.645_shorthand", "645", "645 Ventures", True, 0.85),
    ScorerMistakeCase("prefix.ibm_corp", "ibm", "IBM Corporation", True, 0.85),
    ScorerMistakeCase("negative.john_cobb_ty_cobb", "John Cobb", "Ty Cobb", False, None),
    ScorerMistakeCase("negative.tie_coebb_ty_cobb", "Tie Coebb", "Ty Cobb", False, None),
    ScorerMistakeCase("negative.46_ventures", "46", "645 Ventures", False, None),
    ScorerMistakeCase("negative.645_wrong_prefix", "645", "1645 Ventures", False, None),
    ScorerMistakeCase("negative.dodgers_brooklyn", "Dodgers", "Brooklyn Dodgers", False, None),
    ScorerMistakeCase("negative.york_yankees", "York", "New York Yankees", False, None),
    ScorerMistakeCase("negative.washington_red_sox_boston", "Washington Red Sox", "Boston Red Sox", False, None),
    ScorerMistakeCase("negative.xyzzy_aaron", "XYZZY", "Hank Aaron", False, None),
)

# --- Step-1 matrix (CRM run_query outcome + baseball resolve_target_step1) -------

STEP1_MISTAKE_CASES: tuple[Step1MistakeCase, ...] = (
    # CRM — employer typos / shorthand (hand-test + fuzzy-lookup-policy.md)
    Step1MistakeCase(
        "crm.employer_digit_typo",
        "crm-seeded",
        {"employer": "654 Ventures"},
        "lookup_suggested",
        expected_outcome="lookup_suggested",
        expected_suggested_lookup={"employer": "645 Ventures"},
    ),
    Step1MistakeCase(
        "crm.employer_plural_typo",
        "crm-seeded",
        {"employer": "645 Venture"},
        "lookup_suggested",
        expected_outcome="lookup_suggested",
        expected_suggested_lookup={"employer": "645 Ventures"},
    ),
    Step1MistakeCase(
        "crm.employer_prefix_shorthand",
        "crm-seeded",
        {"employer": "645"},
        "lookup_suggested",
        expected_outcome="lookup_suggested",
        expected_suggested_lookup={"employer": "645 Ventures"},
    ),
    Step1MistakeCase(
        "crm.name_typo",
        "crm-seeded",
        {"name": "Andrea Kalman"},
        "lookup_suggested",
        expected_outcome="lookup_suggested",
        expected_suggested_lookup={"name": "Andrea Kalmans"},
    ),
    Step1MistakeCase(
        "crm.name_only_unknown",
        "crm-seeded",
        {"name": "Paul Murphy"},
        "lookup_incomplete",
        expected_outcome="lookup_incomplete",
    ),
    Step1MistakeCase(
        "crm.employer_exact_multi",
        "crm-seeded",
        {"employer": "645 Ventures"},
        "resolved",
        expected_outcome="lookup_resolved",
    ),
    # Baseball — player typos (bootstrap_only partial)
    Step1MistakeCase(
        "baseball.player_tie_cobb",
        "baseball",
        {"player": "Tie Cobb"},
        "lookup_suggested",
        expected_suggested_lookup={"player": "Ty Cobb"},
    ),
    Step1MistakeCase(
        "baseball.player_ty_cobb_exact",
        "baseball",
        {"player": "Ty Cobb"},
        "resolved",
    ),
    Step1MistakeCase(
        "baseball.player_unknown",
        "baseball",
        {"player": "XYZZY"},
        "not_found",
    ),
    Step1MistakeCase(
        "baseball.player_homonym_last_name",
        "baseball",
        {"player": "John Cobb"},
        "not_found",
    ),
    # Baseball — team exact / mashup / alias path
    Step1MistakeCase(
        "baseball.team_boston_exact",
        "baseball",
        {"team": "Boston Red Sox"},
        "resolved",
    ),
    Step1MistakeCase(
        "baseball.team_mashup",
        "baseball",
        {"team": "Washington Red Sox"},
        "not_found",
    ),
    Step1MistakeCase(
        "baseball.team_partial_red_sox",
        "baseball",
        {"team": "Red Sox"},
        "not_found",
    ),
    Step1MistakeCase(
        "baseball.team_dodgers_alias",
        "baseball",
        {"team": "Dodgers"},
        "resolved",
        use_team_alias_mock=True,
        min_suggestions=None,
    ),
    Step1MistakeCase(
        "baseball.team_bronx_bombers_alias",
        "baseball",
        {"team": "Bronx Bombers"},
        "resolved",
        use_team_alias_mock=True,
        expected_suggested_lookup=None,
    ),
)


@pytest.fixture
def crm_matrix_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> CoreStorage:
    reset_storage()
    reset_entity_registry()
    reset_context_builder()
    reset_core_graph()
    reset_category_tree()
    reset_delivery_store()
    reset_agent_registry()
    reset_agent_factory()

    seed = tmp_path / "seed.json"
    shutil.copy(EXAMPLE_CRM_SEED, seed)
    categories_path = tmp_path / "categories.json"
    shutil.copy(SAMPLE_CATEGORIES, categories_path)
    monkeypatch.setenv("MYCELIUM_NETWORK_ROOT", str(tmp_path))
    shutil.copy(EXAMPLE_CRM / "network.json", tmp_path / "network.json")
    monkeypatch.setenv("MYCELIUM_DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("MYCELIUM_SEED_PATH", str(seed))
    monkeypatch.setenv("MYCELIUM_CHECKPOINT_PATH", str(tmp_path / "cp.sqlite"))
    monkeypatch.setenv("MYCELIUM_CATEGORIES_PATH", str(categories_path))
    monkeypatch.setenv("MYCELIUM_ENTITIES_PATH", str(tmp_path / "entities.json"))
    monkeypatch.setenv("MYCELIUM_DELIVERIES_PATH", str(tmp_path / "deliveries.json"))
    monkeypatch.setenv(
        "MYCELIUM_AGENT_REGISTRY_PATH",
        str(tmp_path / "agent_registry.json"),
    )
    monkeypatch.setenv("MYCELIUM_SPECIALISTS_DIR", str(tmp_path / "specialists"))
    monkeypatch.setenv("MYCELIUM_AGENT_DATA_DIR", str(tmp_path / "agent_data"))
    monkeypatch.setenv("MYCELIUM_USE_SYNC_CHECKPOINTER", "1")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)

    reset_category_tree()
    get_category_tree()
    storage = get_storage()
    import_seed_for_test(seed)
    _ = get_entity_registry()
    reset_core_graph()
    yield storage

    reset_storage()
    reset_entity_registry()
    reset_context_builder()
    reset_core_graph()
    reset_category_tree()
    reset_delivery_store()
    reset_agent_registry()
    reset_agent_factory()


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
    return []


def _prepare_baseball_matrix_registry(tmp_path: Path) -> NetworkPaths:
    root = tmp_path / "baseball-matrix"
    root.mkdir()
    shutil.copy(BASEBALL_MANIFEST, root / "network.json")
    shutil.copy(
        REPO_ROOT / "examples" / "networks" / "baseball" / "guide.md",
        root / "guide.md",
    )
    paths = NetworkPaths.from_root(root)
    apply_network_paths(paths)
    reset_entity_registry()

    team = get_entity_registry(record_type="team")
    teams = (
        ("team-bos", "Boston Red Sox"),
        ("team-cle", "Cleveland Red Sox"),
        ("team-was", "Washington Nationals"),
        ("team-brooklyn", "Brooklyn Dodgers"),
        ("team-la", "Los Angeles Dodgers"),
        ("team-yankees", "New York Yankees"),
    )
    for entity_id, label in teams:
        row = RegistryEntity(
            id=entity_id,
            bind_values={"team": label},
            source="test",
            created_at="2026-06-18T12:00:00+00:00",
        )
        team.register_entity(row)
        team.assign_bind_index(entity_id, row.bind_values)
        team.save_entity(row)

    player = get_entity_registry(record_type="player")
    players = (
        (
            "player-cobb",
            {"player": "Ty Cobb", "debut_team": "Detroit Tigers", "debut_year": "1905"},
        ),
    )
    for entity_id, bind_values in players:
        row = RegistryEntity(
            id=entity_id,
            bind_values=bind_values,
            source="test",
            created_at="2026-06-18T12:00:00+00:00",
        )
        player.register_entity(row)
        player.assign_bind_index(entity_id, row.bind_values)
        player.save_entity(row)

    return paths


def _assert_suggestions(
    suggestions: list[Any],
    case: Step1MistakeCase,
) -> None:
    if case.expected_suggested_lookup is not None:
        assert suggestions, f"{case.id}: expected suggestions"
        top = suggestions[0]
        assert top.suggested_lookup == case.expected_suggested_lookup, (
            f"{case.id}: top suggestion {top.suggested_lookup!r} "
            f"!= {case.expected_suggested_lookup!r}"
        )
        assert top.reason == entity_resolution.FUZZY_BIND_FIELD_REASON, (
            f"{case.id}: reason {top.reason!r} != {entity_resolution.FUZZY_BIND_FIELD_REASON!r}"
        )
    if case.suggestion_contains is not None:
        assert suggestions, f"{case.id}: expected suggestions"
        assert case.suggestion_contains.items() <= suggestions[0].suggested_lookup.items()
    if case.min_suggestions is not None:
        assert len(suggestions) >= case.min_suggestions
    if case.max_suggestions is not None:
        assert len(suggestions) <= case.max_suggestions


@pytest.mark.smoke
@pytest.mark.parametrize(
    "case",
    SCORER_MISTAKE_CASES,
    ids=lambda case: case.id,
)
def test_fuzzy_scorer_mistake_matrix(case: ScorerMistakeCase) -> None:
    scorer = _require_scorer()
    min_score = entity_resolution.SUGGESTION_MIN_SCORE
    score = scorer(case.query, case.candidate)
    if case.should_suggest:
        assert score is not None, f"{case.id}: expected match for {case.query!r} -> {case.candidate!r}"
        assert score >= (case.min_score or min_score), (
            f"{case.id}: score {score} below {(case.min_score or min_score)}"
        )
    else:
        assert score is None or score < min_score, (
            f"{case.id}: unexpected match score={score} for {case.query!r} -> {case.candidate!r}"
        )


CRM_STEP1_CASES = tuple(case for case in STEP1_MISTAKE_CASES if case.network == "crm-seeded")
BASEBALL_STEP1_CASES = tuple(case for case in STEP1_MISTAKE_CASES if case.network == "baseball")


@pytest.mark.smoke
@pytest.mark.parametrize(
    "case",
    CRM_STEP1_CASES,
    ids=lambda case: case.id,
)
def test_fuzzy_step1_crm_mistake_matrix(
    case: Step1MistakeCase,
    crm_matrix_env: CoreStorage,
) -> None:
    _ = crm_matrix_env
    response = run_query(EntityQuery(lookup=case.lookup))
    assert response.outcome == case.expected_outcome, (
        f"{case.id}: outcome {response.outcome!r} != {case.expected_outcome!r}"
    )
    if case.expected_kind == "lookup_suggested":
        _assert_suggestions(list(response.suggestions or []), case)
    if case.expected_kind == "resolved":
        assert (response.total_matches or 0) >= 1


@pytest.mark.smoke
@pytest.mark.parametrize(
    "case",
    BASEBALL_STEP1_CASES,
    ids=lambda case: case.id,
)
def test_fuzzy_step1_baseball_mistake_matrix(
    case: Step1MistakeCase,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    _prepare_baseball_matrix_registry(tmp_path)
    expander = _mock_team_alias_expander if case.use_team_alias_mock else None
    result = resolve_target_step1(
        EntityQuery(lookup=case.lookup),
        alias_expander=expander,
    )
    assert result.kind == case.expected_kind, (
        f"{case.id}: kind {result.kind!r} != {case.expected_kind!r}"
    )
    if case.expected_kind == "lookup_suggested":
        _assert_suggestions(list(result.suggestions), case)
    if case.expected_kind == "resolved" and case.use_team_alias_mock:
        assert result.entity_ids