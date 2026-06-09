# Review: Entity registry + provisional bind — Slice 4

**Reviewer:** Grok  
**Date:** 2026-06-09  
**Verdict:** **Approved**

---

## Spec coverage

| Item | Status |
|------|--------|
| `entities.json` + atomic save (`EntityRegistry`) | Pass |
| `MYCELIUM_ENTITIES_PATH` in `runtime_path()` map | Pass |
| `EntityQuery.binding` on model + MVR normalization | Pass |
| Unknown binding keys ignored (Q4d) | Pass |
| Resolution order: bind_index → uuid → seed → suggest → negotiate | Pass |
| `entity_bound_provisional` with `id`, `name`, `employer` in results (Q4a) | Pass |
| `entity_under_specified` on partial binding | Pass |
| Duplicate bind → `found`, same id, “already bound” (Q4e) | Pass |
| Uuid `entity_key` follow-up lookup (Q4b) | Pass |
| Name-only disambiguation when 0 or 2+ registry rows (Q4c) | Pass (code; no dedicated smoke) |
| Supervisor short-circuit: no classify/specialists on bind / provisional | Pass |
| Bind + `email` same turn → provisional only, no Tavily | Pass |
| Seed `Aaron Holiday` → assembled, no registry write | Pass |
| `describe_network` policy `entity_bind` | Pass |
| No validation loop; no email research on provisional | Pass |
| `.gitignore` for runtime `entities.json` | Pass |

## Tests

- `test_entity_registry_bind.py`: 10/10 smoke
- Full smoke: **194 passed**

Left **uncommitted** until this review — correct governance.

## Non-blocking (polish post–8)

- **P4** — `describe_network` `policy.query.optional_fields` omits `binding` (instructions mention it; field list does not).
- **P5** — No smoke for Q4c name-only with two same-name registry rows (logic present in `resolve_entity`).
- **P2** (carry-over) — Specialist short-circuit still asserted via `"invoke_specialists" not in response.debug` in new bind tests.

---

## Gate

**Slice 5 (`1400` validation)** unblocked — prompt marked **READY**.