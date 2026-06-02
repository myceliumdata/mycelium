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
_last_invocation_trace_id: str | None = None


def _langsmith_tracing_enabled() -> bool:
    """Return True when LangSmith/LangChain tracing v2 is turned on."""
    return os.getenv("LANGCHAIN_TRACING_V2", "").lower() in {"1", "true", "yes", "on"}


def capture_langsmith_trace_id() -> str | None:
    """
    Read the LangSmith trace id for the active run context, if any.

    Returns None when tracing is off, langsmith is unavailable, or no run tree is set.
    """
    try:
        from langsmith.run_helpers import get_current_run_tree
    except ImportError:
        return None

    run_tree = get_current_run_tree()
    if run_tree is None:
        return None

    trace_id = run_tree.trace_id
    return str(trace_id) if trace_id else None


def get_last_invocation_trace_id() -> str | None:
    """Trace id captured during the most recent ``run_query`` / graph invoke (if any)."""
    return _last_invocation_trace_id


def reset_last_invocation_trace_id() -> None:
    """Clear stored trace id (for tests)."""
    global _last_invocation_trace_id
    _last_invocation_trace_id = None


def reset_core_graph() -> None:
    """Clear compiled graph singleton (for tests)."""
    global _compiled_graph, _checkpointer_ctx
    _compiled_graph = None
    _checkpointer_ctx = None
    reset_last_invocation_trace_id()


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


def _invoke_core_graph(
    graph: CompiledStateGraph,
    initial: MyceliumGraphState,
    config: dict[str, Any],
) -> Any:
    """
    Invoke the compiled graph and capture the LangSmith trace id when tracing is enabled.

    The trace id is stored via ``get_last_invocation_trace_id()`` for downstream response wiring.
    """
    global _last_invocation_trace_id
    _last_invocation_trace_id = None

    if _langsmith_tracing_enabled():
        from langsmith.run_helpers import traceable

        @traceable(name="mycelium_core_graph", run_type="chain")
        def _traced_invoke() -> Any:
            global _last_invocation_trace_id
            result = graph.invoke(initial, config=config)
            _last_invocation_trace_id = capture_langsmith_trace_id()
            return result

        return _traced_invoke()

    return graph.invoke(initial, config=config)


def _finalize_response(
    response: PersonResponse,
    *,
    thread_id: str,
    trace_id: str | None,
) -> PersonResponse:
    """Ensure caller thread_id and captured trace_id are on the outbound response."""
    if response.thread_id == thread_id and response.trace_id == trace_id:
        return response
    return response.model_copy(
        update={
            "thread_id": thread_id,
            "trace_id": trace_id,
        },
    )


def run_query(
    query: PersonQuery,
    *,
    thread_id: str = "default",
) -> PersonResponse:
    """Invoke the core graph and return a JSON-serializable response."""
    graph = get_core_graph()
    initial = MyceliumGraphState(
        query=query,
        invocation_thread_id=thread_id,
    )
    config = {"configurable": {"thread_id": thread_id}}
    result = _invoke_core_graph(graph, initial, config)
    captured_trace_id = get_last_invocation_trace_id()
    final = (
        result
        if isinstance(result, MyceliumGraphState)
        else MyceliumGraphState.model_validate(result)
    )
    if final.response is not None:
        return _finalize_response(
            final.response,
            thread_id=thread_id,
            trace_id=captured_trace_id,
        )

    return PersonResponse(
        results=[],
        message="Graph finished without a response payload.",
        debug="No response set by supervisor.",
        thread_id=thread_id,
        trace_id=captured_trace_id,
    )
