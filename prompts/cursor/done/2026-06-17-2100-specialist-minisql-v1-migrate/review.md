# Review: Specialist storage — `migrate_to("minisql_v1")`

**Verdict:** **Approved**  
**Reviewer:** Grok  
**Date:** 2026-06-17

---

## CI

| Suite | Result |
|-------|--------|
| `./bin/ci-local` (Grok re-run) | **457 passed**, 95 deselected; ruff clean; admin-ui build ok |

Matches Cursor `output.md` claim (+6 tests vs slice 1).

---

## Delivery

| Artifact | Status |
|----------|--------|
| `src/storage/minisql_v1.py` | ✅ Shared module: schema, migrate, load/save payload |
| `src/agents/specialists/base.py` | ✅ Strategy-aware init, load/save, `migrate_to` |
| `tests/test_specialist_minisql_v1.py` | ✅ 6 smoke tests |
| `docs/architecture.md` | ✅ `minisql_v1` addendum |
| `prompts/cursor/done/.../prompt.md` + `output.md` | ✅ |
| Prompt removed from `next/` | ✅ Queue empty until slice 4 released |

---

## Spec compliance

| # | Criterion | Status |
|---|-----------|--------|
| 1 | `migrate_to("minisql_v1")` works for `SpecialistStorage` | ✅ |
| 2 | Post-migration `write_fields` preserves versioned bind values | ✅ (`test_optimize_storage_triggers_migration`, roundtrip) |
| 3 | Shared `minisql_v1` module for slice 4 reuse | ✅ |
| 4 | Threshold-triggered migration tested | ✅ env threshold `2`, end-to-end via `SpecialistAgent` |
| 5 | `./bin/ci-local` green | ✅ |
| 6 | CRM capstones + Program 2 matrix | ✅ (included in smoke run) |

Locked decisions M1–M8: Pass (JSON backup, idempotent migrate, strategy metadata, `storage.sqlite`).

---

## Diff reviewed

- `src/storage/minisql_v1.py` (full file)
- `src/agents/specialists/base.py` (`migrate_to`, `load`, `save`, `_ensure_initialized`)
- `tests/test_specialist_minisql_v1.py` (full file)
- `docs/architecture.md` (addendum lines)

---

## Design critique

**Strong:**

- Clean split: shared `minisql_v1.py` with entity/field tables + JSON blobs per field — matches M7 pragmatism and slice 4 reuse path.
- Migration path: copy → rename JSON backup → update strategy with `last_migrated` — matches M5/M6.
- `load`/`save` branch on `current_strategy()`; protocol layer unchanged.
- Tests cover backup file, version structure roundtrip, shared-module migrate, threshold E2E, idempotency, 60-record smoke.

**Honest limits (non-blocking):**

1. **`save_payload` is full replace** — each save deletes and re-inserts all field rows (transactional, but O(n) per write). Still avoids multi-MB JSON rewrites; true incremental updates are follow-up.
2. **`category` param unused** in `migrate_versioned_provenance_v1_json` — reserved for slice 4 entity grain labeling; fine.
3. **Baseball bootstrap perf:** Specialist categories may migrate mid-bootstrap once ≥50 records, but **entity registry per-row `_save()` is unchanged** — timing test 3 vs 3.5h baseline may show only modest gain until slice 4.

---

## Nits

None blocking.

---

## For Paul

**Commit message:**

```
feat(storage): minisql_v1 specialist migration behind optimize_storage threshold
```

**Timing test 3:** Re-run baseball refresh benchmark; compare to **baseline 12,600 s (~3.5 h)** in `docs/manual-checks/2026-06-17-storage-evolution-timing-gates.md`. Record in Test 3 row.

**After test 3:** Move `prompts/cursor/hold/2026-06-17-2300-entity-registry-storage-evolution.md` → `prompts/cursor/next/` for Cursor.

**Push:** Local only until program milestone.