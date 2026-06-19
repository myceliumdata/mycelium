"""Tests for intent slug normalization."""

from __future__ import annotations

import json

from network.intent_map import load_intent_map
from network.intent_normalization import (
    IntentProposal,
    resolve_intent_slug,
    validate_intent_slug,
)
from network.paths import NetworkPaths

MINIMAL_MANIFEST = {
    "domains": {
        "batting": {
            "tables": ["Batting"],
            "grain": ["playerID"],
            "conventions": {},
            "aliases": {},
        },
    },
    "tables": {"Batting": {"columns": ["H", "AB"], "row_count": 1}},
}


def _test_paths(tmp_path) -> NetworkPaths:
    root = tmp_path / "network"
    root.mkdir()
    (root / "network.json").write_text(
        json.dumps(
            {
                "name": "test",
                "mvr": {
                    "default_record_type": "player",
                    "record_types": {
                    "player": {
                        "bind_fields": ["player"],
                        "new_records": "query_allowed",
                    },
                },
                },
            },
        ),
        encoding="utf-8",
    )
    return NetworkPaths.from_root(root)


def test_validate_intent_slug() -> None:
    assert validate_intent_slug("career_batting_average")
    assert not validate_intent_slug("")
    assert not validate_intent_slug("Bad-Slug")
    assert not validate_intent_slug("a" * 65)


def test_resolve_intent_slug_map_hit_skips_llm(tmp_path) -> None:
    paths = _test_paths(tmp_path)
    intent_map = {"career_avg": "career_batting_average"}

    called = {"count": 0}

    def fake_llm(_prompt):
        called["count"] += 1
        return IntentProposal(intent_slug="should_not_run", confidence=1.0)

    slug = resolve_intent_slug(
        "career_avg",
        domain="batting",
        manifest=MINIMAL_MANIFEST,
        paths=paths,
        intent_map=intent_map,
        llm_invoke=fake_llm,
    )
    assert slug == "career_batting_average"
    assert called["count"] == 0


def test_resolve_intent_slug_llm_persists_mapping(tmp_path) -> None:
    paths = _test_paths(tmp_path)
    intent_map: dict[str, str] = {}

    def fake_llm(_prompt):
        return IntentProposal(intent_slug="career_batting_average", confidence=0.95)

    slug = resolve_intent_slug(
        "career_avg",
        domain="batting",
        manifest=MINIMAL_MANIFEST,
        paths=paths,
        intent_map=intent_map,
        llm_invoke=fake_llm,
    )
    assert slug == "career_batting_average"
    assert intent_map["career_avg"] == "career_batting_average"
    assert load_intent_map(paths)["career_avg"] == "career_batting_average"


def test_resolve_intent_slug_low_confidence_falls_back_to_label(tmp_path) -> None:
    paths = _test_paths(tmp_path)
    intent_map: dict[str, str] = {}

    def fake_llm(_prompt):
        return IntentProposal(intent_slug="career_batting_average", confidence=0.5)

    slug = resolve_intent_slug(
        "career_avg",
        domain="batting",
        manifest=MINIMAL_MANIFEST,
        paths=paths,
        intent_map=intent_map,
        llm_invoke=fake_llm,
    )
    assert slug == "career_avg"
    assert intent_map == {}
    assert load_intent_map(paths) == {}
