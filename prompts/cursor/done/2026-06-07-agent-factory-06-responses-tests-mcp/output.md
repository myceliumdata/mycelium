# agent-factory-06-responses-tests-mcp — Output

## Claim

Moved `prompts/cursor/next/2026-06-07-agent-factory-06-responses-tests-mcp.md` → `in-progress/.../prompt.md` before implementation.

## Summary

- **`responses.py`**: `specialist: str | None = None` on `response_found`, `response_not_found`, `response_non_core`; non-core message adds `(via {specialist})` when specialist is set and not `core_data`; debug includes `specialist=` when present
- **`core_data.py`**: passes `specialist="core_data"` to all response builders (no `via` suffix for core)
- **`conftest.py`**: `reset_agent_factory` in session cleanup (registry reset was already present)
- **`test_core_graph.py`**: `temp_storage` fixture adds `MYCELIUM_AGENT_REGISTRY_PATH`, `MYCELIUM_SPECIALISTS_DIR`, `MYCELIUM_AGENT_DATA_DIR` + registry/factory resets; non-core test expects `via demographic_specialist` (first routed specialist owns `age` only)
- **`mcp/server.py`**: `list_specialist_routing` returns real registry entries (`specialists` list, Phase 2 message)

## Test/fixture changes (Guard rule)

```
 tests/conftest.py       |  2 +
 tests/test_core_graph.py | 18 +++++++++++++++---
```

Test/fixture changes strictly limited to the described env/resets in `temp_storage` and enhanced `test_query_non_core_attributes` assertions. No unrelated restorations.

Note: non-core graph test expects `x_handle` in **debug** (classifications) but not message — specialist routes to `demographic_specialist` which researches only its category attrs (`age`).

## Verification

### Smoke

```
$ uv run pytest -m smoke -q
27 passed, 9 deselected
```

### Full targeted

```
$ uv run pytest -m full -q -k "non_core or query_non_core or supervisor or graph or factory or registry"
7 passed, 29 deselected
```

### Ruff

```
All checks passed!
```

### Manual CLI (age)

```
message: "... still researching age (via demographic_specialist)."
debug: specialist='demographic_specialist'; classifications=[...]
```

Real run may create `demographic_specialist.py` under `src/agents/specialists/` (intended for non-test usage).

## Scope

Only modified:
- `src/agents/responses.py`
- `src/agents/core_data.py`
- `tests/conftest.py`
- `tests/test_core_graph.py`
- `src/mycelium_mcp/server.py`

## Ready for slice 07

`2026-06-07-agent-factory-07-polish-refine-verify.md` — final polish, LLM refine, full verification matrix.
