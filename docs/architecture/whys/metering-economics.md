# Why predictable metering economics

**Status:** Shipped for CRM-metering example (Slices 10–11, June 2026)  
**Mechanics:** [`architecture.md`](../../architecture.md) § Metering negotiation vs payment settlement · [`entity-metering-design-phase9.md`](../../plans/entity-metering-design-phase9.md) · `examples/networks/crm-metering/`

---

## The short answer

In agentic systems, **economics must be predictable before work starts**. Metering attaches to the same two-step query spine:

- Step 1 with deliverable scope → `quote_required` + line-item **Quote** + `delivery_id`
- Client accepts → step 2 with `quote_id` + `delivery_id` → work runs

**Negotiation** (MCP `query_entity`) and **settlement** (HTTP `pay_quote` / x402) are **separate layers**. Do not call negotiation “x402 metering.”

Entity bind resolution (who is this person?) stays free; pricing applies when expensive production or consumption is about to run.

---

## Governing thesis

Unlike human SaaS users, agents compare **marginal consumption vs duplicate production** precisely. Opaque lump-sum pricing invites surprise bills and economically irrational duplicate work.

Example (CRM):

- Paul funds research for Angela Murphy @ TalentCare: quote shows `research: $2.00`, `query_value: $0.05`.
- Jan queries same entity next day — cache hit. Quote shows `query_value: $0.05` plus:

```json
"avoidable_cost": { "research_usd": 1.95, "if": "query_only_accepted" },
"funding_model": "marginal"
```

Jan’s agent routes to marginal query — not voluntary $2.00 duplicate research.

---

## Principle 1 — Entity negotiation ≠ workload pricing

Slices 1–8 outcomes (bind, validate, suggest) are unchanged. Metering hooks only when the research gate would invoke **paid work**.

| Phase | Typical cost |
|-------|--------------|
| Resolve Kalman → Kalmans (suggestions) | Free |
| Bind Paul Murphy @ Acme | Free |
| Tavily research for `email` | Quoted |

CRM needs simple research + query meters; a future blockchain network needs backfill + freshness + query pools — **same gate, different `QuoteProvider`**.

---

## Principle 2 — Three billable surfaces

Networks map workloads to one or more of:

| Surface | CRM example | Blockchain example |
|---------|-------------|-------------------|
| **Production** | Tavily research commit | Subgraph/RPC backfill |
| **Freshness** | Optional re-research SLA | Poll interval, lag bound |
| **Consumption** | Query value; query + provenance | Point reads, GraphQL allowance |

Even CRM splits **query value** vs **query with provenance** — attribution and audit cost more. Chain indexing makes the split unavoidable when sponsor A pays for indexing and querier B reads.

---

## Principle 3 — Multi-line-item quotes

Default quotes expose **per-job line items** — production + freshness + consumption in one JSON — not a single opaque total.

Agents optimize across dimensions: sponsor accepts backfill, skips freshness; querier buys query-only on cache hit. Lump sums hide the levers.

`requested_attributes` and match count (N) bound on step 1 — quote prices the frozen `delivery_id` scope, including batch N× singles.

---

## Principle 4 — Funding models are network policy

`network.json` selects `funding_model` and `QuoteProvider`. Framework ships crude defaults; networks override.

**Model B (everyone pays full research)** is supported but **not** the agentic equilibrium — legitimate only for private indexes, scope mismatch, compliance refresh, or first-mover with no shared cache.

Charging Jan full research on a public CRM entity with identical scope and valid cache is extractive; agents will treat it as hostile.

---

## Negotiation vs settlement

```text
query_entity (MCP)
  step 1 → quote_required + Quote + delivery_id
  accept → step 2 + quote_id → work

pay_quote (when payment.enabled)
  pending → paid → accepted
  quote_id before pay → payment_required
```

Test bypass: `MYCELIUM_AUTO_ACCEPT_QUOTES`, `MYCELIUM_AUTO_SETTLE_QUOTES`. Production CRM example keeps both disabled for realistic demos.

Real x402 settlement reads facilitator HTTP later; Slice 11 stub uses test proofs in CI.

---

## Relationship to two-step query

Metering is why `requested_attributes` are step-1 only and why step 1 returns empty `results[]` with a quote — see [two-step-query-protocol.md](two-step-query-protocol.md).

Unmetered networks (`baseball`) skip quotes; the resolve → `delivery_id` → deliver shape is identical.

---

## What we deliberately did not do

| Alternative | Why we rejected it |
|-------------|-------------------|
| Meter step-1 fuzzy suggestions | Negotiation should stay free; pricing attaches to deliver scope |
| Single “query fee” lump sum | Hides cache hits and avoidable duplicate cost |
| x402 on every MCP call | Conflates wallet settlement with entity protocol |
| Cap paying clients with `max_results` in v1 | Batch honesty — N matches quoted and delivered |

---

## Related

- Two-step scope binding: [two-step-query-protocol.md](two-step-query-protocol.md)
- Factory motivation (why agents need cost signals): [data-factory-origin.md](data-factory-origin.md)