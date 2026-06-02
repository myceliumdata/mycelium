# Task 1100 output

## Changes

### `src/agents/__init__.py`
- Removed `enrich_agent` and `validator_agent` imports and `__all__` entries.
- Public exports are now only `core_data_agent` and `supervisor_agent`.
- `enrich.py` / `validator.py` remain on disk but are no longer part of the package surface.

### `src/graphs/core.py`
- Already wired from task 1070: `START → supervisor → core_data → END`, no enrich/validator nodes or imports.
- No edits required for this task.

## Verification

- `uv run pytest -q`: **22 passed**
- Graph path and `run_query` covered by existing tests (`test_graph_invokes_supervisor_then_core_data`, `test_run_query_*`).
- `from agents import core_data_agent, supervisor_agent` succeeds.

## Result

The active graph is query-only: supervisor classifies and routes (`route="core_data"`); `core_data_agent` performs lookup and builds `PersonResponse`.
