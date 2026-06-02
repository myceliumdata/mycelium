"""Tests for LangSmith trace URL helper."""

from __future__ import annotations

import pytest

from utils.langsmith import get_langsmith_trace_url


@pytest.mark.smoke
def test_short_trace_url_by_default() -> None:
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
def test_custom_ui_base(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LANGSMITH_UI_BASE_URL", "https://smith.example.com/")
    url = get_langsmith_trace_url("t1")
    assert url == "https://smith.example.com/r/t1"


@pytest.mark.smoke
def test_empty_trace_id_raises() -> None:
    with pytest.raises(ValueError, match="non-empty"):
        get_langsmith_trace_url("   ")
