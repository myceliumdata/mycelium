"""Tests for per-network intent_map.json."""

from __future__ import annotations

import json

from network.intent_map import load_intent_map, lookup_intent_slug, save_intent_mapping
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


def test_infer_slug_from_warm_cache_single_candidate() -> None:
    from network.intent_map import infer_slug_from_warm_cache

    record = {"career_batting_average": {"versions": [{"status": "found", "value": "0.500"}]}}
    intent_map = {"career_avg": "career_batting_average"}

    def has_value(entry):
        return isinstance(entry, dict) and bool(entry.get("versions"))

    assert infer_slug_from_warm_cache(record, intent_map, has_value=has_value) == "career_batting_average"


def test_infer_slug_from_warm_cache_ambiguous_returns_none() -> None:
    from network.intent_map import infer_slug_from_warm_cache

    record = {
        "career_batting_average": {"versions": [{"status": "found", "value": "0.500"}]},
        "career_ops": {"versions": [{"status": "found", "value": "0.900"}]},
    }
    intent_map = {"career_avg": "career_batting_average", "ops": "career_ops"}

    def has_value(entry):
        return isinstance(entry, dict) and bool(entry.get("versions"))

    assert infer_slug_from_warm_cache(record, intent_map, has_value=has_value) is None
