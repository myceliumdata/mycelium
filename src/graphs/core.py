"""Core Mycelium LangGraph: Supervisor + Enrich + Validator with SQLite checkpointer."""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import Any, Literal

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from agents.enrich import enrich_agent
from agents.supervisor import supervisor_agent
from agents.validator import validator_agent
from models.state import MyceliumGraphState, PersonQuery, PersonResponse

DEFAULT_CHECKPOINT_PATH = Path("data/checkpoints.sqlite")

Route = Literal["enrich", "__end__"]
_compiled_graph: CompiledStateGraph | None = None
_checkpointer_ctx: SqliteSaver | None = None


def reset_core_graph() -> None:
    """Clear compiled graph singleton (for tests)."""
    global _compiled_graph, _checkpointer_ctx
    _compiled_graph = None
    _checkpointer_ctx = None


def _route_after_supervisor(state: MyceliumGraphState | dict[str, Any]) -> Route:
    current = (
        state
        if isinstance(state, MyceliumGraphState)
        else MyceliumGraphState.model_validate(state)
    )
    if current.route == "enrich":
        return "enrich"
    return "__end__"


def build_core_graph(
    *,
    checkpoint_path: Path | None = None,
    setup_checkpointer: bool = True,
) -> CompiledStateGraph:
    """Compile the core graph with a SQLite checkpointer."""
    graph: StateGraph = StateGraph(MyceliumGraphState)

    graph.add_node("supervisor", supervisor_agent)
    graph.add_node("enrich", enrich_agent)
    graph.add_node("validator", validator_agent)

    graph.add_edge(START, "supervisor")
    graph.add_conditional_edges(
        "supervisor",
        _route_after_supervisor,
        {"enrich": "enrich", "__end__": END},
    )
    graph.add_edge("enrich", "validator")
    graph.add_edge("validator", "supervisor")

    checkpointer: SqliteSaver | None = None
    if setup_checkpointer:
        global _checkpointer_ctx
        resolved = Path(
            os.getenv("MYCELIUM_CHECKPOINT_PATH", str(checkpoint_path or DEFAULT_CHECKPOINT_PATH)),
        )
        resolved.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(resolved), check_same_thread=False)
        _checkpointer_ctx = SqliteSaver(conn)
        _checkpointer_ctx.setup()
        checkpointer = _checkpointer_ctx

    return graph.compile(checkpointer=checkpointer)


def get_core_graph() -> CompiledStateGraph:
    """Return a process-wide compiled graph singleton."""
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_core_graph()
    return _compiled_graph


def run_query(
    query: PersonQuery,
    *,
    thread_id: str = "default",
) -> PersonResponse:
    """Invoke the core graph and return a JSON-serializable response."""
    graph = get_core_graph()
    initial = MyceliumGraphState(query=query)
    result = graph.invoke(
        initial,
        config={"configurable": {"thread_id": thread_id}},
    )
    final = (
        result
        if isinstance(result, MyceliumGraphState)
        else MyceliumGraphState.model_validate(result)
    )
    if final.response is not None:
        return final.response

    return PersonResponse(
        status="validation_failed",
        message="Graph finished without a response payload.",
        errors=["No response set by supervisor."],
    )
