# Review: MCP `health_check` refresh dedupe (slice 0900)

**Reviewer:** Grok  
**Verdict:** **Approved** — ready to commit and check off TODO.

## Scope compliance

| Requirement | Status |
|-------------|--------|
| Single `refresh_runtime_from_disk()` per `health_check` | **Done** — line 178, sub-checks use helpers |
| `query_person` still refreshes once per call | **Done** — via `_run_mcp_query` |
| `list_specialist_routing` still refreshes once standalone | **Done** |
| Internal helpers without refresh | **Done** — `_routing_payload`, `_execute_mcp_query` |
| No global skip flags | **Done** |
| Smoke test: health_check refresh count == 1 | **Done** |
| Smoke test: list_specialist_routing refresh count == 1 | **Done** |
| JSON shape / check keys unchanged | **Done** |
| Out of scope respected | **Yes** — server + tests only |

## Code quality

- Clean helper split: public tools wrap bootstrap + refresh; `health_check` composes helpers after one refresh.
- Error recovery stays in `_execute_mcp_query` (not duplicated).
- Tests patch at `mycelium_mcp.server.refresh_runtime_from_disk` — correct import site.

## Verification (re-run)

```
uv run pytest -m smoke -q tests/test_mcp_runtime_reload.py  →  4 passed
uv run ruff check src/mycelium_mcp/server.py tests/test_mcp_runtime_reload.py  →  clean
```

Manual smoke in `output.md`: all checks `ok`.

## Non-blocking notes

1. `health_check` now refreshes **before** storage/graph checks (slightly different ordering than nested-tool calls). Sub-checks see post-refresh state — desirable for diagnostics.
2. Docstring still says "list_specialist_routing" in prose; behavior is equivalent via `_routing_payload`. Optional one-line docstring tweak in a future polish slice.

## Success criteria

Met. Closes the follow-up noted in slice 1200 review.