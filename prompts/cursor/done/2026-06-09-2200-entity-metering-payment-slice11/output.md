# Slice 11 — Payment settlement

## Summary

Implemented payment settlement behind the Slice 10 metering negotiation gate. When `metering.payment.enabled` is true, quotes must be **`paid`** (via `pay_quote`) before `quote_id` unlocks work. CRM defaults keep metering and payment **disabled** — no regression on existing flows.

## Code changes

| Module | Change |
|--------|--------|
| `src/network/payment.py` | `PaymentProvider` protocol, `MockPaymentProvider`, `CreditPaymentProvider`, `X402StubPaymentProvider`, `settle_quote()`, bypass helpers |
| `src/network/credits.py` | Atomic `credits.json` ledger (`tenant` → `balance_usd`) |
| `src/network/quotes.py` | `mark_paid()`, quote payment fields, `accept(require_paid=…)` |
| `src/network/metering_policy.py` | `PaymentPolicy` + `metering.payment` block parsing |
| `src/network/paths.py` | `credits_path`, `MYCELIUM_CREDITS_PATH` |
| `src/agents/metering_gate.py` | `payment_required` gate; auto-settle on bypass |
| `src/agents/responses.py` | `response_payment_required()` |
| `src/agents/dispatch.py` | Route `payment_required` before `quote_required` |
| `src/models/state.py` | `metering_payment_required`, outcome docs |
| `src/mycelium_mcp/server.py` | `pay_quote` MCP tool; `query_entity` docstring |
| `src/network/introspection.py` | Settlement flow policy strings |
| `examples/networks/crm/network.json` | `metering.payment.enabled: false` (documented) |

## Docs

- `docs/architecture.md` — negotiation vs settlement diagram
- `docs/plans/entity-protocol-and-registry-program.md` — Slice 11 shipped
- `docs/plans/entity-metering-payment-phase11.md` — status → implemented
- `docs/plans/entity-metering-payment-implementation.md` — status → shipped

## Tests

**`tests/test_entity_payment.py`** — 8 smoke tests:

| Test | Assert |
|------|--------|
| `test_payment_disabled_quote_id_without_pay` | Slice 10 path when payment off |
| `test_mock_settle_then_accept` | quote → pay → assembled |
| `test_payment_required_before_settle` | `quote_id` before pay → `payment_required` |
| `test_credit_insufficient` | Credit provider error |
| `test_credit_success` | Deduct balance, work runs |
| `test_x402_stub_proof` | `x402:test:` proof only |
| `test_auto_settle_bypass` | `MYCELIUM_AUTO_SETTLE_QUOTES=1` |
| `test_load_metering_policy_parses_payment` | Policy parse |

**Regression:** `test_entity_metering.py` (20) + `test_entity_research_gate.py` + `test_entity_growth.py` — **40 passed**.

## Bypass env

- `MYCELIUM_AUTO_SETTLE_QUOTES=1` — skip payment gate when metering on (also implied by `MYCELIUM_AUTO_ACCEPT_QUOTES`)

## Flow (payment.enabled)

```
query_entity → quote_required
pay_quote(quote_id) → paid
query_entity + quote_id → assembled
```

`quote_id` before `pay_quote` → `payment_required` (echoes quote).

## For Grok + Paul

- Mark **Slice 11 — Payment settlement** done in `TODO.md`
- Queue empty after this slice; next planned item is **Slice 12 — HTTP query gateway** (if still on roadmap)
- Review folder: `prompts/cursor/done/2026-06-09-2200-entity-metering-payment-slice11/`
- Suggested commit message (after review):

```
Add payment settlement (Slice 11): pay_quote, PaymentProvider, paid gate.

Wire mock/credit/x402-stub settlement behind metering quotes; payment_required
outcome when quote_id sent before pay_quote. CRM keeps payment disabled.
```

- **Did not edit `TODO.md`** (per governance)
