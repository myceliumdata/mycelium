# Review: Specialist storage — threshold-based `optimize_storage()` check

**Verdict:** **Approved**  
**Reviewer:** Grok  
**Date:** 2026-06-17

---

## CI

| Suite | Result |
|-------|--------|
| `./bin/ci-local` (Grok re-run) | **451 passed**, 94 deselected; ruff clean; admin-ui build ok |

Matches Cursor `output.md` claim.

---

## Delivery

| Artifact | Status |
|----------|--------|
| `src/agents/specialists/agent.py` | ✅ `optimize_storage_threshold()`, threshold-aware `optimize_storage()` |
| `tests/test_specialist_optimize_storage.py` | ✅ New smoke tests (6) |
| `docs/architecture.md` | ✅ Migration policy addendum |
| `prompts/cursor/done/.../prompt.md` + `output.md` | ✅ |
| Prompt removed from `next/` | ✅ Only slice 2 remains |

---

## Spec compliance

| # | Criterion | Status |
|---|-----------|--------|
| 1 | Base `optimize_storage()` uses strategy guard + threshold + `record_count()` | ✅ |
| 2 | Env `MYCELIUM_OPTIMIZE_STORAGE_THRESHOLD` works (incl. invalid → 50) | ✅ |
| 3 | CRM specialists unchanged | ✅ |
| 4 | Smoke tests: below/at/migrated guard/write path/subclass threshold | ✅ |
| 5 | `./bin/ci-local` green | ✅ |
| 6 | `test_specialist_agent_class.py` green (`MigratingSpecialist` subclass override unaffected) | ✅ |

Locked decisions S1–S7: Pass.

---

## Diff reviewed

- `src/agents/specialists/agent.py`
- `tests/test_specialist_optimize_storage.py`
- `docs/architecture.md` (addendum lines only)

---

## Design critique

**Strong:**

- Strategy guard before `record_count()` avoids JSON load when already on `minisql_v1` — matches S3.
- Per-instance policy on base class; CRM thin subclasses inherit without copy-paste — matches S1/S2.
- `_maybe_optimize_storage()` unchanged; `NotImplementedError` still swallowed until slice 2 — S7 safe.
- Tests cover env override, migrated guard (spy on `record_count`), end-to-end write with mocked `migrate_to`, and subclass `optimize_storage_threshold()` override.

**Honest limits (non-blocking):**

1. **S4 wording:** Locked decision mentioned “class attribute override”; implementation uses **method** override only (`optimize_storage_threshold()`). Architecture doc matches method override — sufficient for v1.
2. **Env edge cases:** Non-integer env falls back to 50; negative threshold not validated (would always migrate). Unlikely misconfiguration — document if ops knobs grow.
3. **`record_count()` on hot path:** When on JSON strategy, every write still loads full storage for count check once threshold evaluation runs — acceptable until slice 2 migration; entity slice is separate bottleneck for baseball bootstrap.

---

## Nits

None blocking. Optional follow-up: validate `MYCELIUM_OPTIMIZE_STORAGE_THRESHOLD` ≥ 1 in slice 2 when migration is real.

---

## For Paul

**Commit message:**

```
feat(specialists): threshold-based optimize_storage check on base agent
```

**Next:** Cursor picks up `prompts/cursor/next/2026-06-17-2100-specialist-minisql-v1-migrate.md` (slice 2).

**Manual gate after slice 2:** timing test 3 per `docs/manual-checks/2026-06-17-storage-evolution-timing-gates.md`; then release slice 4 from `hold/`.

**Push:** Local only until program milestone — no `origin` push unless you ask.