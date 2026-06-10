# Task: Entity metering Slice 10 — fix slice

> **READY** — Slice 10 shipped; review nits. Move to `in-progress/` to start.

**Read these first (mandatory):**
- `prompts/cursor/WORKFLOW.md`
- [`docs/plans/entity-metering-slice10-fix.md`](../../docs/plans/entity-metering-slice10-fix.md) — **locked fix spec**
- Slice 10 output: `prompts/cursor/done/2026-06-09-2100-entity-metering-implementation/output.md`

**Depends on:** Slice 10 metering implementation.

---

## Objective

Fix five review nits from Slice 10. No payment integration (Slice 11).

---

## Fixes (implement all)

### F1 — `EntityQuery.provenance`

- Add `provenance: bool = False` to `EntityQuery` (request sources/audit trail; Q9g-A `query_provenance` meter).
- `build_workload_spec()` in `metering_gate.py` must pass `query.provenance` (not hardcoded `False`).
- `scope_hash` must differ when `provenance` toggles (already in `compute_scope_hash` — verify with test).

### F2 — `full_duplicate` E2E

- Test with `metering.enabled: true` and `default_funding_model: "full_duplicate"`.
- After Paul research + entitlement/cache hit, second query quote must include **production** line (not consumption-only).

### F3 — `meter_first_delivery: false` E2E

- Test with `meter_first_delivery: false` in metering fixture `network.json`.
- First quote on cache miss: **production only** (no consumption line).
- Second query (cache hit): consumption line present.

### F4 — `principal_required` outcome

- Replace generic `outcome: error` for metering principal failures with **`principal_required`**.
- Add `response_principal_required()` in `responses.py` (mirror `response_quote_required` style).
- Include `required_fields` empty; message explains missing principal + funding model.
- Update `QueryResponse.outcome` description and program outcome table in `entity-protocol-and-registry-program.md`.

### F5 — Sponsor E2E

- `default_funding_model: "sponsor_public"` + no `principal` on billable query → `outcome: principal_required` (not `error`).

---

## Tests

Extend `tests/test_entity_metering.py` with cases in fix spec. All prior metering tests must still pass.

```bash
uv run pytest tests/test_entity_metering.py -q
uv run pytest tests/test_entity_research_gate.py tests/test_entity_growth.py -q
```

---

## Introspection

Update `src/network/introspection.py` policy strings:
- Document optional `provenance` on `EntityQuery`.
- Document `principal_required` outcome.

---

## Governance

- Match existing metering code style.
- CRM example `network.json`: optional comment in metering block documenting `provenance` + `full_duplicate` (no behavior change; `enabled: false`).
- **Do not edit `TODO.md`.**

---

## Deliverables

`prompts/cursor/done/2026-06-09-2110-entity-metering-slice10-fix/` with `prompt.md`, `output.md`.

---

## Exit criteria

- [ ] F1–F5 implemented
- [ ] 4+ new tests; full metering suite green
- [ ] Entity protocol regression green
- [ ] Ruff clean