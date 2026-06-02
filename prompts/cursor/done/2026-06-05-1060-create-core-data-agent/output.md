# Output: Create Core Data agent (1060)

## Summary

Added `src/agents/core_data.py` with async `core_data_agent` — the specialist node that owns core CRM lookups for the query-only public interface. Lookups run via `get_core_identity().find_by_key()` inside `asyncio.to_thread`; responses use the same builders as routing (`response_found`, `response_not_found`, `response_non_core`). Propagates `invocation_thread_id` / `invocation_trace_id` into `PersonResponse`.

## New file: `src/agents/core_data.py`

- `_build_lookup_response()` — found / not-found / non-core selection (mirrors routing lookup logic)
- `_run_core_data_lookup()` — sync worker for thread offload
- `core_data_agent()` — async LangGraph node returning `person`, `response`, `route=None`, `audit_log`

## Other touches

| File | Change |
|------|--------|
| `src/agents/core_identity.py` | Docstring: facade used by CoreDataAgent |
| `src/agents/__init__.py` | Export `core_data_agent` |
| `tests/test_core_data_agent.py` | Async tests with stubbed CoreIdentity |

## Not done (by design)

- Graph wiring (task **1070** / **1100**)
- Supervisor/routing delegation to this node (task **1100**)
- Persist path on core data agent (future internal coordination)

## Verification

```bash
uv run pytest tests/test_core_data_agent.py -q   # 2 passed
uv run pytest -q                                 # full suite green
uv run ruff check src/agents/core_data.py
```

## Next steps

Wire `core_data_agent` into `graphs/core.py` and route supervisor → core_data instead of inline routing lookup.
