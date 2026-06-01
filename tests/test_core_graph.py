"""Tests for core Mycelium graph and storage."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from graphs.core import reset_core_graph, run_query
from models.state import Person, PersonQuery
from storage.core import CoreStorage, reset_storage


@pytest.fixture
def temp_storage(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> CoreStorage:
    reset_storage()
    reset_core_graph()
    db = tmp_path / "test.db"
    seed = tmp_path / "seed.json"
    seed.write_text(
        json.dumps(
            {
                "people": [
                    {
                        "id": "person-test",
                        "name": "Test User",
                        "email": "test@example.com",
                        "employer": "Test Co",
                    },
                ],
            },
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("MYCELIUM_DB_PATH", str(db))
    monkeypatch.setenv("MYCELIUM_SEED_PATH", str(seed))
    monkeypatch.setenv("MYCELIUM_CHECKPOINT_PATH", str(tmp_path / "cp.sqlite"))
    from storage.core import get_storage

    storage = get_storage()
    yield storage
    reset_storage()
    reset_core_graph()


def test_query_existing_person(temp_storage: CoreStorage) -> None:
    _ = temp_storage
    response = run_query(PersonQuery(person_key="test@example.com"))
    assert response.status == "found"
    assert response.person is not None
    assert response.person.email == "test@example.com"


def test_query_missing_person(temp_storage: CoreStorage) -> None:
    _ = temp_storage
    response = run_query(PersonQuery(person_key="missing@example.com"))
    assert response.status == "data_request"
    assert response.data_request is not None
    assert "email" in response.data_request.required_fields


def test_query_derivative_attributes(temp_storage: CoreStorage) -> None:
    _ = temp_storage
    response = run_query(
        PersonQuery(
            person_key="test@example.com",
            requested_attributes=["age", "x_handle"],
        ),
    )
    assert response.status == "derivative_pending"
    assert response.derivative is not None
    assert "age" in response.derivative.attributes


def test_ingest_new_person(temp_storage: CoreStorage) -> None:
    _ = temp_storage
    response = run_query(
        PersonQuery(
            person_key="new@example.com",
            provided_data=Person(
                id="",
                name="New User",
                email="new@example.com",
                employer="New Co",
            ),
        ),
    )
    assert response.status == "ingested"
    assert response.person is not None
    stored = temp_storage.find_person("new@example.com")
    assert stored is not None
