# Data factory origin — why raw data + MCP is not enough

**Date:** 2026-06-14  
**Participants:** Paul + Grok  
**Status:** Origin story — product motivation, not a spec  
**Related:** [`mycelium_lahman_design_prompt.md`](../mycelium_lahman_design_prompt.md) (baseball second example), [`architecture.md`](../../architecture.md)

---

## The triggering experience

Paul was using an MCP server that exposed **total API query counts per second** across **600+ endpoints**. The ask was modest in human terms:

> Graph the **average API calls per hour** for all endpoints over a **four-month** period.

An agent pointed at the MCP server set to work. Answering that “simple” question required **hundreds of thousands** of MCP calls. Every ~2 hours Paul ran out of tokens. The job took **over a week**, with Paul returning repeatedly to prompt the agent to continue.

---

## The insight

**Sticking an MCP server on top of raw data is close to useless** for non-trivial analytics.

Analogy: sending a capable robot to Africa and asking it to mine all raw materials in an iPhone, refine them, shape them, and assemble the device. In theory possible someday; in practice insane — years of work, enormous cost. Today’s LLMs are like those future robots: they *can* do anything, but they **should not**, especially for data.

Paul needed a **factory for data**, but not the old way (guess what human customers will want upfront). The factory must be **adaptable to agentic clients** that are faster and ask **unpredictable, finer-grained** questions.

The only workable model: **agents in control of the factory** — organizing and deriving data based on client needs. Organization and process **change over time** as query patterns evolve.

---

## Implications for Mycelium (high level)

| Raw MCP + tables | Mycelium-style factory |
|------------------|------------------------|
| Agent discovers schema per question | Network ontology + specialists + governed stores |
| Repeated micro-reads | Resolve → deliver on scoped, prepared artifacts |
| Static human BI guesses | Agent-managed derivations with provenance |
| No eviction policy | Economic tradeoffs: cache vs recompute (future) |

**CRM example** today: thin identity registry + **researched** extended attributes (web sources, `versions[]`).

**Baseball example** (planned): multi-grain registries, Lahman warehouse, **agent-chosen derivations** (career totals, team lifetime batting average time series, etc.) — exercises the factory idea on **tabular** authoritative data instead of live research.

---

## Derivative retention (explore later — not in scope now)

Agents should decide what derived artifacts to **maintain** vs **compute once and discard**:

- **One-shot** answers: compute, return, delete when economics say so.
- **Durable series**: e.g. **team batting average across franchise lifetime** — very expensive to compute; new base data arrives ~once per year (contrast: blockchain-style sources where new data arrives every block).

Humans are bad at cache/retention tradeoffs; agents can weigh **cost to store** vs **cost to recompute** if metering and lineage exist. Deferred to later programs — noted here so baseball/Lahman design does not prematurely freeze a retention policy.

---

## Open design threads (June 2026)

- **Two registry entry points** in one `baseball` network: player MVR and team-season MVR (fields TBD).
- **`id` vs source keys:** protocol `id` replaces client use of Lahman `playerID`; whether `playerID` can *be* the registry `id` is a separate implementation choice (see design discussion 2026-06-14).
- **Complete Lahman ER map:** pending Paul sharing the actual 2025 CSV bundle locally (Box link not machine-readable).

---

*Archived from Paul + Grok design session, June 2026.*