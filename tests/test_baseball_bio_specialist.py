"""Smoke tests for baseball bio specialist raw warehouse read + provenance."""

from __future__ import annotations

from pathlib import Path

import pytest

from graphs.core import run_query
from models.state import EntityQuery
from baseball_minimal_fixture import (
    SAMPLE_PLAYER,
    refresh_baseball_root,
    refresh_baseball_root_with_fixture,
    write_missing_birth_month_fixture,
    write_missing_death_month_fixture,
)


def _deliver_bio_attr(
    attr: str,
    *,
    provenance: bool = False,
) -> tuple[object, object]:
    step1 = EntityQuery(
        lookup=dict(SAMPLE_PLAYER),
        requested_attributes=[attr],
        provenance=provenance,
    )
    r1 = run_query(step1, thread_id=f"{attr}-step1")
    assert r1.outcome == "lookup_resolved", r1.message
    assert r1.delivery is not None
    r2 = run_query(
        EntityQuery(delivery_id=r1.delivery.delivery_id),
        thread_id=f"{attr}-step2",
    )
    return r1, r2


@pytest.mark.smoke
def test_birth_date_deliver_found(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    refresh_baseball_root(tmp_path, monkeypatch)
    _, response = _deliver_bio_attr("birth_date")
    assert response.outcome in {"found", "assembled"}
    assert response.results
    assert response.results[0].get("birth_date") == "1934-02-05"


@pytest.mark.smoke
def test_birth_date_provenance_shape(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    refresh_baseball_root(tmp_path, monkeypatch)
    _, response = _deliver_bio_attr("birth_date", provenance=True)
    assert response.provenance is not None
    attrs = response.provenance["entities"][0]["attributes"]
    version = attrs["birth_date"]["versions"][0]
    assert version["status"] == "found"
    assert version["value"] == "1934-02-05"
    assert version["sources"][0]["kind"] == "dataset"
    assert version["sources"][0]["id"] == "lahman"
    assert version["computation"]["inline"]
    assert version["parameters"]["lahman.playerID"] == "aaronha01"
    assert version["parameters"]["warehouse"] == "warehouse/lahman.sqlite"
    assert version["parameters"]["attribute"] == "birth_date"
    assert version["actor"]["specialist"] == "bio_specialist"
    inline = version["computation"]["inline"]
    assert "birthYear" in inline
    assert "people_compose_iso_date" in inline or "birthMonth" in inline
    assert "birthYear" in version["parameters"].get("columns", "")


@pytest.mark.smoke
def test_birth_date_cache_hit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = refresh_baseball_root(tmp_path, monkeypatch)
    _, first = _deliver_bio_attr("birth_date")
    _, second = _deliver_bio_attr("birth_date")
    assert first.results[0].get("birth_date") == "1934-02-05"
    assert second.results[0].get("birth_date") == "1934-02-05"
    assert (root / "agents" / "bio" / "storage.json").is_file()


@pytest.mark.smoke
def test_birth_date_missing_birth_month_na(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    refresh_baseball_root_with_fixture(
        tmp_path,
        monkeypatch,
        fixture_fn=write_missing_birth_month_fixture,
    )
    _, response = _deliver_bio_attr("birth_date")
    assert response.results
    assert response.results[0].get("birth_date") == "N/A"


@pytest.mark.smoke
def test_death_date_missing_death_month_na(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    refresh_baseball_root_with_fixture(
        tmp_path,
        monkeypatch,
        fixture_fn=write_missing_death_month_fixture,
    )
    _, response = _deliver_bio_attr("death_date")
    assert response.results
    assert response.results[0].get("death_date") == "N/A"


@pytest.mark.smoke
def test_bats_deliver_found(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    refresh_baseball_root(tmp_path, monkeypatch)
    _, response = _deliver_bio_attr("bats")
    assert response.outcome in {"found", "assembled"}
    assert response.results
    assert response.results[0].get("bats") == "R"


@pytest.mark.smoke
def test_height_deliver_found(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    refresh_baseball_root(tmp_path, monkeypatch)
    _, response = _deliver_bio_attr("height")
    assert response.outcome in {"found", "assembled"}
    assert response.results
    assert response.results[0].get("height") == "72"


@pytest.mark.smoke
def test_weight_deliver_found(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    refresh_baseball_root(tmp_path, monkeypatch)
    _, response = _deliver_bio_attr("weight")
    assert response.results
    assert response.results[0].get("weight") == "180"


@pytest.mark.smoke
def test_birth_country_deliver_found(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    refresh_baseball_root(tmp_path, monkeypatch)
    _, response = _deliver_bio_attr("birth_country")
    assert response.results
    assert response.results[0].get("birth_country") == "USA"


@pytest.mark.smoke
def test_final_game_deliver_found(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    refresh_baseball_root(tmp_path, monkeypatch)
    _, response = _deliver_bio_attr("final_game")
    assert response.results
    assert response.results[0].get("final_game") == "1976-10-03"


@pytest.mark.smoke
def test_death_date_deliver_found(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    refresh_baseball_root(tmp_path, monkeypatch)
    _, response = _deliver_bio_attr("death_date")
    assert response.results
    assert response.results[0].get("death_date") == "2021-01-22"


@pytest.mark.smoke
def test_death_date_provenance_shape(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    refresh_baseball_root(tmp_path, monkeypatch)
    _, response = _deliver_bio_attr("death_date", provenance=True)
    assert response.provenance is not None
    version = response.provenance["entities"][0]["attributes"]["death_date"]["versions"][0]
    assert version["status"] == "found"
    assert version["value"] == "2021-01-22"
    assert version["parameters"]["lahman.playerID"] == "aaronha01"
    assert version["parameters"]["warehouse"] == "warehouse/lahman.sqlite"
    assert version["parameters"]["attribute"] == "death_date"
    inline = version["computation"]["inline"]
    assert "deathYear" in inline or "people_compose_iso_date" in inline
    assert "deathYear" in version["parameters"].get("columns", "")


@pytest.mark.smoke
def test_hall_of_fame_year_warehouse_manifest(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    refresh_baseball_root(tmp_path, monkeypatch)
    _, response = _deliver_bio_attr("hall_of_fame_year")
    assert response.outcome in {"found", "assembled"}
    assert response.results
    assert str(response.results[0].get("hall_of_fame_year")) == "1982"


@pytest.mark.smoke
def test_primary_nickname_research_mocked(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from tools.research import ResearchRunResult

    refresh_baseball_root(tmp_path, monkeypatch)
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("TAVILY_API_KEY", "test-key")

    def _fake_research(**kwargs):
        from agents.specialists.fields import append_version, ensure_versioned_for_write, research_actor

        storage = kwargs["storage"]
        person_id = kwargs["person_id"]
        category = kwargs["category"]
        specialist_name = kwargs["specialist_name"]
        data = storage.load()
        rec = data.setdefault("records", {}).setdefault(person_id, {})
        shell = ensure_versioned_for_write(rec.get("primary_nickname"))
        rec["primary_nickname"] = append_version(
            shell,
            {
                "at": "2026-01-01T00:00:00+00:00",
                "status": "found",
                "value": "Hammer",
                "sources": ["https://example.com/aaron"],
                "actor": research_actor(category=category, specialist_name=specialist_name),
            },
        )
        storage.save(data)
        return ResearchRunResult(fields_updated=["primary_nickname"])

    monkeypatch.setattr("tools.research.run_field_research", _fake_research)
    monkeypatch.setattr("tools.research.is_research_available", lambda: True)

    _, response = _deliver_bio_attr("primary_nickname")
    assert response.outcome in {"found", "assembled"}
    assert response.results
    assert response.results[0].get("primary_nickname") == "Hammer"
