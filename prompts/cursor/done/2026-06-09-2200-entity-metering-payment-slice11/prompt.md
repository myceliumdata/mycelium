# Task: Payment settlement — Slice 11

> **READY** — Slice 10 + fix `2110` approved. Move to `in-progress/` to start.

**Read these first (mandatory):**
- `prompts/cursor/WORKFLOW.md`
- [`docs/plans/entity-metering-payment-phase11.md`](../../docs/plans/entity-metering-payment-phase11.md) — design (negotiation ≠ settlement)
- [`docs/plans/entity-metering-payment-implementation.md`](../../docs/plans/entity-metering-payment-implementation.md) — **locked implementation spec**

**Depends on:** Slice 10 metering + Slice 10 fix (`2110`).

---

## Objective

Implement **payment settlement** in one slice: `PaymentProvider`, `pay_quote` MCP tool, `paid` gate, mock + credit + x402-stub providers. Do **not** build HTTP query gateway (Slice 12).

Paul: full Slice 11 as planned — no split.

---

## Locked decisions

| Item | Choice |
|------|--------|
| Q11a | Mock default; credit via `payment.provider: credit` |
| Q11b | `pay_quote` MCP tool + `settle_quote()` internally |
| Q11c | No HTTP gateway |
| Q11d | `paid` required for all billable quotes when `payment.enabled` |

**Terminology:** Negotiation = MCP quotes (Slice 10). Settlement = this slice. x402 = settlement stub only, not negotiation.

---

## Deliverables

### Code

1. **`src/network/payment.py`** — `PaymentProvider`, `MockPaymentProvider`, `CreditPaymentProvider`, `X402StubPaymentProvider`, `get_payment_provider()`, `settle_quote()`.
2. **`src/network/credits.py`** — `credits.json` ledger under network_root.
3. **`src/network/quotes.py`** — `mark_paid()`; statuses `pending` → `paid` → `accepted`; accept honors payment policy.
4. **`src/network/metering_policy.py`** — parse `metering.payment` block.
5. **`src/agents/metering_gate.py`** — require `paid` before accept when `payment.enabled`; emit `payment_required` when `quote_id` but not paid.
6. **`src/agents/responses.py`** — `response_payment_required()`.
7. **`src/mycelium_mcp/server.py`** — `pay_quote` tool; update `query_entity` docstring (quote → pay → accept loop).
8. **`src/network/introspection.py`** — settlement flow policy strings.
9. **`src/network/paths.py`** — credits path + env.
10. **`examples/networks/crm/network.json`** — `metering.payment.enabled: false` (documented).

### Tests

**`tests/test_entity_payment.py`** — per implementation spec table. Metering + entity regression green.

### Docs

- **`docs/architecture.md`** — mermaid or ascii: MCP negotiation vs PaymentProvider settlement.
- **`docs/plans/entity-protocol-and-registry-program.md`** — Slice 11 shipped; add outcomes `payment_required`, `principal_required`.

### Bypass env

- `MYCELIUM_AUTO_SETTLE_QUOTES=1` — skip payment gate when metering on (tests/demos). Document alongside `MYCELIUM_AUTO_ACCEPT_QUOTES`.

---

## Flow (payment.enabled)

```
query_entity → quote_required
pay_quote(quote_id) → paid
query_entity + quote_id → assembled (or research path)
```

If `query_entity + quote_id` before pay → `payment_required` (echo quote).

---

## Non-goals

- Real x402 facilitator / mainnet in CI
- HTTP 402 query API
- Rebate/pool ledger
- Admin UI
- **Do not edit `TODO.md`**

---

## Governance

- CRM defaults keep metering and payment **disabled** — zero regression on existing tests.
- Match atomic JSON store patterns from `entitlements.py` / `quotes.py`.
- Ruff clean.

---

## Deliverables folder

`prompts/cursor/done/2026-06-09-2200-entity-metering-payment-slice11/` with `prompt.md`, `output.md`.

---

## Exit criteria

- [ ] `tests/test_entity_payment.py` + `tests/test_entity_metering.py` + entity smokes pass
- [ ] `pay_quote` MCP tool works in isolation (unit/integration)
- [ ] `architecture.md` diagram present
- [ ] For Grok + Paul section in `output.md`