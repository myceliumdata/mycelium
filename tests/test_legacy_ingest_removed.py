"""Smoke guards: legacy ingest modules and SQLite people API stay removed."""

from __future__ import annotations

from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parent.parent
_AGENTS = _REPO / "src" / "agents"


@pytest.mark.smoke
def test_legacy_ingest_modules_deleted() -> None:
    for name in ("enrich.py", "validator.py", "person_prep.py"):
        assert not (_AGENTS / name).exists(), f"legacy module still present: {name}"


@pytest.mark.smoke
def test_core_storage_has_no_people_identity_api() -> None:
    text = (_REPO / "src" / "storage" / "core.py").read_text(encoding="utf-8")
    for symbol in (
        "seed_from_file",
        "upsert_person",
        "find_persons",
        "get_person_by_id",
        "CREATE TABLE IF NOT EXISTS people",
        "auto_seed",
    ):
        assert symbol not in text
