"""Tests for supervisor routing and the thin supervisor agent node."""

from __future__ import annotations

import pytest

from agents.core_identity import CoreIdentity
from agents.routing import evaluate_supervisor_turn
from agents.supervisor import supervisor_agent
from models.state import MyceliumGraphState, Person, PersonQuery


class _StubCoreIdentity(CoreIdentity):
    def __init__(self, person: Person | None) -> None:
        super().__init__(storage=None)
        self._person = person
        self.persisted: list[Person] = []

    def find_by_key(self, person_key: str) -> Person | None:
        return self._person

    def persist(self, person: Person) -> None:
        self.persisted.append(person)


@pytest.mark.smoke
def test_routing_delegates_lookup_to_core_identity() -> None:
    person = Person(id="p1", name="Ada", employer="Lab")
    core_identity = _StubCoreIdentity(person)
    state = MyceliumGraphState(query=PersonQuery(person_key="Ada"))

    decision = evaluate_supervisor_turn(state, core_identity=core_identity)

    assert len(decision.response.results) == 1
    assert decision.response.results[0]["name"] == "Ada"
    assert "Found core record" in decision.response.message


@pytest.mark.smoke
def test_routing_not_found_when_missing() -> None:
    core_identity = _StubCoreIdentity(None)
    state = MyceliumGraphState(query=PersonQuery(person_key="Missing"))

    decision = evaluate_supervisor_turn(state, core_identity=core_identity)

    assert decision.response.results == []
    assert "No core record found" in decision.response.message
    assert core_identity.persisted == []
    assert "ingest" not in decision.response.message.lower()
    assert "provided_data" not in decision.response.message.lower()


@pytest.mark.smoke
def test_routing_non_core_attributes() -> None:
    person = Person(id="p1", name="Ada", employer="Lab")
    core_identity = _StubCoreIdentity(person)
    state = MyceliumGraphState(
        query=PersonQuery(person_key="Ada", requested_attributes=["age"]),
    )

    decision = evaluate_supervisor_turn(state, core_identity=core_identity)

    assert len(decision.response.results) == 1
    assert "still researching" in decision.response.message
    assert "age" in decision.response.message


@pytest.mark.smoke
@pytest.mark.asyncio
async def test_supervisor_agent_routes_to_core_data() -> None:
    """Supervisor node only classifies; it does not build responses."""
    state = MyceliumGraphState(query=PersonQuery(person_key="any-key"))

    result = await supervisor_agent(state)

    assert result["route"] == "core_data"
    assert "response" not in result
    assert any("core_data" in entry for entry in result["audit_log"])
