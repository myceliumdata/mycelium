"""Unit tests for versioned specialist field helpers."""

from __future__ import annotations

import pytest

from agents.specialist_fields import (
    append_version,
    current_status,
    current_value,
    current_version,
    ensure_versioned_for_write,
    field_has_value,
    research_actor,
    validate_versioned_field,
)
from tools.research import _write_pending
from versioned_storage_fixtures import versioned_found, versioned_na, versioned_pending


@pytest.mark.smoke
def test_append_two_research_versions_current_is_v2() -> None:
    actor = research_actor(category="social", specialist_name="social_specialist")
    entry = append_version(
        None,
        {
            "at": "2026-06-11T05:00:00+00:00",
            "status": "found",
            "value": "https://linkedin.com/in/old",
            "confidence": 0.7,
            "sources": [{"url": "https://linkedin.com/in/old"}],
            "actor": actor,
        },
    )
    entry = append_version(
        entry,
        {
            "at": "2026-06-11T06:00:00+00:00",
            "status": "found",
            "value": "https://linkedin.com/in/new",
            "confidence": 0.9,
            "sources": [{"url": "https://linkedin.com/in/new"}],
            "actor": actor,
        },
    )
    assert entry["current_version_id"] == "v2"
    assert len(entry["versions"]) == 2
    assert current_value(entry) == "https://linkedin.com/in/new"


@pytest.mark.smoke
def test_flat_v1_entry_raises_on_validate() -> None:
    flat = {"status": "found", "value": "a@b.com", "researched_at": "2026-06-11T00:00:00+00:00"}
    with pytest.raises(ValueError, match="deprecated flat field format"):
        validate_versioned_field(flat, field_name="email", category="contact")


@pytest.mark.smoke
def test_pending_and_na_version_append() -> None:
    pending = versioned_pending(started_at="2026-06-11T05:00:00+00:00", last_error="timeout")
    assert current_status(pending) == "pending"
    assert not field_has_value(pending)

    na = versioned_na(at="2026-06-11T06:00:00+00:00", reason="no evidence")
    assert current_status(na) == "na"
    assert not field_has_value(na)


@pytest.mark.smoke
def test_current_value_and_field_has_value_by_status() -> None:
    found = versioned_found(at="2026-06-11T05:00:00+00:00", value="a@b.com")
    assert field_has_value(found)
    assert current_value(found) == "a@b.com"
    version = current_version(found)
    assert version is not None
    assert version["status"] == "found"


@pytest.mark.smoke
def test_ensure_versioned_for_write_wraps_flat_pending() -> None:
    flat_pending = {
        "status": "pending",
        "started_at": "2026-06-11T05:00:00+00:00",
        "last_error": "timeout",
    }
    wrapped = ensure_versioned_for_write(flat_pending)
    assert wrapped["current_version_id"] == "v1"
    assert len(wrapped["versions"]) == 1
    assert wrapped["versions"][0]["status"] == "pending"
    assert wrapped["versions"][0]["started_at"] == "2026-06-11T05:00:00+00:00"
    assert wrapped["versions"][0]["last_error"] == "timeout"


@pytest.mark.smoke
def test_write_pending_in_place_retry_preserves_started_at() -> None:
    first = _write_pending(
        None,
        at="2026-06-11T05:00:00+00:00",
        last_error="err1",
        started_at=None,
        category="contact",
        specialist_name="contact_specialist",
    )
    second = _write_pending(
        first,
        at="2026-06-11T06:00:00+00:00",
        last_error="err2",
        started_at="2026-06-11T05:00:00+00:00",
        category="contact",
        specialist_name="contact_specialist",
    )
    assert len(second["versions"]) == 1
    assert second["current_version_id"] == "v1"
    version = second["versions"][0]
    assert version["started_at"] == "2026-06-11T05:00:00+00:00"
    assert version["at"] == "2026-06-11T06:00:00+00:00"
    assert version["last_error"] == "err2"
