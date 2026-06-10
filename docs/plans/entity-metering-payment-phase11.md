# Payment settlement — Slice 11 (design)

**Status:** **Implemented** (Slice 11) — Cursor: `prompts/cursor/done/2026-06-09-2200-entity-metering-payment-slice11/` · Spec: [`entity-metering-payment-implementation.md`](entity-metering-payment-implementation.md)  
**Program:** [`entity-protocol-and-registry-program.md`](entity-protocol-and-registry-program.md)  
**Depends on:** Slice 10 (`quote_required`, `QuoteStore`, `metering_gate`)  
**Prerequisite reading:** [`entity-metering-design-phase9.md`](entity-metering-design-phase9.md) (negotiation), Slice 10 implementation

---

## The distinction (important)

We have been loose with **"x402-style metering."** Slice 11 clarifies two layers that must not be conflated:

| Layer | Name | Transport | What it does |
|-------|------|-----------|--------------|
| **Negotiation** | **Priced commit** (Slice 9–10) | **MCP** (`query_entity`) | Multi-phase entity + workload negotiation; `quote_required` + full `Quote` JSON; accept via `quote_id` on retry |
| **Settlement** | **Payment** (Slice 11+) | **HTTP x402**, credits, wallet MCP, etc. | Move money; mark quote `paid` in `QuoteStore`; gate checks `paid` not just `accepted` |

**x402 is not useless** — it is the wrong tool for **negotiation**. It does not replace `Quote.line_items`, `cache_state`, `avoidable_cost`, or the Paul/Jan marginal story.

**x402 is a candidate settlement backend** once the agent has agreed to a quote.

### Terminology (use consistently)

| Say | Don't say (when meaning negotiation) |
|-----|--------------------------------------|
| Priced commit, quote protocol, metering negotiation | "x402 phases" |
| x402 settlement, HTTP 402, PaymentProvider | "x402 metering" (ambiguous) |

Update all program docs accordingly.

---

## Why MCP and HTTP stay separate

- **MCP (stdio)** — `query_entity` is JSON-RPC tool calls, not HTTP. Literal HTTP 402 does not appear on the stdio wire.
- **Negotiation** needs multiple rounds, rich quotes, and cache economics — beyond a single 402 envelope.
- **x402** — HTTP 402 → sign USDC → `PAYMENT-SIGNATURE` → facilitator verify/settle. One-shot per HTTP resource.

### Where the worlds meet

```
┌──────────────────────────────────────────────────────────────┐
│ NEGOTIATION (MCP-native — shipped Slice 10)                  │
│   query_entity → quote_required + Quote                      │
│   query_entity + quote_id → (if paid) work runs               │
└────────────────────────────┬─────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────┐
│ SETTLEMENT (Slice 11 — pluggable PaymentProvider)            │
│   MockProvider      — CI, proof="test:…"                     │
│   CreditProvider    — API key → tenant ledger (CRM)          │
│   X402Provider      — facilitator HTTP; testnet wallet       │
│   WalletMcpBridge   — funded middleware MCP (Coinbase pattern)│
└──────────────────────────────────────────────────────────────┘
```

The commit gate today accepts `quote_id` when quote status is `accepted`. Slice 11 adds: **production/consumption quotes require `paid` before accept** (unless bypass / credits / auto-accept).

---

## x402 integration patterns (not mutually exclusive)

### Pattern A — PaymentProvider behind the gate (recommended default)

1. Agent receives `quote_required` over MCP.
2. Agent (or operator runtime) calls `PaymentProvider.settle(quote_id)` — internally may use x402 HTTP to facilitator.
3. `QuoteStore` → `status: paid`, `payment_proof` recorded.
4. Agent retries `query_entity` with `quote_id`.

MCP carries negotiation; settlement is **application-internal** or a **second MCP tool** (`pay_quote`).

### Pattern B — Wallet-equipped MCP middleware (Coinbase demo)

Claude does not hold a wallet. A **middleware MCP server** with `EVM_PRIVATE_KEY` calls x402-paid HTTP APIs on the agent's behalf. For Mycelium: middleware settles quotes, then calls Mycelium with `quote_id`.

See [Coinbase x402 MCP example](https://docs.cdp.coinbase.com/x402/mcp-server).

### Pattern C — Streamable HTTP MCP + 402 on `tools/call`

MCP server over HTTPS; middleware returns 402 on paid `tools/call`. Flat per-call pricing — awkward for multi-line-item quotes unless envelope is extended. Deferred.

### Pattern D — Optional HTTP query gateway

Separate REST/HTTP API for `query_entity` semantics; literal x402 on that surface. MCP path unchanged. For non-MCP clients.

---

## Slice 11 objective

Add **`PaymentProvider`** and wire it between **quote issuance** and **quote accept**:

| Component | Responsibility |
|-----------|----------------|
| `PaymentProvider` (protocol) | `settle(quote_id, proof?) → PaidReceipt` |
| `MockPaymentProvider` | CI; no chain |
| `CreditPaymentProvider` | Deduct tenant balance (API key → principal) |
| `X402PaymentProvider` | Facilitator verify/settle (testnet in integration tests) |
| Gate change | `quote_id` honored only when `status == paid` (configurable per network) |

**Non-goals (Slice 11):**

- Rebates / pool ledger (still Q9j-B)
- Blockchain freshness meters
- Literal 402 on stdio MCP

---

## Testing strategy (Slice 11)

| Tier | What | Who pays |
|------|------|----------|
| **CI** | `MockPaymentProvider` | Nobody |
| **Integration** | `X402PaymentProvider` + testnet wallet script | Funded test hot wallet (not Claude) |
| **Agent E2E** | LangGraph test agent with `pay_quote` tool | Test wallet or credits |
| **Claude Desktop** | Credits or auto-accept / pre-paid quotes | Operator ledger or bypass |

**Claude is not a payment client.** Fund a **test harness agent** or **middleware MCP server** for real E2E.

---

## Open questions — **LOCKED** (Paul, June 2026 — one slice)

| ID | Decision |
|----|----------|
| Q11a | Mock default; credit via `payment.provider: credit` |
| Q11b | `pay_quote` MCP tool + internal `settle_quote()` |
| Q11c | HTTP gateway → Slice 12 |
| Q11d | `paid` required for all billable quotes when `payment.enabled` |

---

## Relationship to slices

| Slice | Ships |
|-------|--------|
| **9** | Negotiation design (locked) |
| **10** | `quote_required`, stores, gate, `quote_id` accept (no money) |
| **11** | `PaymentProvider`, paid gate, mock + credit + x402 providers |
| **12** | Rebate/pool ledger, blockchain workloads, async quotes (TBD) |

---

## Doc updates required when Slice 11 ships

- [`entity-protocol-and-registry-program.md`](entity-protocol-and-registry-program.md) — program goal line 5
- [`entity-metering-design-phase9.md`](entity-metering-design-phase9.md) — glossary cross-link
- [`docs/architecture.md`](architecture.md) — negotiation vs settlement diagram
- Conversation index — note terminology correction