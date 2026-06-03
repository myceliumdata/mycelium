# agent-factory-05-dispatch-graph-supervisor — Output

## Claim

Moved `prompts/cursor/next/2026-06-07-agent-factory-05-dispatch-graph-supervisor.md` → `in-progress/.../prompt.md` before implementation.

## Summary

Wired dynamic specialist routing and on-demand creation trigger (slice 05):

- `**dispatch.py**` — `specialist_dispatcher` resolves `state.route` via registry, falls back to `core_data_agent`
- `**state.py**` — `route: str | None` with Phase 2 field description
- `**graphs/core.py**` — `specialist` node + conditional; removed hardcoded `core_data` node
- `**supervisor.py**` — Phase 2 block: create specialist if missing, set `route` to `assigned_agent` (first non-unknown classification)
- **Tests** — pre-register `contact_specialist` in classifies test; new trigger test with fake `create_specialist`

Import note: `from agents.factory.agent_factory import get_agent_factory` (factory `__init__.py` does not re-export; out of scope to change).

## Test changes (Guard rule)

`git diff --stat tests/test_supervisor_routing.py`:

```
 tests/test_supervisor_routing.py | 428 +++++++++++++++++++++++++++++++++++++++
```

Test changes strictly limited to:

- `test_supervisor_agent_classifies_requested_attributes`: tmp registry + pre-register + route/audit asserts
- `test_supervisor_triggers_creation_for_unregistered_specialist`: new smoke test (~75 lines)

No unrelated restorations or refactors from other phases.

## Verification

### Smoke

```
$ uv run pytest -m smoke -q
...........................                                              [100%]
27 passed, 9 deselected in 0.22s
```

### Ruff

```
All checks passed!
```

### Manual core query

```
Found core record for Nichanan Kesonpat.
(outcome='found')
```

### Scope files touched

- `src/agents/dispatch.py` (full impl)
- `src/agents/supervisor.py`
- `src/models/state.py`
- `src/graphs/core.py`
- `tests/test_supervisor_routing.py` (listed adjustments only)

## Ready for slice 06

`2026-06-07-agent-factory-06-responses-tests-mcp.md` — `specialist=` in responses, core_data, test_core_graph fixture, MCP.