"""Tests for per-network intent_map.json."""

from __future__ import annotations

import json

from network.intent_map import (
    labels_for_intent_slug,
    load_intent_map,
    lookup_intent_slug,
    save_intent_mapping,
)
from network.paths import NetworkPaths

_MINIMAL_NETWORK_JSON = {
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
}


def _test_paths(tmp_path) -> NetworkPaths:
    root = tmp_path / "network"
    root.mkdir()
    (root / "network.json").write_text(json.dumps(_MINIMAL_NETWORK_JSON), encoding="utf-8")
    return NetworkPaths.from_root(root)


def test_intent_map_round_trip(tmp_path) -> None:
    paths = _test_paths(tmp_path)

    assert load_intent_map(paths) == {}

    save_intent_mapping(paths, "career_avg", "career_batting_average")
    mappings = load_intent_map(paths)
    assert lookup_intent_slug("career_avg", mappings) == "career_batting_average"
    assert lookup_intent_slug("Career_Avg", mappings) == "career_batting_average"

    save_intent_mapping(paths, "batting_average", "career_batting_average")
    mappings = load_intent_map(paths)
    assert lookup_intent_slug("batting_average", mappings) == "career_batting_average"
    assert len(mappings) == 2

    raw = (paths.root / "intent_map.json").read_text(encoding="utf-8")
    assert '"version": "1.0"' in raw


def test_labels_for_intent_slug() -> None:
    intent_map = {
        "career_avg": "career_batting_average",
        "batting_average": "career_batting_average",
        "ops": "career_ops",
    }
    assert labels_for_intent_slug("career_batting_average", intent_map) == {
        "career_batting_average",
        "career_avg",
        "batting_average",
    }
