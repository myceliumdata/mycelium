# Output: Simplify graph — remove ingest nodes, wire core_data (1070)

## Summary

Replaced the enrich/validator ingest loop with a query-only graph: **START → supervisor → core_data → END**.

## Graph (`src/graphs/core.py`)

| Before | After |
|--------|-------|
| Nodes: supervisor, enrich, validator | supervisor, **core_data** |
| Conditional: `route == "enrich"` | `route == "core_data"` |
| Loop enrich → validator → supervisor | `core_data` → END |

Imports: `core_data_agent` only (enrich/validator removed from graph).

## Supervisor (`src/agents/supervisor.py`)

Thin router only — sets `route: "core_data"` and audit logs. No storage access, no `PersonResponse` (built in `core_data_agent`).

## State (`src/models/state.py`)

`route` literal updated: `"enrich"` → `"core_data"`.

## Supervisor output for routing

```python
{"route": "core_data", "audit_log": [...]}
```

`_route_after_supervisor` reads `state.route == "core_data"` and edges to the `core_data` node.

## Verification

```bash
uv run pytest -q   # 18 passed
uv run ruff check src/graphs/core.py src/agents/supervisor.py src/models/state.py
```

`enrich.py` / `validator.py` remain on disk but are unwired. `agents/__init__.py` cleanup deferred to task **1100**.

## Follow-up

- **1100**: clean `agents/__init__.py` exports
- **1080**: integration tests may assert visited nodes include `core_data`
