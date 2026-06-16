# Specialist storage — minisql_v1 migration

## Summary

Implemented **`migrate_to("minisql_v1")`** for `SpecialistStorage` with shared module `src/storage/minisql_v1.py`. Threshold-gated migration copies JSON to `storage.sqlite`, renames JSON to `storage.json.pre-minisql-v1`, updates strategy. `load`/`save` branch on strategy; protocol snapshots unchanged.

## Key changes

| Area | Change |
|------|--------|
| `src/storage/minisql_v1.py` | `migrate_versioned_provenance_v1_json`, `load_payload`, `save_payload`, entity + field tables |
| `src/agents/specialists/base.py` | `migrate_to`, `load`, `save`, `sqlite_file`, strategy-aware `_ensure_initialized` |
| `tests/test_specialist_minisql_v1.py` | Backup, roundtrip, threshold trigger, idempotent migrate, 60-record smoke |
| `docs/architecture.md` | minisql_v1 addendum |

CRM capstones unchanged (under default threshold 50).

## Verification

```bash
./bin/ci-local
# CI local: all steps passed.
# 457 passed, 95 deselected
```

## For Grok + Paul

- **Timing test 3:** Paul + Grok run manual gate per `docs/manual-checks/2026-06-17-storage-evolution-timing-gates.md` (Lahman benchmark not in CI).
- After test 3 recorded: move `hold/2026-06-17-2300-entity-registry-storage-evolution.md` → `next/`.
- Suggested commit:

```
feat(storage): minisql_v1 specialist migration behind optimize_storage threshold
```

- Do not commit from Cursor unless Paul asks.
