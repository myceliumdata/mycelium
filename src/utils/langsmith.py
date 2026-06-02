"""LangSmith helpers for linking responses to observability UI."""

from __future__ import annotations

import os

_DEFAULT_UI_BASE = "https://smith.langchain.com"


def get_langsmith_trace_url(trace_id: str) -> str:
    """
    Return the LangSmith trace URL for a given ``trace_id``.

    By default uses the short form ``{base}/r/{trace_id}``, which LangSmith
    redirects to the correct run view. When ``LANGSMITH_ORG_ID`` and
    ``LANGSMITH_PROJECT_ID`` are set, returns the project-scoped URL:

    ``{base}/o/{org_id}/projects/p/{project_id}/r/{trace_id}``

    Override the UI host with ``LANGSMITH_UI_BASE_URL`` (no trailing slash).
    """
    tid = trace_id.strip()
    if not tid:
        msg = "trace_id must be a non-empty string"
        raise ValueError(msg)

    base = os.getenv("LANGSMITH_UI_BASE_URL", _DEFAULT_UI_BASE).rstrip("/")
    org_id = os.getenv("LANGSMITH_ORG_ID", "").strip()
    project_id = os.getenv("LANGSMITH_PROJECT_ID", "").strip()

    if org_id and project_id:
        return f"{base}/o/{org_id}/projects/p/{project_id}/r/{tid}"
    return f"{base}/r/{tid}"
