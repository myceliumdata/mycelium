# Why a data factory (not MCP on raw data)

**Status:** Product direction (June 2026) — motivates baseball example and warehouse work  
**Mechanics:** [`baseball-example-program.md`](../../plans/baseball-example-program.md) · [`architecture.md`](../../architecture.md) § Overview

---

## The short answer

Mycelium exists because **exposing raw data through MCP and letting agents figure it out per question does not scale** — economically, latency-wise, or architecturally.

The framework is a **factory for prepared data**: networks declare ontology, specialists own domains, bootstrap builds registries and warehouses, and the two-step query protocol delivers **scoped artifacts** (identity, researched attrs, computed stats) with provenance — not repeated micro-reads against source tables.

---

## The triggering experience

Paul asked an agent for a modest analytics question over an MCP server exposing **600+ API endpoints**: average calls per hour per endpoint over four months.

Answering required **hundreds of thousands** of MCP calls. Token budgets exhausted every ~2 hours. The job took **over a week** of repeated prompting.

The insight: sticking MCP on raw data is like sending a robot to mine and refine every iPhone material from scratch for each device. LLMs *can* do anything; they **should not** do everything per query.

---

## What agents need instead

| Raw MCP + tables | Mycelium-style factory |
|------------------|------------------------|
| Discover schema every question | Network ontology + `describe_network` catalog |
| Repeated identical reads | Resolve → scoped deliver; specialist cache |
| Human BI guesses baked in | Agent-managed derivations with lineage |
| No cost visibility | Metered quotes before expensive work (CRM) |
| Static organization | Organization evolves with query patterns (baseball franchise vs fan team) |

Agents are faster and more unpredictable than human dashboard users. The factory must be **adaptable** — specialists, derivations, and retention change as demand appears, not only at initial schema design time.

---

## Two example networks, one factory pattern

**CRM (`crm-seeded`):** thin identity registry + **web-researched** extended attributes. Specialists own categories; Tavily fills cache misses. Demonstrates negotiation, metering, and versioned provenance on ephemeral sources.

**Baseball (`baseball`):** **authoritative tabular** ground truth (Lahman warehouse) + **computed** derivatives (`career_hr`, future `career_avg`). Web research is supplemental and policy-gated — not the path for batting stats. Demonstrates manifest-driven resolve, computation-centric provenance, and emergent organization (fan team vs franchise).

Both use the same public protocol (two-step query, specialist dispatch, `versions[]`). The **data preparation strategy** differs per network pack.

---

## Derivatives and retention (direction, not v1 policy)

Agents should eventually decide what to **cache** vs **compute once and discard**:

- One-shot answers: compute, return, drop when economics say so
- Durable series (e.g. franchise lifetime batting average): keep when recompute cost dominates storage cost

Humans are poor at per-field retention tuning. Deferred until metering and lineage signals exist — see [warehouse-factory-stack.md](warehouse-factory-stack.md) § Storage policy.

---

## Blockchain-scale motivation (brief)

Fully indexing blockchains produces volumes and refresh cadence (new data every block) that amplify the same factory problem. Baseball exercises the factory on **slow-moving authoritative CSVs**; chain indexing is a future stress test for backfill, freshness entitlements, and query pools — see [metering-economics.md](metering-economics.md).

---

## What we deliberately did not do

| Alternative | Why we rejected it |
|-------------|-------------------|
| “Smart MCP” over vendor APIs only | No governed ontology, provenance, or cross-client cache economics |
| Precompute all human BI upfront | Agents ask finer-grained, unpredictable questions |
| One global schema for all domains | Networks own MVR, categories, and specialist strategies |
| Skip provenance to save tokens | Agents cannot audit or avoid duplicate production without lineage |

---

## Related

- Warehouse execution stack: [warehouse-factory-stack.md](warehouse-factory-stack.md)
- Two-step deliver contract: [two-step-query-protocol.md](two-step-query-protocol.md)
- Sources vs computation in provenance: [computation-centric-provenance.md](computation-centric-provenance.md)