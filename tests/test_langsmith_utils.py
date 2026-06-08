"""Tests for LangSmith trace URL helper."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from utils.langsmith import get_langsmith_trace_url, reset_langsmith_scope_cache


@pytest.fixture(autouse=True)
def _clear_scope_cache() -> None:
    reset_langsmith_scope_cache()
    yield
    reset_langsmith_scope_cache()


@pytest.mark.smoke
def test_short_trace_url_when_scope_unresolved(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("LANGSMITH_ORG_ID", raising=False)
    monkeypatch.delenv("LANGSMITH_PROJECT_ID", raising=False)
    monkeypatch.delenv("LANGCHAIN_API_KEY", raising=False)
    monkeypatch.delenv("LANGSMITH_API_KEY", raising=False)
    url = get_langsmith_trace_url("trace-abc")
    assert url == "https://smith.langchain.com/r/trace-abc"


@pytest.mark.smoke
def test_project_scoped_trace_url_when_org_and_project_set(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("LANGSMITH_ORG_ID", "org-1")
    monkeypatch.setenv("LANGSMITH_PROJECT_ID", "proj-2")
    url = get_langsmith_trace_url("trace-xyz")
    assert url == "https://smith.langchain.com/o/org-1/projects/p/proj-2/r/trace-xyz"


@pytest.mark.smoke
def test_project_scoped_trace_url_from_api_resolve(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("LANGSMITH_ORG_ID", raising=False)
    monkeypatch.delenv("LANGSMITH_PROJECT_ID", raising=False)
    monkeypatch.setenv("LANGCHAIN_API_KEY", "lsv2_pt_test")
    monkeypatch.setenv("LANGCHAIN_PROJECT", "mycelium")

    project = MagicMock()
    project.id = "proj-api-uuid"
    project.tenant_id = "org-api-uuid"

    client = MagicMock()
    client.read_project.return_value = project

    monkeypatch.setattr("langsmith.Client", lambda api_key=None: client)

    url = get_langsmith_trace_url("trace-resolved")
    assert url == (
        "https://smith.langchain.com/o/org-api-uuid/projects/p/proj-api-uuid/r/trace-resolved"
    )
    client.read_project.assert_called_once_with(project_name="mycelium")
    # Second call uses cache (no extra API call).
    url2 = get_langsmith_trace_url("trace-two")
    assert "org-api-uuid" in url2
    assert client.read_project.call_count == 1


@pytest.mark.smoke
def test_env_scope_takes_precedence_over_api_resolve(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("LANGSMITH_ORG_ID", "env-org")
    monkeypatch.setenv("LANGSMITH_PROJECT_ID", "env-proj")
    monkeypatch.setenv("LANGCHAIN_API_KEY", "lsv2_pt_test")

    client = MagicMock()
    monkeypatch.setattr("langsmith.Client", lambda api_key=None: client)

    url = get_langsmith_trace_url("trace-env")
    assert url == "https://smith.langchain.com/o/env-org/projects/p/env-proj/r/trace-env"
    client.read_project.assert_not_called()


@pytest.mark.smoke
def test_api_resolve_failure_falls_back_to_short_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("LANGSMITH_ORG_ID", raising=False)
    monkeypatch.delenv("LANGSMITH_PROJECT_ID", raising=False)
    monkeypatch.setenv("LANGCHAIN_API_KEY", "lsv2_pt_test")

    client = MagicMock()
    client.read_project.side_effect = RuntimeError("network down")
    monkeypatch.setattr("langsmith.Client", lambda api_key=None: client)

    url = get_langsmith_trace_url("trace-fallback")
    assert url == "https://smith.langchain.com/r/trace-fallback"


@pytest.mark.smoke
def test_custom_ui_base(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LANGSMITH_UI_BASE_URL", "https://smith.example.com/")
    monkeypatch.delenv("LANGSMITH_ORG_ID", raising=False)
    monkeypatch.delenv("LANGSMITH_PROJECT_ID", raising=False)
    monkeypatch.delenv("LANGCHAIN_API_KEY", raising=False)
    monkeypatch.delenv("LANGSMITH_API_KEY", raising=False)
    url = get_langsmith_trace_url("t1")
    assert url == "https://smith.example.com/r/t1"


@pytest.mark.smoke
def test_empty_trace_id_raises() -> None:
    with pytest.raises(ValueError, match="non-empty"):
        get_langsmith_trace_url("   ")
