# Review: MCP runtime reload (slice 1200)

**Reviewer:** Grok  
**Verdict:** **Approved** — ready to commit and check off TODO.

## Scope compliance

| Requirement | Status |
|-------------|--------|
| `refresh_runtime_from_disk()` helper | **Done** — `src/agents/runtime.py` |
| Call before `query_person` / health ping | **Done** — `_run_mcp_query` |
| Registry, categories, seed, factory, module eviction | **Done** |
| No happy-path `reset_core_graph()` | **Done** — error path unchanged |
| Smoke tests | **Done** — `tests/test_mcp_runtime_reload.py` (2 tests) |
| README MCP restart sentence | **Done** |
| Out of scope respected | **Yes** — no graph/query/research changes |

**Bonus (good):** `list_specialist_routing` also calls `refresh_runtime_from_disk()` so routing list matches disk without a query.

## Code quality

- Clear module docstring; `reload_dotenv=False` for tests is the right escape hatch.
- `evict_cached_specialist_modules()` correctly preserves `agents.specialists.base`.
- Uses existing `reset_*` + `get_*` patterns (stronger than in-place `reload()` alone; consistent with `conftest`).

## Verification (re-run)

```
uv run pytest -m smoke -q  → 52 passed
uv run ruff check src tests → clean
```

## Non-blocking notes

1. **`health_check`** triggers refresh twice (via `list_specialist_routing` and `_run_mcp_query` ping). Harmless; optimize later if ever hot path.
2. **Uncommitted** — implementation lives in working tree only; commit after this review.
3. **Manual CLI/MCP parity** — documented in `output.md`; Paul should spot-check once with live keys + Andrea Kalmans email.

## Success criteria

Addresses the reported bug: MCP no longer needs restart to see registry/specialist storage written by a concurrent CLI process, assuming disk paths and `cwd` are correct.

**Follow-up for Paul/Grok:** Mark `MCP singleton reload` done in `TODO.md` after commit.