# Payment settlement — Slice 11 implementation

**Status:** Shipped + fix slice 2210 (review pending)  
**Design:** [`entity-metering-payment-phase11.md`](entity-metering-payment-phase11.md)  
**Depends on:** Slice 10 + Slice 10 fix (`2110`)  
**Paul (June 2026):** One slice — negotiation (10) + settlement (11); no split.

---

## Objective

Wire **payment settlement** behind the existing **negotiation** gate:

1. `PaymentProvider` protocol + mock, credit, x402-stub implementations.
2. `pay_quote` MCP tool + shared `settle_quote()` for tests/harness.
3. When `payment.enabled`: quotes must be **`paid`** before `quote_id` unlocks work.
4. Docs: `architecture.md` negotiation/settlement diagram; program outcome table.

**Non-goals:** HTTP query gateway (Q11c → Slice 12), rebate/pool ledger, real mainnet settlement in CI.

---

## Locked Q11 defaults (Paul waive — one slice)

| ID | Decision |
|----|----------|
| Q11a | **Mock** default provider when `payment.enabled`; **Credit** optional via `payment.provider: credit` + `credits.json` |
| Q11b | **`pay_quote` MCP tool** + internal `settle_quote(quote_id, proof?)` API |
| Q11c | **HTTP gateway deferred** (Slice 12) |
| Q11d | **`paid` required for all billable quotes** (production + consumption) when `payment.enabled` |

---

## Quote lifecycle (when `payment.enabled`)

```
pending  ──pay_quote──►  paid  ──query_entity+quote_id──►  accepted + work runs
```

When `payment.enabled` is false (default): Slice 10 behavior — `quote_id` → `accepted` directly.

Bypass unchanged: `metering.enabled: false` OR `MYCELIUM_AUTO_ACCEPT_QUOTES=1` skips metering; add `MYCELIUM_AUTO_SETTLE_QUOTES=1` to skip payment in tests if needed (or auto-settle in auto-accept path).

---

## `network.json` extension

```json
{
  "metering": {
    "enabled": false,
    "payment": {
      "enabled": false,
      "provider": "mock",
      "require_paid_before_accept": true
    }
  }
}
```

CRM example: `payment.enabled: false` (documented, no regression).

---

## Code layout

| Module | Role |
|--------|------|
| `src/network/payment.py` | `PaymentProvider` protocol, `MockPaymentProvider`, `CreditPaymentProvider`, `X402StubPaymentProvider`, `get_payment_provider()` |
| `src/network/credits.py` | `credits.json` ledger (tenant → balance_usd), atomic save |
| `src/network/quotes.py` | `mark_paid()`, status `pending\|paid\|accepted`; accept requires `paid` when payment policy says so |
| `src/agents/metering_gate.py` | Check paid before accept |
| `src/mycelium_mcp/server.py` | `pay_quote` tool |
| `src/network/paths.py` | `credits_path`, `MYCELIUM_CREDITS_PATH` |

### `PaymentProvider`

```python
class PaidReceipt(BaseModel):
    quote_id: str
    provider: str
    amount_usd: float
    proof: str | None = None
    settled_at: str

class PaymentProvider(Protocol):
    def settle(self, quote_id: str, *, proof: str | None = None, principal: BillingPrincipal | None = None) -> PaidReceipt: ...
```

**Mock:** always succeeds; proof optional `test:…`.

**Credit:** deduct `quote.total_usd` from principal.id balance; error if insufficient.

**X402 stub:** accepts proof prefix `x402:test:` only (no network); stores proof on quote; env `MYCELIUM_X402_FACILITATOR_URL` documented for future real wiring.

---

## MCP `pay_quote`

```json
{ "quote_id": "q_abc", "proof": "optional", "principal": { "kind": "tenant", "id": "acme" } }
```

Returns JSON: `{ "status": "paid", "receipt": { ... } }` or error.

Update `describe_network` / introspection: negotiation → pay_quote → query_entity+quote_id flow.

---

## New / updated outcomes

| Outcome | When |
|---------|------|
| `quote_required` | Unpaid quote needed (unchanged) |
| `payment_required` | `quote_id` present but quote not `paid` yet (payment.enabled) — echo quote, message: call `pay_quote` |
| `principal_required` | Slice 10 fix (unchanged) |

Add `payment_required` to program outcome table.

---

## Tests — `tests/test_entity_payment.py`

| Test | Assert |
|------|--------|
| payment disabled | Slice 10 path: quote_id without pay_quote works |
| mock settle + accept | quote_required → pay_quote → quote_id → assembled |
| payment_required | quote_id before pay_quote → `payment_required` |
| credit insufficient | CreditProvider + low balance → settle error |
| credit success | Deduct balance; paid; work runs |
| x402 stub proof | proof `x402:test:abc` settles |
| auto bypass | `MYCELIUM_AUTO_SETTLE_QUOTES` or combined auto-accept skips payment |

Extend metering regression; CRM default off.

---

## Doc updates (mandatory in slice)

- [`docs/architecture.md`](docs/architecture.md) — negotiation vs settlement diagram
- [`entity-protocol-and-registry-program.md`](entity-protocol-and-registry-program.md) — Slice 11 shipped, outcomes, `principal_required`
- [`entity-metering-payment-phase11.md`](entity-metering-payment-phase11.md) — status → implemented

---

## Exit criteria

- [x] All tests pass (payment + metering + entity regression)
- [x] CRM `metering.payment.enabled: false` default
- [x] `pay_quote` documented in MCP
- [x] No HTTP gateway code