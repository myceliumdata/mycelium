"""Test helpers for versioned_provenance_v1 specialist storage fixtures."""

from __future__ import annotations

from typing import Any

from agents.specialist_fields import append_version, research_actor


def versioned_found(
    *,
    at: str,
    value: str,
    confidence: float = 0.9,
    sources: list[str] | None = None,
    category: str = "contact",
    specialist_name: str = "contact_specialist",
) -> dict[str, Any]:
    urls = sources or ["https://example.com"]
    return append_version(
        None,
        {
            "at": at,
            "status": "found",
            "value": value,
            "confidence": confidence,
            "sources": [{"url": url} for url in urls],
            "actor": research_actor(category=category, specialist_name=specialist_name),
        },
    )


def versioned_na(
    *,
    at: str,
    reason: str,
    category: str = "contact",
    specialist_name: str = "contact_specialist",
) -> dict[str, Any]:
    return append_version(
        None,
        {
            "at": at,
            "status": "na",
            "reason": reason,
            "actor": research_actor(category=category, specialist_name=specialist_name),
        },
    )


def versioned_pending(
    *,
    started_at: str,
    last_error: str = "",
    category: str = "contact",
    specialist_name: str = "contact_specialist",
) -> dict[str, Any]:
    return append_version(
        None,
        {
            "at": started_at,
            "status": "pending",
            "started_at": started_at,
            "last_error": last_error,
            "actor": research_actor(category=category, specialist_name=specialist_name),
        },
    )


def versioned_operator(
    *,
    at: str,
    value: str,
    note: str = "",
    category: str = "contact",
    specialist_name: str = "contact_specialist",
) -> dict[str, Any]:
    body: dict[str, Any] = {
        "at": at,
        "status": "found",
        "value": value,
        "actor": {"kind": "operator", "category": category, "specialist": specialist_name},
    }
    if note:
        body["note"] = note
    return append_version(None, body)
