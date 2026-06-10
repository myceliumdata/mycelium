# Task: Entity metering Slice 11 — fix slice

> **READY** — Slice 11 reviewed and approved; fix nits before Slice 12. Move to `in-progress/` to start.

**Read these first (mandatory):**
- `prompts/cursor/WORKFLOW.md`
- [`docs/plans/entity-metering-slice11-fix.md`](../../docs/plans/entity-metering-slice11-fix.md) — **locked fix spec**
- Slice 11 output: `prompts/cursor/done/2026-06-09-2200-entity-metering-payment-slice11/output.md`
- Slice 11 review: `prompts/cursor/done/2026-06-09-2200-entity-metering-payment-slice11/review.md`

**Depends on:** Slice 11 payment settlement.

---

## Objective

Fix six review nits from Slice 11 (expiry, credit ordering, MCP test, doc hygiene). No Slice 12 scope.

---

## Fixes (implement all)

### F1 — Quote expiry in settlement

- Add `quote_is_expired(quote)` to `src/network/quotes.py`.
- `settle_quote()` rejects expired quotes before calling any provider.
- Refactor `QuoteStore.accept()` to use the same helper (no behavior change).

### F2 — Credit deduct after `mark_paid`

- `CreditPaymentProvider.settle()` validates principal + balance only — **no deduct**.
- `settle_quote()` deducts credits **after** successful `mark_paid`.
- On deduct failure: revert quote from `paid` to `pending` (new store method) and raise `PaymentError`.
- Balance must be unchanged if `mark_paid` fails (test with mock).

### F3 — MCP `pay_quote` round-trip

- Add test in `tests/test_entity_payment.py` calling `mycelium_mcp.server.pay_quote` directly (see `tests/test_entity_rename.py` for `query_entity` pattern).
- Assert JSON `status: paid`, then full flow to `assembled`.

### F4 — Doc exit criteria

- `docs/plans/entity-metering-payment-implementation.md` — mark exit criteria `[x]`.
- `docs/plans/entity-metering-implementation.md` — mark exit criteria `[x]` where satisfied.
- `docs/plans/entity-protocol-and-registry-program.md` — Slice 11 status → **review approved**; add **Slice 11 fix** subsection pointing at this slice.

### F5 — X402 facilitator env note

- Document `MYCELIUM_X402_FACILITATOR_URL` in `src/network/payment.py` module docstring and `docs/architecture.md` (future real x402; stub ignores today).

### F6 — Expired paid quote cannot unlock work

- Test: quote marked `paid` but past `expires_at`; `query_entity` + `quote_id` must **not** reach `assembled`.
- Ensure agent gets a clear outcome (re-quote or error — match existing `accept()` expiry behavior; do not silently run work).

---

## Tests

```bash
uv run pytest tests/test_entity_payment.py -q
uv run pytest tests/test_entity_metering.py tests/test_entity_research_gate.py tests/test_entity_growth.py -q
```

All must pass. Add at least 4 new tests per fix spec table.

---

## Governance

- Match existing metering/payment code style.
- CRM `metering.payment.enabled: false` unchanged.
- **Do not edit `TODO.md`.**

---

## Deliverables

`prompts/cursor/done/2026-06-09-2210-entity-metering-payment-slice11-fix/` with `prompt.md`, `output.md`.

---

## Exit criteria

- [ ] F1–F6 implemented
- [ ] 4+ new tests; payment + metering + entity regression green
- [ ] Ruff clean