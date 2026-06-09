# Output — Entity outcome infrastructure (Phase 2, slice `1100`)

## Summary

Hardened **outcome consistency** across every `QueryResponse` exit path. No new negotiation logic. Public `outcome` now mirrors debug `outcome=` on all builders and error fallbacks.

## Changes

| File | Change |
|------|--------|
| `src/agents/responses.py` | `response_non_core` public + debug outcome → `assembled` (per locked spec: same shape as post-specialist) |
| `src/graphs/core.py` | Graph empty-response fallback sets `outcome="error"` |
| `src/mycelium_mcp/server.py` | MCP internal-error JSON includes `outcome` + `suggestions`; schema description documents new fields |
| `src/models/state.py` | `QueryResponse.outcome` / `suggestions` field descriptions updated |
| `src/network/introspection.py` | `policy.outcome` — every response includes machine-readable outcome |
| `tests/test_query_response_outcomes.py` | **New** — table-driven builder matrix + MCP schema smoke |
| `tests/test_supervisor_routing.py` | Assert `outcome` on found / not_found / non-core routing paths |
| `README.md` | Response shape paragraph: `outcome` + `suggestions` on CLI/MCP JSON |

## Outcome matrix (after slice 2)

| Path | `outcome` |
|------|-----------|
| `response_found` | `found` |
| `response_assembled` | `assembled` |
| `response_not_found` | `not_found` |
| `response_entity_unresolved` | `entity_key_unresolved` |
| `response_non_core` | `assembled` |
| Graph empty fallback | `error` |
| MCP internal error | `error` |

## Tests

```bash
uv run pytest tests/test_query_response_outcomes.py -m smoke -q   # 8 passed
uv run pytest -m smoke -q                                           # 172 passed, 2 pre-existing flakes
```

Pre-existing flakes (unchanged): `test_bootstrap_fails_when_unconfigured` (env `MYCELIUM_NETWORK=crm`), `test_create_specialist_writes_files_and_registers` (LLM research `pending` vs `na`).

## For Grok + Paul

- Mark **Slice 2 (`1100`)** done in `TODO.md` / program index when reviewed.
- **`response_non_core` rule:** public outcome is `assembled` (not `non_core_requested`); debug `outcome=` matches. Pre-specialist routing shape aligns with post-specialist assembled responses.
- Admin UI outcome badges remain deferred per [`admin-ui-backlog.md`](../../../docs/plans/admin-ui-backlog.md).
- Queue **Slice 3 (`1200` entity-unknown-mvr)** when ready.

## Exit criteria

- [x] Every documented response path sets non-null `outcome`
- [x] MCP `mycelium://schema/query-response` includes `outcome`, `suggestions`
- [x] Smoke tests green (minus known flakes)
