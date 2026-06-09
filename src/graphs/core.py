"""Core Mycelium LangGraph: seed resolution, context build, specialists, assembly.

Flow: START → supervisor → validate_entity → build_context (if specialists needed)
→ invoke_specialists → assemble_response → END; or validate_entity → assemble_response.

The default uses AsyncSqliteSaver (aiosqlite) so LangGraph Studio / langgraph dev
(ASGI) can use ainvoke cleanly. The MCP server forces the sync SqliteSaver path
(via MYCELIUM_USE_SYNC_CHECKPOINTER) for stability across many sequential
run_query calls inside a single long-lived stdio process. CLI currently goes
through the async path (one-shot invocations).
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path
from typing import Any, Literal

import aiosqlite
import sqlite3
from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from agents.dispatch import (
    assemble_response_node,
    build_context_node,
    invoke_specialists_node,
    validate_entity_node,
)
from agents.supervisor import supervisor_agent
from models.state import EntityQuery, MyceliumGraphState, QueryResponse

# Pydantic types stored in LangGraph checkpoints (avoids "Deserializing unregistered
# type models.state.*" warnings when resuming threads).
_CHECKPOINT_MSGPACK_ALLOWLIST: tuple[tuple[str, str], ...] = (
    ("models.state", "MyceliumGraphState"),
    ("models.state", "SeedRecord"),
    ("models.state", "EntityQuery"),
    ("models.state", "QueryResponse"),
    ("models.state", "EntityKeySuggestion"),
)

AfterValidation = Literal["build_context", "assemble_response"]
_compiled_graph: CompiledStateGraph | None = None
_checkpointer_ctx: AsyncSqliteSaver | SqliteSaver | None = None
_last_invocation_trace_id: str | None = None
_is_async_checkpointer: bool = True


async def _setup_async_checkpointer(checkpoint_path: Path) -> AsyncSqliteSaver:
    """Create and initialize the async SQLite checkpointer (non-blocking for ASGI)."""
    checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
    conn = await aiosqlite.connect(str(checkpoint_path))
    serde = JsonPlusSerializer(allowed_msgpack_modules=_CHECKPOINT_MSGPACK_ALLOWLIST)
    saver = AsyncSqliteSaver(conn, serde=serde)
    await saver.setup()
    return saver


def _close_checkpointer() -> None:
    """Close the process-wide checkpointer connection (async or sync) if present."""
    global _checkpointer_ctx, _is_async_checkpointer
    if _checkpointer_ctx is None:
        return
    conn = _checkpointer_ctx.conn
    if _is_async_checkpointer:
        async def _close() -> None:
            await conn.close()

        try:
            asyncio.get_running_loop()
        except RuntimeError:
            asyncio.run(_close())
        else:
            # Called from an active loop (unusual for this codebase); schedule close.
            asyncio.create_task(_close())
    else:
        # Sync SqliteSaver uses a regular sqlite3 connection.
        try:
            conn.close()
        except Exception:
            pass
    _checkpointer_ctx = None
    _is_async_checkpointer = True


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
    _close_checkpointer()
    _compiled_graph = None
    reset_last_invocation_trace_id()


def _specialists_planned(state: MyceliumGraphState) -> bool:
    ctx = state.context if isinstance(state.context, dict) else {}
    meta = ctx.get("_meta")
    if not isinstance(meta, dict):
        return False
    planned = meta.get("specialists_to_invoke") or []
    return bool(planned)


def _route_after_validation(
    state: MyceliumGraphState | dict[str, Any],
) -> AfterValidation:
    current = (
        state
        if isinstance(state, MyceliumGraphState)
        else MyceliumGraphState.model_validate(state)
    )
    if _specialists_planned(current):
        return "build_context"
    return "assemble_response"


def build_core_graph(
    *,
    checkpoint_path: Path | None = None,
    setup_checkpointer: bool = True,
    async_checkpointer: bool | None = None,
) -> CompiledStateGraph:
    """Compile the query-only graph with a SQLite checkpointer.

    By default uses the async (aiosqlite) saver, which is required for
    LangGraph Studio / langgraph dev (ASGI). Callers that need a long-lived
    synchronous process (MCP server, some CLI scenarios) can request the
    sync SqliteSaver by passing async_checkpointer=False or by setting
    MYCELIUM_USE_SYNC_CHECKPOINTER=1 before importing graphs.core.
    """
    graph: StateGraph = StateGraph(MyceliumGraphState)

    graph.add_node("supervisor", supervisor_agent)
    graph.add_node("validate_entity", validate_entity_node)
    graph.add_node("build_context", build_context_node)
    graph.add_node("invoke_specialists", invoke_specialists_node)
    graph.add_node("assemble_response", assemble_response_node)

    graph.add_edge(START, "supervisor")
    graph.add_edge("supervisor", "validate_entity")
    graph.add_conditional_edges(
        "validate_entity",
        _route_after_validation,
        {
            "build_context": "build_context",
            "assemble_response": "assemble_response",
        },
    )
    graph.add_edge("build_context", "invoke_specialists")
    graph.add_edge("invoke_specialists", "assemble_response")
    graph.add_edge("assemble_response", END)

    checkpointer: AsyncSqliteSaver | SqliteSaver | None = None
    if setup_checkpointer:
        global _checkpointer_ctx, _is_async_checkpointer
        from network.paths import runtime_path

        resolved = (
            checkpoint_path
            if checkpoint_path is not None
            else runtime_path("MYCELIUM_CHECKPOINT_PATH")
        )

        # Determine saver type. Default = async (Studio friendly).
        # MCP server sets MYCELIUM_USE_SYNC_CHECKPOINTER=1 before import.
        if async_checkpointer is None:
            env_sync = os.getenv("MYCELIUM_USE_SYNC_CHECKPOINTER", "").lower()
            use_sync = env_sync in {"1", "true", "yes", "on"}
            use_async = not use_sync
        else:
            use_async = async_checkpointer

        if use_async:
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
            _is_async_checkpointer = True
            checkpointer = _checkpointer_ctx
        else:
            # Sync path: regular sqlite3 connection + SqliteSaver.
            # Much more stable for long-running stdio servers (MCP) that make
            # repeated run_query calls, because we avoid asyncio.run + aiosqlite
            # loop affinity problems.
            resolved.parent.mkdir(parents=True, exist_ok=True)
            conn = sqlite3.connect(str(resolved), check_same_thread=False)
            serde = JsonPlusSerializer(allowed_msgpack_modules=_CHECKPOINT_MSGPACK_ALLOWLIST)
            saver = SqliteSaver(conn, serde=serde)
            saver.setup()
            _checkpointer_ctx = saver
            _is_async_checkpointer = False
            checkpointer = _checkpointer_ctx

    return graph.compile(checkpointer=checkpointer)


def get_core_graph(async_checkpointer: bool | None = None) -> CompiledStateGraph:
    """Return a process-wide compiled graph singleton."""
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_core_graph(async_checkpointer=async_checkpointer)
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
    """Sync entry for CLI/MCP when using the async checkpointer.

    Runs the async graph invoke in a fresh event loop via asyncio.run().
    Only used for the async saver path (Studio, default).
    """
    return asyncio.run(_ainvoke_core_graph(graph, initial, config))


def _invoke_sync_graph(
    graph: CompiledStateGraph,
    initial: MyceliumGraphState,
    config: dict[str, Any],
) -> Any:
    """Direct sync invoke for the sync SqliteSaver path (used by MCP server).

    Avoids any asyncio.run() + aiosqlite loop affinity issues in long-lived
    processes that handle multiple sequential queries.
    """
    global _last_invocation_trace_id
    _last_invocation_trace_id = None

    if _langsmith_tracing_enabled():
        try:
            from langsmith import traceable
            from langsmith.run_helpers import get_current_run_tree

            @traceable(name="mycelium_core_graph", run_type="chain")
            def _traced_sync_invoke(initial_state: MyceliumGraphState, cfg: dict[str, Any]) -> Any:
                global _last_invocation_trace_id
                res = graph.invoke(initial_state, config=cfg)
                tree = get_current_run_tree()
                if tree is not None:
                    _last_invocation_trace_id = str(tree.trace_id) if tree.trace_id else None
                return res

            return _traced_sync_invoke(initial, config)
        except Exception:
            # Fall back to plain invoke if langsmith traceable isn't usable here.
            pass

    return graph.invoke(initial, config=config)


def _finalize_response(
    response: QueryResponse,
    *,
    thread_id: str,
    trace_id: str | None,
) -> QueryResponse:
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
    query: EntityQuery,
    *,
    thread_id: str = "default",
) -> QueryResponse:
    """Invoke the core graph and return a JSON-serializable response.

    The LangSmith trace Input always contains a ``query`` section (a query-only
    ``EntityQuery``). Supervisor plans specialists; graph nodes build context, invoke, assemble.
    """
    graph = get_core_graph()
    # Checkpointed threads may still hold ``response`` from a prior query on the
    # same ``thread_id``. Clear it so ``assemble_response`` rebuilds for this
    # ``EntityQuery`` (see tests/test_query_messages.py thread reuse test).
    initial = MyceliumGraphState(
        query=query,
        invocation_thread_id=thread_id,
        response=None,
    )
    config = {"configurable": {"thread_id": thread_id}}

    if _is_async_checkpointer:
        result = _invoke_core_graph(graph, initial, config)
    else:
        result = _invoke_sync_graph(graph, initial, config)

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

    return QueryResponse(
        results=[],
        message="Graph finished without a response payload.",
        debug="outcome='error'; reason='no_response_set_by_assemble_response'",
        outcome="error",
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
# The MCP server (mycelium_mcp/server.py) sets MYCELIUM_USE_SYNC_CHECKPOINTER=1
# *before* importing this module so it gets a stable sync SqliteSaver instead of
# the async one. This prevents the repeated-asyncio.run + aiosqlite connection
# affinity problems that can cause the server to get "stuck" after a few calls
# in a long-lived stdio process.
#
# Skip during pytest runs (including collection of smoke tests) to avoid
# creating long-lived aiosqlite connections/threads that prevent the pytest
# process from exiting promptly after the tests have reported their results.
if "pytest" not in sys.modules:
    use_sync = os.getenv("MYCELIUM_USE_SYNC_CHECKPOINTER", "").lower() in {"1", "true", "yes", "on"}
    get_core_graph(async_checkpointer=not use_sync)
