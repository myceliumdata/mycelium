# Review: Seed vs specialists boundary — Slice 7

**Reviewer:** Grok  
**Date:** 2026-06-09  
**Verdict:** **Approved** *(fix `1605` approved — Q7b complete)*

---

## Spec coverage

| Item | Status |
|------|--------|
| `context.py` — `entity_id`, `bind`, stripped specialist storage | Pass |
| `build_context_node` — no top-level `seed` blob | Pass |
| Factory template + research Jinja use `bind` | Pass |
| `storage_strategy.json` documents bind boundary | Pass |
| Legacy `name`/`employer` ignored on read (`strip_bind_fields`) | Pass |
| New factory writes omit bind fields | Pass |
| `core_identity.py` deleted | Pass |
| `routing.py` uses `agents.seed.find_by_key` | Pass |
| `reset_core_identity` removed from conftest/tests | Pass |
| No runtime `core_identity` imports in `src/` | Pass |
| CRM `examples/networks/crm/specialists/contact_specialist.py` regenned | Pass |
| Admin backlog #8 already listed | Pass |
| **Q7b: all framework reference specialists regenned** | Pass (`1605`) |

## Tests

- `test_entity_boundary.py`: 3/3 smoke (+ 2 unit)
- Full smoke: **208 passed**

Committed with fix `1605` (Grok, 2026-06-09).

---

## Non-blocking (polish post–8)

- **P11** — Supervisor/validate paths still embed `context["seed"]` pre–`build_context`; harmless today but confusing vs new shape.
- **P2** (carry-over) — Weak specialist-invoke assertions in entity-protocol tests.

---

## Gate

**Slice 8 (`1700`)** unblocked.