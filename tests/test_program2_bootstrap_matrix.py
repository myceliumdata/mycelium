"""Program 2 bootstrap path matrix (smoke): seed vs create-on-deliver × storage assertions."""

from __future__ import annotations

from pathlib import Path

import pytest

from agents.entity_registry import get_entity_registry
from graphs.core import run_query
from models.state import EntityQuery
from network.example import refresh_example_network
from test_example_network_capstones import (
    ROAD_RUNNER_LOOKUP,
    apply_refreshed_root,
    assert_bind_storage,
    assert_crm_seed_capstone,
    run_create_on_deliver,
)


@pytest.mark.smoke
def test_matrix_a_crm_refresh_seed_bootstrap_storage(tmp_path: Path) -> None:
    target = tmp_path / "matrix-a"
    refresh_example_network("crm", root=target, register=False, yes=True)
    assert_crm_seed_capstone(target)


@pytest.mark.smoke
def test_matrix_b_empty_crm_refresh_create_on_deliver_bind(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    target = tmp_path / "matrix-b"
    refresh_example_network("empty-crm", root=target, register=False, yes=True)
    outcome = run_create_on_deliver(
        monkeypatch,
        target,
        {"name": "Paul Murphy", "employer": "Acme Corp"},
    )
    assert_bind_storage(entity_id=outcome["entity_id"], actor_kind="bind")


@pytest.mark.smoke
def test_matrix_c_crm_road_runner_create_on_deliver(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    target = tmp_path / "matrix-c"
    refresh_example_network("crm", root=target, register=False, yes=True)
    outcome = run_create_on_deliver(monkeypatch, target, ROAD_RUNNER_LOOKUP)
    assert outcome["created"]["name"] == "Road Runner"
    assert_bind_storage(entity_id=outcome["entity_id"], actor_kind="bind")


@pytest.mark.smoke
def test_matrix_d_crm_road_runner_no_duplicate_bind_version(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    target = tmp_path / "matrix-d"
    refresh_example_network("crm", root=target, register=False, yes=True)
    first = run_create_on_deliver(monkeypatch, target, ROAD_RUNNER_LOOKUP)
    entity_id = first["entity_id"]

    apply_refreshed_root(monkeypatch, target)
    step1 = run_query(EntityQuery(lookup=ROAD_RUNNER_LOOKUP))
    assert step1.outcome == "lookup_resolved"
    assert step1.total_matches == 1
    assert step1.delivery is not None
    assert step1.delivery.create_on_deliver is not True

    step2 = run_query(EntityQuery(delivery_id=step1.delivery.delivery_id))
    assert step2.outcome == "found"
    assert len(step2.results) == 1
    assert step2.results[0]["id"] == entity_id

    assert_bind_storage(
        entity_id=entity_id,
        actor_kind="bind",
        name_version_count=1,
    )
    registry = get_entity_registry()
    assert len(registry.list_entities()) >= 16
