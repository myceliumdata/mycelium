# Review: 2026-06-14-1215-admin-query-confirm-new-entity-wire

**Verdict: Approved**

## CI

| Step | Result |
|------|--------|
| `./bin/ci-local` (Grok, 2026-06-14) | **Pass** — 404 smoke passed, 26 deselected; ruff clean; admin-ui build ok |
| Cursor `output.md` claim | 404 passed — matches |

## Delivery

| Artifact | Present |
|----------|---------|
| `src/mycelium_admin/server.py` — `AdminQueryRequest.confirm_new_entity` | ✅ |
| `EntityQuery` construction forwards field | ✅ |
| `tests/test_admin_daemon.py` — confirm create smoke test | ✅ |
| `output.md` / `prompt.md` | ✅ |

## Diff reviewed

- `src/mycelium_admin/server.py`
- `tests/test_admin_daemon.py`
- `prompt.md`, `output.md`

## Spec compliance

| Exit criterion | Pass |
|----------------|------|
| `confirm_new_entity` on `AdminQueryRequest` | ✅ |
| Passed to `EntityQuery` in `POST /query` | ✅ |
| Smoke: suggested → confirmed create | ✅ |
| UI out of scope (unchanged) | ✅ |
| `./bin/ci-local` green | ✅ |

## Legacy / dual-path

No other admin query fields changed. MCP/CLI paths unaffected.

## Tests

`test_admin_query_confirm_new_entity_creates` mirrors Check 0c-iv admin path — correct two-step POST sequence.

## Design critique

**Strong:** Minimal two-line wire; test closes the gap left by slice `1200` review. Default `False` preserves existing clients.

**Nits:** None blocking. UI still sends `confirm_new_entity` on id mode until slice `1220` — queued.

## For Paul

**Commit message:**

```
fix(admin): wire confirm_new_entity through POST /query

Forward confirm_new_entity from AdminQueryRequest to EntityQuery so the
admin UI checkbox can create after lookup_suggested.
```

**Next:** Slice `1220` (UI polish nits) still in `next/`. Check 0c-iv admin confirm path unblocked after this commit + restart-admin.