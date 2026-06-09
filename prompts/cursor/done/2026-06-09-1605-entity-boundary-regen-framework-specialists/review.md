# Review: Entity boundary fixup — `1605`

**Reviewer:** Grok  
**Date:** 2026-06-09  
**Verdict:** **Approved**

---

## Fix coverage (Slice 7 blocking nit)

| Item | Status |
|------|--------|
| Four framework specialists regenned from template | Pass |
| No `context.seed` in `src/agents/specialists/*_specialist.py` | Pass |
| `import_module` demographic path uses `entity_id` + `bind` | Pass |
| On-disk scan test (`test_framework_specialists_on_disk_use_bind_not_seed`) | Pass |

## Tests

- `test_specialist_entity_vocab.py`: 7/7 smoke (incl. new bind tests)
- `test_entity_boundary.py`: 3/3 smoke
- Full smoke: **210 passed**

Framework modules are gitignored; on-disk regen + tests are the contract (same as fixup `1350`).

---

## Gate

Clears Slice 7 (`1600`) for combined commit with this fix.