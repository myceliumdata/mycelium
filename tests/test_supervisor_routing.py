"""Tests for supervisor routing and Core Identity delegation."""

from __future__ import annotations

from agents.core_identity import CoreIdentity
from agents.routing import evaluate_supervisor_turn
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


def test_routing_delegates_lookup_to_core_identity() -> None:
    person = Person(id="p1", name="Ada", employer="Lab")
    core_identity = _StubCoreIdentity(person)
    state = MyceliumGraphState(query=PersonQuery(person_key="Ada"))

    decision = evaluate_supervisor_turn(state, core_identity=core_identity)

    assert decision.action == "respond"
    assert decision.response is not None
    assert len(decision.response.results) == 1
    assert decision.response.results[0]["name"] == "Ada"


def test_routing_persist_after_validation() -> None:
    person = Person(id="p2", name="New", employer="Co")
    core_identity = _StubCoreIdentity(None)
    state = MyceliumGraphState(
        query=PersonQuery(person_key="New"),
        person=person,
        validation_passed=True,
    )

    decision = evaluate_supervisor_turn(state, core_identity=core_identity)

    assert decision.action == "respond"
    assert core_identity.persisted == [person]
    assert "Added core record" in (decision.response.message if decision.response else "")
