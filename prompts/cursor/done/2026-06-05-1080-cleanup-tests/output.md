# Output: Cleanup tests (1080)

## Summary

Confirmed ingest tests were already removed in the 1000–1050 batch. Expanded coverage for query-only paths, `core_data_agent`, thin supervisor routing, and the supervisor → core_data graph flow.

## Changes

### `tests/test_core_graph.py`

- Module docstring notes query-only scope.
- **Added** `test_graph_invokes_supervisor_then_core_data` — `build_core_graph` + `ainvoke`; asserts audit trail includes supervisor routing and CoreDataAgent lookup.

### `tests/test_supervisor_routing.py`

- **Added** `test_routing_non_core_attributes`
- **Added** `test_supervisor_agent_routes_to_core_data` (no `response` on supervisor output)
- **Added** not-found assertions: no ingest / `provided_data` language

### `tests/test_core_data_agent.py`

- **Added** `test_core_data_agent_non_core`

## Removed earlier (1000–1050, not re-done here)

- `test_ingest_new_person`, `test_ingest_validation_failure`, `test_run_query_echoes_thread_id_on_ingest`
- Ingest routing / `persist_after_validation` tests

## Verification

```bash
uv run pytest -q   # 22 passed
uv run ruff check tests
```

## Tests to re-add when internal data addition returns

- Public ingest via `provided_data` on `PersonQuery`
- Graph enrich → validator loop
- `response_ingest_success` / `response_ingest_failure` outcomes
- MCP `submit_person_data` integration tests
