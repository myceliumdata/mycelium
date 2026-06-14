# Review — Slice 1520: Status surfaces — target resolve JSON (D2-b)

**Verdict:** ✅ **Approved**

**Reviewer:** Grok  
**Date:** 2026-06-14  
**CI:** `./bin/ci-local` green — **427 passed**, 26 deselected

---

## Scope check

| Requirement | Status |
|-------------|--------|
| CLI `--id` + `--lookup-json`; hard remove `--entity` | ✅ |
| Admin `GET /status` `id` param; remove `entity` | ✅ |
| `NetworkStatusSummary` → `resolve`, `resolve_matches`, … | ✅ |
| `build_network_status(resolve_id, resolve_lookup)` | ✅ |
| Id path → `lookup_by_id`; lookup path → `resolve_status_for_target_lookup` | ✅ |
| No `resolve_entity_for_lookup` on status path | ✅ grep clean in introspection/main/server/tests |
| Inspect exact only — no fuzzy suggestions | ✅ `test_status_exact_inspect_no_fuzzy` |
| Human formatters print `Resolve:` | ✅ |
| Admin UI types + `inspectStatusParams` + drill-down header | ✅ |
| Mandatory smokes + admin `test_status_by_id` | ✅ |
| Manual gate doc Check 1/7 updated | ✅ |
| No `TODO.md` edit | ✅ |

---

## What looks good

- **Clean D2-b shape:** `status_to_dict` omits null `resolve` and strips unset id/lookup keys inside `resolve` — JSON stays tight.
- **Mutual exclusion** enforced consistently: CLI `ValueError`, admin `400`, `build_network_status` guard.
- **Id drill-down** is a direct registry read (no resolution helper) — correct for inspect semantics.
- **Breaking change is intentional and tested:** `entity_key` absent from overview and drill-down payloads; fuzzy near-miss test replaced with exact-only assertion.
- **`resolve_entity_for_lookup` retained** for 1530 removal — status path no longer calls it.

---

## Polish backlog (1560)

| Item | Status after 1520 |
|------|-------------------|
| **P1–P4** | Unchanged — still 1560 |
| **P5** | Unchanged (none from 1510) |
| **P6** | **None** — `resolve_suggestions` / `resolve_required_fields` UI branches are forward-compatible; inspect path correctly leaves them empty under exact-only resolution |

---

## CI

```
./bin/ci-local — all steps passed
427 passed, 26 deselected
```

Full integration (`pytest -m full`) not required — not program final slice.

---

## Commit

```
feat(status): target resolve JSON and id/lookup-json inspect inputs
```

**Breaking:** CLI `--entity` and admin `?entity=` removed; status JSON uses `resolve` / `resolve_*` fields.

**Next slice:** `1530-legacy-graph-removal`.