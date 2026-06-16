# Specialist storage — threshold-based optimize_storage check

## Summary

Base `SpecialistAgent` now evaluates **per-instance** migration policy before writes: strategy guard (`versioned_provenance_v1` only), then `record_count()` vs configurable threshold (default 50, env `MYCELIUM_OPTIMIZE_STORAGE_THRESHOLD`). `migrate_to("minisql_v1")` still raises `NotImplementedError` until slice 2 — swallowed as before.

## Key changes

| Area | Change |
|------|--------|
| `src/agents/specialists/agent.py` | `optimize_storage_threshold()`, threshold-aware `optimize_storage()` |
| `tests/test_specialist_optimize_storage.py` | Below/at threshold, env override, migrated guard, write path, subclass threshold |
| `docs/architecture.md` | Migration policy addendum |

CRM specialists unchanged — inherit base policy via thin subclasses.

## Verification

```bash
./bin/ci-local
# CI local: all steps passed.
# 451 passed, 94 deselected
```

## For Grok + Paul

- **Slice 2 ready:** `2026-06-17-2100-specialist-minisql-v1-migrate.md` (already in `next/`).
- Optional pre-slice-2 timing baseline: `docs/manual-checks/2026-06-17-storage-evolution-timing-gates.md`.
- Suggested commit:

```
feat(specialists): threshold-based optimize_storage check on base agent
```

- Do not commit from Cursor unless Paul asks.
