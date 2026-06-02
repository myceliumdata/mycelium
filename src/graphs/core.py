"""Core Mycelium LangGraph: Supervisor + Core Data specialist (query-only).

Flow: START → supervisor (classify & route) → core_data (lookup & response) → END.

Uses AsyncSqliteSaver (aiosqlite) + async nodes so langgraph dev / Studio (ASGI)
can ainvoke without blocking warnings. CLI and MCP use the sync run_query()
bridge which does asyncio.run(ainvoke) internally.
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path
from typing import Any, Literal

import aiosqlite
from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from agents.core_data import core_data_agent
from agents.supervisor import supervisor_agent
from models.state import MyceliumGraphState, PersonQuery, PersonResponse

DEFAULT_CHECKPOINT_PATH = Path("data/checkpoints.sqlite")

# Pydantic types stored in LangGraph checkpoints (avoids "Deserializing unregistered
# type models.state.*" warnings when resuming threads).
_CHECKPOINT_MSGPACK_ALLOWLIST: tuple[tuple[str, str], ...] = (
    ("models.state", "MyceliumGraphState"),
    ("models.state", "Person"),
    ("models.state", "PersonQuery"),
    ("models.state", "PersonResponse"),
)

Route = Literal["core_data", "__end__"]
_compiled_graph: CompiledStateGraph | None = None
_checkpointer_ctx: AsyncSqliteSaver | None = None
_last_invocation_trace_id: str | None = None


async def _setup_async_checkpointer(checkpoint_path: Path) -> AsyncSqliteSaver:
    """Create and initialize the async SQLite checkpointer (non-blocking for ASGI)."""
    checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
    conn = await aiosqlite.connect(str(checkpoint_path))
    serde = JsonPlusSerializer(allowed_msgpack_modules=_CHECKPOINT_MSGPACK_ALLOWLIST)
    saver = AsyncSqliteSaver(conn, serde=serde)
    await saver.setup()
    return saver


def _close_async_checkpointer() -> None:
    """Close the process-wide async checkpointer connection if present."""
    global _checkpointer_ctx
    if _checkpointer_ctx is None:
        return
    conn = _checkpointer_ctx.conn

    async def _close() -> None:
        await conn.close()

    try:
        asyncio.get_running_loop()
    except RuntimeError:
        asyncio.run(_close())
    else:
        # Called from an active loop (unusual for this codebase); schedule close.
        asyncio.create_task(_close())
    _checkpointer_ctx = None


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
    global _compiled_graph
    _close_async_checkpointer()
    _compiled_graph = None
    reset_last_invocation_trace_id()


def _route_after_supervisor(state: MyceliumGraphState | dict[str, Any]) -> Route:
    current = (
        state
        if isinstance(state, MyceliumGraphState)
        else MyceliumGraphState.model_validate(state)
    )
    if current.route == "core_data":
        return "core_data"
    return "__end__"


def build_core_graph(
    *,
    checkpoint_path: Path | None = None,
    setup_checkpointer: bool = True,
) -> CompiledStateGraph:
    """Compile the query-only graph with a SQLite checkpointer."""
    graph: StateGraph = StateGraph(MyceliumGraphState)

    graph.add_node("supervisor", supervisor_agent)
    graph.add_node("core_data", core_data_agent)

    graph.add_edge(START, "supervisor")
    graph.add_conditional_edges(
        "supervisor",
        _route_after_supervisor,
        {"core_data": "core_data", "__end__": END},
    )
    graph.add_edge("core_data", END)

    checkpointer: AsyncSqliteSaver | None = None
    if setup_checkpointer:
        global _checkpointer_ctx
        resolved = Path(
            os.getenv("MYCELIUM_CHECKPOINT_PATH", str(checkpoint_path or DEFAULT_CHECKPOINT_PATH)),
        )
        try:
            asyncio.get_running_loop()
            in_loop = True
        except RuntimeError:
            in_loop = False

        if in_loop:
            raise RuntimeError(
                "build_core_graph() (and thus get_core_graph()) was invoked "
                "from within a running event loop. The eager `get_core_graph()` "
                "call at the bottom of this module should ensure the (one-time) "
                "build + asyncio.run for the async checkpointer happens at import "
                "time, before langgraph dev / Studio's ASGI loop starts serving. "
                "If you hit this after reset_core_graph() in an async context, "
                "re-acquire the graph from a synchronous context, or restructure "
                "so the singleton is not cleared while the server loop is live."
            )

        _checkpointer_ctx = asyncio.run(_setup_async_checkpointer(resolved))
        checkpointer = _checkpointer_ctx

    return graph.compile(checkpointer=checkpointer)


def get_core_graph() -> CompiledStateGraph:
    """Return a process-wide compiled graph singleton."""
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_core_graph()
    return _compiled_graph


async def _ainvoke_core_graph(
    graph: CompiledStateGraph,
    initial: MyceliumGraphState,
    config: dict[str, Any],
) -> Any:
    """
    Invoke the compiled graph asynchronously and capture the LangSmith trace id.

    Uses ``ainvoke`` so LangGraph dev / ASGI servers do not block the event loop.
    The trace id is stored via ``get_last_invocation_trace_id()`` for downstream wiring.

    When tracing is enabled we wrap ``ainvoke`` in @traceable so the top-level run
    appears in LangSmith with the initial state as input (not a zero-arg closure).
    """
    global _last_invocation_trace_id
    _last_invocation_trace_id = None

    if _langsmith_tracing_enabled():
        from langsmith.run_helpers import traceable

        @traceable(name="mycelium_core_graph", run_type="chain")
        async def _traced_ainvoke(initial_state: MyceliumGraphState, cfg: dict[str, Any]) -> Any:
            global _last_invocation_trace_id
            result = await graph.ainvoke(initial_state, config=cfg)
            _last_invocation_trace_id = capture_langsmith_trace_id()
            return result

        return await _traced_ainvoke(initial, config)

    return await graph.ainvoke(initial, config=config)


def _invoke_core_graph(
    graph: CompiledStateGraph,
    initial: MyceliumGraphState,
    config: dict[str, Any],
) -> Any:
    """Sync entry for CLI/MCP; runs the async graph invoke in a fresh event loop."""
    return asyncio.run(_ainvoke_core_graph(graph, initial, config))


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
    """Invoke the core graph and return a JSON-serializable response.

    The LangSmith trace Input always contains a ``query`` section (a query-only
    ``PersonQuery``). Supervisor routes to ``core_data``; lookups run in that node.
    """
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
        debug="No response set by core_data.",
        thread_id=thread_id,
        trace_id=captured_trace_id,
    )


# Eager initialization of the graph singleton at module import time.
# langgraph dev / Studio (and its langgraph_api) lazily invokes the graph factory
# (get_core_graph) from within a running event loop (during request handling
# in langgraph_api/graph.py -> get_graph). Performing the build (which calls
# asyncio.run for the async checkpointer setup) at import time ensures it
# happens before the ASGI server loop is active. Subsequent calls return the
# cached graph without re-entering build_core_graph.
#
# Skip during pytest runs (including collection of smoke tests) to avoid
# creating long-lived aiosqlite connections/threads that prevent the pytest
# process from exiting promptly after the tests have reported their results.
if "pytest" not in sys.modules:
    get_core_graph()
