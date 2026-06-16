# Output — specialist minisql_v1 incremental per-entity writes

## Summary

Specialist `minisql_v1` hot path no longer reloads and rewrites the full SQLite store on each bind. `write_fields` / `read_fields` use per-entity `load_entity` + `save_entity` upserts. Bulk `load()` / `save()` / `save_payload` remain for migration and diagnostics. `write_bind_fields_multi` rollback snapshots one entity per category instead of deep-copying the full store.

## Files changed

| File | Change |
|------|--------|
| `src/storage/minisql_v1.py` | `load_entity_record`, `upsert_entity_record`, `delete_entity_record`; shared `_write_entity_fields` / `_write_all_records`; schema ensured once per connection via `_ensure_schema` |
| `src/agents/specialists/base.py` | `load_entity`, `save_entity`, `delete_entity` (minisql incremental + JSON fallback) |
| `src/agents/specialists/agent.py` | `write_fields` / `read_fields` minisql branch; per-entity rollback in `write_bind_fields_multi` |
| `tests/test_specialist_minisql_incremental.py` | New — unrelated-entity preservation, no table-wide DELETE, rollback, bulk roundtrip |
| `docs/architecture.md` | Paragraph on per-entity upsert hot path |
| `docs/manual-checks/2026-06-17-storage-evolution-timing-gates.md` | Test 6 row already present (no numbers recorded) |

## Exit criteria

| # | Status |
|---|--------|
| E1 | `write_fields` on `minisql_v1` upserts single entity without table-wide DELETE |
| E2 | Unrelated entities unchanged after incremental write (test proves) |
| E3 | `write_bind_fields_multi` rollback uses per-entity snapshots |
| E4 | Migration + bulk `save_payload` still work |
| E5 | `./bin/ci-local` green — **470** smoke tests passed |
| E6 | Paul timing test 6 — pending manual run |

## For Grok + Paul

- **Queue timing test 6** after approval: baseball benchmark with incremental specialist writes. Expect a large drop vs test 5 (hours → minutes target). Record `real` in `docs/manual-checks/2026-06-17-storage-evolution-timing-gates.md` Test 6 row.
- **Progress slice (`2355`)** can run after this commit or in parallel — it is orthogonal (stderr progress during bootstrap). Recommended order: approve this slice → timing test 6 → then progress slice if still queued.
- Incremental upsert still runs `DELETE FROM field_records WHERE entity_id = ?` for the touched entity before re-inserting fields (correct full-entity replace for that row). No `DELETE FROM field_records` without `WHERE`.

**Suggested commit message:**

```
perf(specialist): incremental minisql_v1 per-entity upserts

Stop full-table DELETE/INSERT on each write_fields; load/save one
entity on minisql_v1 hot path. Per-entity rollback in
write_bind_fields_multi. Bulk save_payload retained for migration.
```
