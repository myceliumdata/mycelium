# Metering Slice 11 — fix slice

**Status:** Shipped (fix slice 2210 — review pending)  
**Depends on:** Slice 11 shipped (`prompts/cursor/done/2026-06-09-2200-entity-metering-payment-slice11/`)  
**Program:** [`entity-protocol-and-registry-program.md`](entity-protocol-and-registry-program.md)

---

## Objective

Close review nits from Slice 11 payment settlement and related metering doc hygiene. No HTTP gateway, no real x402 facilitator, no rebate/pool ledger (Slice 12).

---

## Fixes (locked)

| # | Gap | Fix |
|---|-----|-----|
| F1 | `settle_quote` ignores quote expiry | Shared `quote_is_expired(quote)` in `quotes.py`; reject settlement with clear `PaymentError` when expired; reuse in `accept()` (DRY) |
| F2 | Credit deduct before `mark_paid` | Credit provider validates balance only in `settle()`; deduct **after** successful `mark_paid` in `settle_quote()`; if deduct fails, revert quote `paid → pending` and raise |
| F3 | No MCP `pay_quote` test | Round-trip test importing `pay_quote` from `mycelium_mcp.server` (mirror `test_mcp_query_entity_round_trip_json`) |
| F4 | Implementation spec exit criteria stale | Mark `[x]` on satisfied exit criteria in `entity-metering-payment-implementation.md` and `entity-metering-implementation.md`; set Slice 11 program status to **review approved** |
| F5 | `MYCELIUM_X402_FACILITATOR_URL` undocumented | One-line note in `payment.py` module docstring + `architecture.md` settlement section (stub today; real wiring Slice 12) |
| F6 | Expired quote after pay edge case | E2E: `quote_id` on expired **paid** quote → accept fails gracefully (not `assembled`); message/debug indicates expiry |

---

## Non-goals

- HTTP query gateway (Slice 12)
- Real x402 facilitator HTTP client
- Rebate / pool ledger
- Admin UI payment surfaces
- Pluggable `QuoteProvider` loading
- **Do not edit `TODO.md`**

---

## F1 — Quote expiry helper

Add to `src/network/quotes.py`:

```python
def quote_is_expired(quote: Quote, *, now: datetime | None = None) -> bool:
    ...
```

- Parse `expires_at` with same logic as `accept()` today.
- `settle_quote()` calls this before provider settlement; error: `quote {id!r} expired`.
- Refactor `accept()` to call `quote_is_expired()` instead of inline parse.

---

## F2 — Credit settlement ordering

**Target invariant:** tenant balance changes only after quote is durably `paid`.

1. `CreditPaymentProvider.settle()` — validate `principal` + `has_sufficient_balance`; return `PaidReceipt` **without** deducting.
2. `settle_quote()` — after `mark_paid()` succeeds, if provider is credit, call `credit_store.deduct()`.
3. On deduct failure after `mark_paid`, add `QuoteStore.revert_paid(quote_id)` (or equivalent) restoring `pending` and clearing payment fields; raise `PaymentError`.

Add `CreditStore.has_sufficient_balance(tenant_id, amount)` if cleaner than try/except on deduct.

---

## Tests

Extend `tests/test_entity_payment.py`:

| Test | Assert |
|------|--------|
| `test_settle_quote_rejects_expired` | Issue quote; set `expires_at` in past (direct store edit or monkeypatch); `settle_quote` → `PaymentError` match `expired` |
| `test_credit_deduct_after_mark_paid` | Credit success path still works; balance unchanged if `mark_paid` mocked to fail |
| `test_mcp_pay_quote_round_trip` | `pay_quote('{"quote_id":…}')` → JSON `status: paid`; then `query_entity` + `quote_id` → `assembled` |
| `test_accept_rejects_expired_paid_quote` | Paid quote past expiry + `quote_id` → not `assembled` (gate does not accept) |

Regression:

```bash
uv run pytest tests/test_entity_payment.py tests/test_entity_metering.py \
  tests/test_entity_research_gate.py tests/test_entity_growth.py -q
```

Expect **44+** tests green (4 new + 40 existing).

---

## Doc touch-ups

- `entity-metering-payment-implementation.md` — exit criteria `[x]`; status → shipped + fix pending
- `entity-metering-implementation.md` — exit criteria `[x]` where satisfied
- `entity-protocol-and-registry-program.md` — add **Slice 11 fix** row; Slice 11 status → review approved
- `architecture.md` — `MYCELIUM_X402_FACILITATOR_URL` future hook note (if not already present)

---

## Exit criteria

- [x] F1–F6 implemented
- [x] 4+ new tests; full payment + metering + entity regression green
- [x] Ruff clean
- [x] No behavior change when `payment.enabled: false`