# Review — Entity metering Slice 11 (payment settlement)

**Reviewer:** Grok (June 2026)  
**Verdict:** **Approve** — spec delivered; tests green; ready to commit.

---

## Summary

Slice 11 cleanly separates **negotiation** (Slice 10 `quote_required`) from **settlement** (`pay_quote` → `paid` → `quote_id` accept). `PaymentProvider` (mock/credit/x402-stub), the paid gate in `metering_gate`, and `payment_required` outcome all match the locked Q11 decisions. CRM keeps `metering.payment.enabled: false`; no regression on default flows. Docs (`architecture.md`, program doc, phase11/implementation specs) are updated with correct terminology.

---

## Spec checklist

| Requirement | Verdict | Notes |
|-------------|---------|-------|
| `PaymentProvider` + mock/credit/x402-stub | Pass | `src/network/payment.py`; `x402` alias → stub |
| `settle_quote()` shared API | Pass | Idempotent when already `paid` |
| `pay_quote` MCP tool | Pass | Thin JSON wrapper; documented in tool docstring |
| Paid gate when `payment.enabled` | Pass | `require_paid_before_accept`; `store.accept(require_paid=…)` |
| `payment_required` outcome | Pass | Dispatch routes before `quote_required`; echoes stored quote |
| `credits.json` ledger | Pass | Atomic save; `MYCELIUM_CREDITS_PATH` |
| Quote lifecycle `pending → paid → accepted` | Pass | `mark_paid()` + `accept()` |
| Bypass env | Pass | `MYCELIUM_AUTO_SETTLE_QUOTES`; implied via `MYCELIUM_AUTO_ACCEPT_QUOTES` |
| CRM default payment off | Pass | `examples/networks/crm/network.json` |
| No HTTP gateway | Pass | Deferred per Q11c |
| Docs | Pass | `architecture.md` diagram; program outcomes table |

---

## Tests

```
uv run pytest tests/test_entity_payment.py tests/test_entity_metering.py \
  tests/test_entity_research_gate.py tests/test_entity_growth.py -q
→ 40 passed
```

| Test file | Count | Coverage |
|-----------|-------|----------|
| `test_entity_payment.py` | 8 | disabled path, mock settle, `payment_required`, credit fail/success, x402 stub, auto-settle, policy parse |
| `test_entity_metering.py` | 20 | Slice 10 + fix regression intact |
| research_gate + growth | 12 | No regression |

All implementation-spec test rows satisfied. `settle_quote()` is exercised directly; MCP `pay_quote` is a thin delegate (acceptable for this slice).

---

## Code review notes

**Strengths**

- Clear separation: negotiation gate unchanged when `payment.enabled: false`.
- `payment_required` returns the **stored** quote (not a re-priced quote) — correct agent UX.
- `settle_quote` idempotency on `paid` quotes avoids double credit deduction.
- Auto-settle bypass calls `settle_quote` then accepts with `require_paid=False` — consistent test/demo path.

**Non-blocking nits (future / Slice 12)**

1. **`settle_quote` does not check quote expiry** — a client could pay an expired quote; `accept()` would still reject. Consider validating `expires_at` in `settle_quote` or returning a clearer error.
2. **Credit deduct before `mark_paid`** — if `mark_paid` fails after `CreditPaymentProvider.settle`, balance is deducted without a `paid` quote. Unlikely (same-process file write); worth a transactional pattern if credits go production.
3. **No MCP-level `pay_quote` integration test** — `settle_quote` coverage is sufficient for Slice 11; add one if MCP wiring regresses often.
4. **`entity-metering-payment-implementation.md` exit-criteria checkboxes** still `[ ]` — update to `[x]` on commit for doc hygiene.

---

## Architecture alignment

Negotiation vs settlement distinction is correctly documented and implemented:

```
quote_required → pay_quote → query_entity + quote_id → assembled
quote_id before pay_quote → payment_required
```

Terminology in program doc uses **priced commit** (negotiation) vs **settlement** (x402/credits) — matches Paul's June 2026 locks.

---

## Recommendation

**Ship Slice 11.** Suggested commit message from `output.md`:

```
Add payment settlement (Slice 11): pay_quote, PaymentProvider, paid gate.

Wire mock/credit/x402-stub settlement behind metering quotes; payment_required
outcome when quote_id sent before pay_quote. CRM keeps payment disabled.
```

After commit: mark Slice 11 done in `TODO.md`; program doc status can move from "review pending" → shipped.

**Next:** Slice 12 scoping (HTTP query gateway, rebate/pool ledger, real x402 facilitator, async quotes — per roadmap).