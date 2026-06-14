# Review — Slice 1540: Legacy test migration and cleanup

**Verdict:** ✅ **Approved**

**Reviewer:** Grok  
**Date:** 2026-06-14  
**CI:** `./bin/ci-local` green — **400 passed**, 26 deselected

---

## Scope check

| Requirement | Status |
|-------------|--------|
| Migrate deferred `entity_key` test corpus to `lookup` / `id` / `delivery_id` | ✅ 20 modules updated |
| Remove `pytest_ignore_collect` / legacy module skip list | ✅ `conftest.py` clean |
| Zero `EntityQuery(entity_key=…)` except intentional reject tests | ✅ 2 `# type: ignore` smokes only |
| `MYCELIUM_ALLOW_LEGACY_ENTITY_KEY` absent from tests | ✅ |
| Delete redundant legacy-only modules with documented merge | ✅ 2 files deleted |
| `registry_helpers` step1/step2 helpers | ✅ |
| Smoke CI green + count reported | ✅ 400 (was 288 under 1530 skip) |
| No `TODO.md` edit | ✅ |
| Docs scrub | Deferred **1550** (per plan) |

---

## What looks good

- **`conftest.py` fully restored** — session cleanup only; P7 nit from 1530 closed.
- **`registry_helpers.resolve_and_deliver`** gives a consistent two-step pattern; migrations read clearly (e.g. `test_entity_registry_bind.py` `entity_validated` → `lookup_resolved` + `found`).
- **Sensible deletions:** `test_supervisor_routing.py` (dead `agents.routing` shim) and `test_entity_key_suggestions.py` (fuzzy/suggest covered by `test_target_step1_lookup_clarity.py` + `test_mvr_target_resolve.py`).
- **Outcome assertions updated** — no legacy outcome strings left in active tests (grep clean).
- Smoke count **288 → 400** — suite largely restored; **27 fewer** than pre-1530 (427) due to merged/deleted legacy-only cases — documented and acceptable.

---

## Polish backlog (1560)

| Item | Status after 1540 |
|------|-------------------|
| **P7** (redundant conftest skip hook) | **Closed** — entire legacy block removed |
| **P8** | **None** |

Docs still mention `MYCELIUM_ALLOW_LEGACY_ENTITY_KEY` — **1550** scope (already queued).

---

## CI

```
./bin/ci-local — all steps passed
400 passed, 26 deselected
```

Full integration (`pytest -m full`) not required — **1560** program gate.

---

## Commit

```
test: migrate suite to target protocol; remove legacy entity_key tests
```

**Next slice:** `1550-policy-docs-hygiene`.