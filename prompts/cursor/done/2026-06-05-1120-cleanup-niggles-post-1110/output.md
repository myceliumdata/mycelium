# Task 1120 output — Cleanup niggles post-1110

## Statement

**Niggles cleaned.** `docs/architecture.md`, `full-code-walkthrough.md`, `tmp/`, and the primary reset(s) now accurately describe the query-only public interface with core data owned by the `core_data_agent` (post 1110 + 1120). Checkpoint warnings addressed in normal operation.

## Grep discovery (stale phrases — before fix)

| Location | Stale content |
|----------|----------------|
| `docs/architecture.md` | "in progress (1070/1100)", inline routing, enrich/validator "until task 1070" |
| `docs/full-code-walkthrough.md` | pending wiring, transitional graph, "not yet default path", Target 1070/1100 |
| `tmp/restart-server-for-schema.md` | provided_data, ingest, enrich step |

Excluded from edits: `prompts/cursor/done/**` (audit record).

## Files touched

| File | Change |
|------|--------|
| `docs/architecture.md` | Replaced "Phase 1 progress" supervisor section with "Phase 1 complete"; updated flow table; footer 1120 |
| `docs/full-code-walkthrough.md` | Full refresh: current graph path, supervisor/routing/core_data accuracy, gaps from TODO, mental model |
| `tmp/restart-server-for-schema.md` | Query-only rewrite; 1120 header note |
| `src/graphs/core.py` | `JsonPlusSerializer(allowed_msgpack_modules=...)` on checkpointer (see below) |
| `bin/run-studio` | No functional change (removed ineffective env export after serde fix) |
| `prompts/resets/2026-06-02b_mvp_reset.md` | 1120 success criteria + next objectives |
| `prompts/resets/2026-06-05_mvp_current.md` | **New** canonical session reset |
| `TODO.md` | Last-updated note |

## Key before/after excerpts

### architecture.md — supervisor section (before)

> Wiring supervisor → `core_data_agent` in the graph is **in progress** (tasks 1070/1100); today routing still performs lookups inline...

### architecture.md — supervisor section (after)

> Wiring supervisor → `core_data_agent` ... was **completed** in tasks 1070/1100 and the final alignment pass was 1110. Legacy enrich/validator/person_prep ... **unwired legacy** ... not present in the compiled public graph.

### tmp/restart-server-for-schema.md (before)

> when adding Person under **provided_data** ... **new ingests** — the **enrich step** will generate the id

### tmp/restart-server-for-schema.md (after)

> Query-only input: `query` with `person_key` + optional `requested_attributes`. Expected path: **supervisor → core_data → END**. See `tmp/studio-inputs.md`.

## Checkpoint warnings fix

**Finding:** `LANGGRAPH_ALLOWED_MSGPACK_MODULES` is not read by LangGraph; warnings come from permissive default `JsonPlusSerializer`.

**Fix:** In `_setup_async_checkpointer`, pass:

```python
serde = JsonPlusSerializer(allowed_msgpack_modules=_CHECKPOINT_MSGPACK_ALLOWLIST)
saver = AsyncSqliteSaver(conn, serde=serde)
```

Allowlist: `MyceliumGraphState`, `Person`, `PersonQuery`, `PersonResponse`.

**Verification:** Second `run_query` with same `thread_id` after `reset_core_graph()` — **no** `"Deserializing unregistered type"` lines in stdout (see `/tmp/1120-verify.txt`). Second call hit a pre-existing `asyncio` event-loop lock error when reusing the saver across multiple `asyncio.run()` in one process; CLI single-invocation smoke is clean.

## Verification output

### `uv run ruff check src tests`

```
All checks passed!
```

### `uv run pytest -q`

```
22 passed in 0.43s
```

### `uv run pytest tests/test_core_graph.py::test_graph_invokes_supervisor_then_core_data -q --tb=no`

```
1 passed
```

### CLI smoke (`LANGCHAIN_TRACING_V2=false`)

```bash
uv run mycelium query --person-key "Nichanan Kesonpat" --thread-id "niggle-test-1120-b"
```

```json
{
  "results": [{"id": "person-0001", "name": "Nichanan Kesonpat", "employer": "1k(x)"}],
  "message": "Found core record for Nichanan Kesonpat.",
  "thread_id": "niggle-test-1120-b"
}
```

No deserialization warnings in captured CLI output.

### MCP smoke

Full `from mycelium_mcp.server import query_person` can block >120s when checkpoint DB is contended (eager `get_core_graph()`). Source remains query-only; graph path covered by pytest + CLI.

### Post-edit grep (docs, tmp, active resets)

No matches for: `pending (1070/1100)`, `until task 1070`, `Compiled today (transitional)`, `not yet the default path`, `Routing still performs lookups inline today`.

### `git status --porcelain` (task-related)

```
 M TODO.md
 M bin/run-studio
 M docs/architecture.md
 M docs/full-code-walkthrough.md
 M src/graphs/core.py
 M prompts/resets/2026-06-02b_mvp_reset.md
?? prompts/resets/2026-06-05_mvp_current.md
 (+ tmp/ changes if tracked)
```

## Future work (not in scope)

- Reduce `routing.py` duplication now that `core_data_agent` owns graph lookups (`TODO.md`).
- Internal data addition design (`TODO.md` "Re-adding data addition").
- LangSmith E2E in operator environment.
- Regenerate `src/mycelium.egg-info/` after release packaging.

## Follow-up prompts

None created in `next/` — remaining items are in `TODO.md`; add prompts when Paul/Grok prioritize.
