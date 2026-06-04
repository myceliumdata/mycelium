# Slice 1530 — eliminate-core (reprocess)

## Claim

Moved `prompts/cursor/next/2026-06-09-1530-eliminate-core-reprocess.md` → `prompts/cursor/in-progress/2026-06-09-1530-eliminate-core-reprocess/prompt.md`, then delivered here.

## Summary

Removed the privileged `core_data` specialist. Identity resolution and name-only responses now flow through `agents.seed` + `supervisor_agent`; dispatch only runs when `route` is set.

| Component | Change |
|-----------|--------|
| `src/agents/core_data.py` | Deleted |
| `src/agents/supervisor.py` | `find_by_key` → `matched_persons` / `context`; direct `PersonResponse` when `route=None` |
| `src/agents/dispatch.py` | No fallback; `RuntimeError` if route unregistered |
| `src/agents/registry.py` | Empty `_SEED_REGISTRY`; no `core_data` import path |
| `data/agent_registry.json` | `core_data` entry removed |
| `src/agents/__init__.py` | Export `supervisor_agent` only |
| `bin/reset-mycelium` | No `CORE_AGENT_NAME` preserve logic |
| Tests | Graph/supervisor/registry updated; `test_core_data_agent.py` module skip |

## Scoped files

- `src/agents/supervisor.py`, `dispatch.py`, `registry.py`, `__init__.py`
- `src/agents/core_data.py` (deleted)
- `data/agent_registry.json`
- `bin/reset-mycelium`
- `tests/test_core_graph.py`, `test_supervisor_routing.py`, `test_core_data_agent.py`

## Verification

```text
$ uv run ruff check src/agents/supervisor.py src/agents/dispatch.py src/agents/registry.py src/agents/__init__.py tests/test_core_graph.py tests/test_supervisor_routing.py tests/test_core_data_agent.py
All checks passed!

$ uv run pytest -m smoke -q
25 passed, 9 deselected in 0.87s

$ uv run pytest -m full -q -k "query_existing_person or query_missing_person or query_non_core_attributes"
3 passed, 31 deselected in 0.13s

$ bin/reset-mycelium --dry-run --all
(reset plan printed; no core_data preserve; specialists listed for removal)
```

Runtime grep (`supervisor`, `dispatch`, `registry`, `graphs/core`, `reset-mycelium`): no `core_data` references.

## Scope confirmation

Only 1530 slice work (no specialist template, context builder, or later slices).

**Ready for next slice:** `2026-06-09-1540-specialist-template-base-reprocess.md`
