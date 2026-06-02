"""Tests for Core Data specialist agent."""

from __future__ import annotations

import pytest

from agents.core_data import core_data_agent
from agents.core_identity import CoreIdentity
from models.state import MyceliumGraphState, Person, PersonQuery


class _StubCoreIdentity(CoreIdentity):
    def __init__(self, person: Person | None) -> None:
        super().__init__(storage=None)
        self._person = person

    def find_by_key(self, person_key: str) -> Person | None:
        return self._person


@pytest.mark.smoke
@pytest.mark.asyncio
async def test_core_data_agent_found(monkeypatch: pytest.MonkeyPatch) -> None:
    person = Person(id="p1", name="Ada", employer="Lab")
    stub = _StubCoreIdentity(person)
    monkeypatch.setattr("agents.core_data.get_core_identity", lambda: stub)
    state = MyceliumGraphState(
        query=PersonQuery(person_key="Ada"),
        invocation_thread_id="t1",
    )

    result = await core_data_agent(state)

    assert result["person"] == person
    assert "Found core record" in result["response"].message
    assert result["response"].thread_id == "t1"


@pytest.mark.smoke
@pytest.mark.asyncio
async def test_core_data_agent_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "agents.core_data.get_core_identity",
        lambda: _StubCoreIdentity(None),
    )
    state = MyceliumGraphState(query=PersonQuery(person_key="Missing"))

    result = await core_data_agent(state)

    assert "person" not in result
    assert result["response"].results == []
    assert "No core record found" in result["response"].message


@pytest.mark.smoke
@pytest.mark.asyncio
async def test_core_data_agent_non_core(monkeypatch: pytest.MonkeyPatch) -> None:
    person = Person(id="p1", name="Ada", employer="Lab")
    monkeypatch.setattr(
        "agents.core_data.get_core_identity",
        lambda: _StubCoreIdentity(person),
    )
    state = MyceliumGraphState(
        query=PersonQuery(person_key="Ada", requested_attributes=["email"]),
    )

    result = await core_data_agent(state)

    assert result["person"] == person
    assert "still researching" in result["response"].message
    assert "email" in result["response"].message
