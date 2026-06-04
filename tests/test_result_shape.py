"""Smoke tests for attribute-scoped PersonResponse results (slice 1400)."""

from __future__ import annotations

import pytest

from agents.responses import merge_requested_record, shape_results


@pytest.mark.smoke
def test_shape_results_identity_summary() -> None:
    records = [{"id": "u1", "name": "Ada", "employer": "Lab", "extra": "x"}]
    shaped = shape_results(records, None)
    assert shaped == [{"id": "u1", "name": "Ada", "employer": "Lab"}]


@pytest.mark.smoke
def test_shape_results_requested_only() -> None:
    records = [{"id": "u1", "name": "Ada", "employer": "Lab"}]
    shaped = shape_results(records, ["name"])
    assert shaped == [{"id": "u1", "name": "Ada"}]


@pytest.mark.smoke
def test_merge_specialist_over_seed() -> None:
    seed = {"id": "u1", "name": "Paul Murphy", "employer": "Co"}
    contributions = [
        {
            "specialist_contrib": {
                "values": {"name": "Paul Robert Murphy"},
            },
        },
    ]
    merged, provisional, unavailable = merge_requested_record(
        seed,
        contributions,
        ["name"],
    )
    assert merged["name"] == "Paul Robert Murphy"
    assert provisional == []
    assert unavailable == []


@pytest.mark.smoke
def test_merge_seed_provisional_when_specialist_pending() -> None:
    seed = {"id": "u1", "name": "Nichanan Kesonpat", "employer": "1k(x)"}
    contributions = [
        {
            "specialist_contrib": {
                "values": {"name": "pending"},
                "status": "pending",
            },
        },
    ]
    merged, provisional, unavailable = merge_requested_record(
        seed,
        contributions,
        ["name"],
    )
    assert merged["name"] == "Nichanan Kesonpat"
    assert provisional == ["name"]
    assert unavailable == []