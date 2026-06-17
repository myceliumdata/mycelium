# Output — 2026-06-17-2100-query-grain-router

**Completed by:** Grok (Cursor server died mid-slice; Paul authorized Grok to finish).

## Summary

Implemented multi-grain step-1 query routing: per-grain fan-out with bind-field filtering, 0-hit lazy-alias retry on closed grains, LLM grain disambiguation (trigger A), cross-grain `ambiguous` → `lookup_suggested` with per-candidate `grain`, optional `EntityQuery.grain` override, and `delivery.grain` honored on step 2.

## Files

| Area | Files |
|------|-------|
| Router | `src/agents/query_grain_router.py` |
| Disambiguation | `src/agents/grain_disambiguation.py` |
| Resolve / deliver / dispatch | `src/agents/target_resolve.py`, `target_deliver.py`, `dispatch.py` |
| Models / delivery | `src/models/state.py`, `src/network/delivery.py` |
| MCP / introspection | `src/mycelium_mcp/server.py`, `src/network/introspection.py` |
| Docs | `docs/query-grain-router.md`, `docs/architecture.md` (runtime store link) |
| Tests | `tests/test_query_grain_router.py` (8 smoke) |

## Grok fixes (post-Cursor)

1. **Test fixtures** — team disambiguation entities use `name: "Washington"` (exact bind match) so both grains hit.
2. **Test isolation** — baseball tests use `monkeypatch.setenv` for all `MYCELIUM_*` paths (no env pollution into CRM tests).
3. **MCP schema** — restored `required_fields` text accidentally truncated in QueryResponse description.
4. **Introspection** — removed duplicate `bind_index` line from 1800 merge artifact.

## Verification

```
./bin/ci-local — green (493 smoke passed)
```

## Exit criteria

| # | Status |
|---|--------|
| E1 | Pass — fan-out + per-grain filter |
| E2 | Pass — 0-hit alias retry pipeline |
| E3 | Pass — disambiguation trigger A + mock tests |
| E4 | Pass — 3c `lookup_suggested` + `grain` |
| E5 | Pass — `delivery.grain` on step 2 |
| E6 | Pass — `docs/query-grain-router.md` with mermaid |
| E7 | Pass — no baseball/Lahman in `src/` |
| E8 | Pass — `./bin/ci-local` green |

## For Grok + Paul

- **MCP clients:** document `EntityQuery.grain` and multi-grain `suggestions[].grain` in client examples when baseball goes live.
- **Derivative `create_pending`:** still deferred (closed grains only on 0-hit).
- **Optional follow-up:** extend `bin/smoke-baseball-e2e` with team-grain scenario now that router lands.
- **1800 slice:** WIP hunks (`default_seed`, `rows[]`, `seed-bootstrap.md`, CRM seed fixtures) remain unstaged — do not mix into this commit.

## Suggested commit message

```
feat(resolve): multi-grain query router and delivery grain

Fan-out lookup per MVR grain with LLM disambiguation on multi-grain
hits; 0-hit lazy-alias retry; cross-grain ambiguous uses lookup_suggested.
```