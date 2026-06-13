# MVR redesign — Slice M5 (step-2 deliver, metering off)

**Program:** [`docs/plans/mvr-redesign-program.md`](../../docs/plans/mvr-redesign-program.md)  
**Prerequisite:** M4 reviewed and approved  
**Depends on:** M2 `DeliveryStore`; M4 step-1 `lookup_resolved` + `delivery_id` issuance

---

## Objective

Wire **step-2 deliver** for the target protocol: `delivery_id` (+ no `quote_id` when `metering.enabled` is false) → load `DeliveryScope`, return `results[]` with registry identity (and merged attrs if `requested_attributes` were bound on step 1). **Legacy `entity_key` path unchanged.**

**Not in M5:** metering `quote_required` / `quote_id` gate (M6), create-on-0 (M7).

---

## Read first

- [`docs/plans/mvr-redesign-entity-query-examples.md`](../../docs/plans/mvr-redesign-entity-query-examples.md)
- [`src/agents/target_resolve.py`](../../src/agents/target_resolve.py)
- [`src/network/delivery.py`](../../src/network/delivery.py)
- [`src/agents/dispatch.py`](../../src/agents/dispatch.py) — `target_resolve_node`, `assemble_response_node`
- [`src/models/state.py`](../../src/models/state.py) — `entity_query_is_delivery_step()`

---

## Tasks

1. **Deliver gate** — when query is delivery step (`delivery_id`), short-circuit at graph entry (extend `target_resolve` or new `deliver` node): load scope from `DeliveryStore`; expired/unknown → `not_found`.

2. **Results assembly** — for valid scope, populate `results[]` from `entity_ids` (registry rows). Honor `requested_attributes` bound on step 1: run existing specialist merge path when attrs present; identity-only when empty.

3. **Outcomes** — `found` (no attrs) or `assembled` (attrs merged); include `provenance` block when step-1 scope had `provenance=true`.

4. **Metering off only** — reject or defer `quote_id` requirements to M6; document in `output.md`.

5. **Tests** — smoke: step-1 then step-2 roundtrip; expired `delivery_id`; legacy `entity_key` still unaffected.

---

## Constraints

- **Do not edit `TODO.md`.**
- **Do not** implement metering quote on step 2 (M6).
- **Do not** remove `entity_key` resolution (M7).

---

## Governance (mandatory)

- **Do not edit `TODO.md`.** Roadmap updates are for Grok + Paul after review.
- In `output.md`, add **"For Grok + Paul"**: what to check off, any roadmap notes.
- Cursor delivers: code, tests, task-scoped docs, and `output.md` only.

---

## Verification

```bash
./bin/ci-local
```

---

## Output

`prompts/cursor/done/2026-06-13-1400-mvr-redesign-slice-m5/` — queue M6 in For Grok + Paul.

Do not commit until review.

---

## Exit criteria

- Step-2 `delivery_id` returns `results[]` (metering off)
- Expired/invalid delivery → `not_found`
- Legacy path unchanged
- Smoke green