"""LangSmith helpers for linking responses to observability UI."""

from __future__ import annotations

import os

_DEFAULT_UI_BASE = "https://smith.langchain.com"

_cached_scope: tuple[str, str] | None = None


def reset_langsmith_scope_cache() -> None:
    """Clear cached org/project resolution (for tests and env changes)."""
    global _cached_scope
    _cached_scope = None


def _langsmith_api_key() -> str:
    return (
        os.getenv("LANGCHAIN_API_KEY", "").strip()
        or os.getenv("LANGSMITH_API_KEY", "").strip()
    )


def _resolve_langsmith_scope() -> tuple[str, str] | None:
    """
    Resolve LangSmith org and project UUIDs for deep trace URLs.

    Precedence: env vars (``LANGSMITH_ORG_ID`` + ``LANGSMITH_PROJECT_ID``), then
    one cached API lookup via ``read_project`` when an API key is configured.
    """
    global _cached_scope
    if _cached_scope is not None:
        return _cached_scope

    org_id = os.getenv("LANGSMITH_ORG_ID", "").strip()
    project_id = os.getenv("LANGSMITH_PROJECT_ID", "").strip()
    if org_id and project_id:
        _cached_scope = (org_id, project_id)
        return _cached_scope

    api_key = _langsmith_api_key()
    if not api_key:
        return None

    project_name = os.getenv("LANGCHAIN_PROJECT", "mycelium").strip() or "mycelium"
    try:
        from langsmith import Client

        project = Client(api_key=api_key).read_project(project_name=project_name)
        resolved_org = str(getattr(project, "tenant_id", "") or "").strip()
        resolved_project = str(getattr(project, "id", "") or "").strip()
        if resolved_org and resolved_project:
            _cached_scope = (resolved_org, resolved_project)
            return _cached_scope
    except Exception:
        return None
    return None


def get_langsmith_trace_url(trace_id: str) -> str:
    """
    Return the LangSmith trace URL for a given ``trace_id``.

    Prefers the project-scoped URL (works in the LangSmith UI):

    ``{base}/o/{org_id}/projects/p/{project_id}/r/{trace_id}``

    Org/project IDs come from ``LANGSMITH_ORG_ID`` + ``LANGSMITH_PROJECT_ID`` when
    set, otherwise a one-time ``read_project`` lookup using ``LANGCHAIN_API_KEY``
    (or ``LANGSMITH_API_KEY``) and ``LANGCHAIN_PROJECT``.

    If resolution fails, falls back to ``{base}/r/{trace_id}`` — that short form
    may return "Page not found" in the current LangSmith UI.

    Override the UI host with ``LANGSMITH_UI_BASE_URL`` (no trailing slash).
    """
    tid = trace_id.strip()
    if not tid:
        msg = "trace_id must be a non-empty string"
        raise ValueError(msg)

    base = os.getenv("LANGSMITH_UI_BASE_URL", _DEFAULT_UI_BASE).rstrip("/")
    scope = _resolve_langsmith_scope()
    if scope is not None:
        org_id, project_id = scope
        return f"{base}/o/{org_id}/projects/p/{project_id}/r/{tid}"
    return f"{base}/r/{tid}"
