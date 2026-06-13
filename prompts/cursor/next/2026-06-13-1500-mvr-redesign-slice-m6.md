# MVR redesign — Slice M6 (metering + quote_id)

**Program:** [`docs/plans/mvr-redesign-program.md`](../../docs/plans/mvr-redesign-program.md)  
**Prerequisite:** M5 reviewed and approved  
**Depends on:** M4 step-1 resolve; M5 step-2 deliver; existing `metering_gate` / `QuoteStore`

---

## Objective

Wire **metering** into the target two-step protocol: step-1 may return **`quote_required`** (with `delivery_id` + quote binding scope); step-2 requires valid **`quote_id`** when `metering.enabled`. Batch line items ≈ N singles per program R9.

**Not in M6:** create-on-0 (M7), batch provenance shape (M8), CLI/MCP migration (M9).

---

## Read first

- [`docs/plans/mvr-redesign-program.md`](../../docs/plans/mvr-redesign-program.md) — R8, R9, step-1/2 quote examples
- [`src/agents/metering_gate.py`](../../src/agents/metering_gate.py)
- [`src/network/quotes.py`](../../src/network/quotes.py)
- [`src/agents/dispatch.py`](../../src/agents/dispatch.py) — `target_resolve_node`
- M5: [`src/agents/target_deliver.py`](../../src/agents/target_deliver.py), `delivery_scope_attrs`

---

## Tasks

1. **Step-1 metering** — when `metering.enabled` and delivery/research is billable, return `quote_required` with `total_matches`, `delivery`, and `quote` workload referencing `delivery_id` + bound attrs (replace M4/M5 `lookup_resolved`-only shortcut for metered networks).

2. **Quote workload** — extend `WorkloadSpec` (or parallel) to reference `delivery_id` + entity count / attrs from `DeliveryScope`; persist quote linked to delivery scope.

3. **Step-2 gate** — when metering on, require paid/accepted `quote_id` matching delivery scope before deliver; `payment_required` / `principal_required` as today where applicable.

4. **Batch metering** — N matches in scope → line items ≈ N × single-entity research/delivery (no silent truncation).

5. **Tests** — smoke: metered step-1 `quote_required`; step-2 without quote blocked; step-2 with accepted quote delivers; free network still `lookup_resolved` → deliver without quote.

---

## Constraints

- **Do not edit `TODO.md`.**
- **Do not** implement create-on-0 (M7).
- **Do not** remove legacy `entity_key` metering path until M7–M9.

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

`prompts/cursor/done/2026-06-13-1500-mvr-redesign-slice-m6/` — queue M7 in For Grok + Paul.

Do not commit until review.

---

## Exit criteria

- Metered step-1 → `quote_required` when appropriate
- Step-2 gated on `quote_id` when metering enabled
- Batch line items reflect N entities in scope
- Smoke green; legacy path still works on metered networks via `entity_key`