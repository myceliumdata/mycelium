# Peer-aware specialists + analytic orchestration (design lock)

**Date:** 2026-06-21  
**Participants:** Paul + Grok  
**Status:** Design locked — implementation deferred; metering review required before cohort-scale delivers  
**Builds on:** [`2026-06-19-warehouse-factory-layer3-specialist-emergence.md`](2026-06-19-warehouse-factory-layer3-specialist-emergence.md), [`2026-06-21-baseball-bio-research-specialist.md`](2026-06-21-baseball-bio-research-specialist.md), [`docs/architecture.md`](../../architecture.md) § Supervisor (no god agents)

---

## Problem

Cross-domain analytic questions combine **warehouse facts** with **dimensions Lahman does not carry**. Example (Paul):

> In 1985, which group had the best overall batting average — whites, African Americans, Latinos, or Asians?

| Sub-problem | Ground truth |
|-------------|--------------|
| 1985 batting per player | Lahman `Batting` (warehouse) |
| Player race/ethnicity | **Not in Lahman** (`People` has birth country, not race) |
| Group comparison | Computation over enriched cohort |

**Correction (June 2026):** Product and analytic specialists do **not** call Tavily for bio-owned facts. **Bio** owns race; bio uses **web research on miss**. Product/analytic **delegates to bio** via the specialist protocol.

---

## Routing model — Option 2 (locked)

Paul prefers **peer-aware specialists** over a central “god” router.

| Approach | Verdict |
|----------|---------|
| **Option 1 — God specialist / dispatcher** | Reject — conflicts with architecture lock: **no god agents**; supervisor stays narrow |
| **Option 2 — Peer-aware delegation** | **Adopt** — each specialist knows ontology + peer map; delegates through **framework dispatch**, not private Tavily stacks or ad-hoc LLM routers |

**Nuance:** Option 2 means **distributed ownership + centralized protocol** (`dispatch_read_fields`, planned peer invoke). Specialists must not each reimplement supervisor classification logic.

---

## Locked decisions (Paul, 2026-06-21)

### Q1 — Ontology: race lives on bio

| Item | Lock |
|------|------|
| Category | `bio` → `bio_specialist` |
| Primary label | `race` |
| Synonym | `ethnicity` → intent slug `race` (M4b pattern) |
| Lahman | No manifest alias v1 — research path on miss |
| Policy | `guide.md` paragraph: bucket semantics, low confidence → N/A |

### Q2 — Orchestration cost

| Item | Lock |
|------|------|
| Technical budget cap | **None** — full cohort fan-out allowed when client accepts quote |
| Economics | **Metering** prices the job; client pays for Tavily/LLM volume |
| Follow-on | **Metering review** — quote must reflect orchestrated work (see § Metering) |

### Q3 — Caching

Bio owns per-player `race` in `agents/bio/storage.json`. Product/analytic reads via **dispatch only** — never re-research, never duplicate Tavily for bio-owned fields.

### Q4 — Client shape + cohort discovery

**Mode A (primary):** one analytic `requested_attributes` label (e.g. `best_batting_group_by_race`) routed to **analytic/product** specialist.

**Critical:** The **step-1 supervisor does not enumerate players**. Only the specialist that **knows the warehouse** discovers the cohort (e.g. 1985 Red Sox from `Batting` ⋈ team scope), **then** fans out to bio for `race` per `playerID`.

```text
Client step-1:
  lookup: { team: "Boston Red Sox" }
  scope: { yearID: "1985" }
  requested_attributes: [best_batting_group_by_race]

Supervisor:
  → classify one attr → analytic_specialist
  → does NOT plan per-player bio calls

Analytic specialist:
  1. Warehouse: discover player cohort (meaningful 1985 batting for scoped team)
  2. For each player_id: dispatch_read_fields(bio, race) / invoke bio on miss
  3. Aggregate batting average by race group; deliver winner
```

**Mode B (secondary):** client explicitly requests `race` + `batting_average` with scope — supervisor fans out bio + batting in parallel (existing graph); aggregation still analytic specialist unless client computes externally.

NL `question` on `EntityQuery`: still deferred ([`unlikely/README.md`](../unlikely/README.md)).

### Q5 — Provenance

**Shallow** (v1): analytic attr gets `computation.inline` + `parameters` (year, team scope, group definitions, counts). Per-player `race` provenance stays in **bio storage**; batting provenance in warehouse paths. Deep lineage: deferred ([`2026-06-19-deep-provenance-lineage-expansion.md`](2026-06-19-deep-provenance-lineage-expansion.md)).

---

## Specialist tiers (clarified)

```text
Warehouse stat specialists
  manifest aliases + derive-on-miss (sqlite sandbox)
  domain-bounded recipes; peer map in briefing

Bio specialist
  warehouse People reads + research_on_miss (Tavily) for bio-owned attrs (race, hall_of_fame_year, …)

Product specialists (roster, franchise)
  cross-table artifacts within Lahman; peer-aware; delegate bio-owned dims via dispatch
  full warehouse catalog in briefing; no hard table firewall (soft hints)

Analytic / orchestrating product tier (emergent)
  discovers cohort from warehouse
  orchestrates peer specialists (bio fill, batting reads)
  LLM derive for novel aggregates when needed
  promotion path: repeat patterns → committed product recipe or manifest alias
```

**Product specialist self-awareness (direction):** briefing includes ontology peer map (`categories.json`), `guide.md` excerpts, full `warehouse_manifest` — not table ACLs. See manifest promotion conversation in `TODO.md`.

---

## Framework work (not yet built)

| Piece | Description |
|-------|-------------|
| **Specialist briefing** | Load category description + peer map (`assigned_agent`, example attrs) at `run()` |
| **Peer read** | `dispatch_read_fields(peer_category, entity_id, fields)` — existing protocol |
| **Peer fill** | Orchestrated bio invoke on cache miss (same deliver or sub-plan) — **design TBD** |
| **`ProductTeamSpecialist` + orchestration** | Framework shell for scope-aware cache + peer delegation hooks |
| **Analytic category** | New ontology category + thin pack specialist (name TBD) |
| **Bio `race`** | Ontology + `research_on_miss` (blocked on bio slice `2410` design lock; `race` can follow) |

**Explicit non-goals v1:**

- God router agent
- Product specialists calling Tavily for bio-owned attributes
- Hard per-deliver research caps (metering replaces technical throttles)

---

## Metering (review required)

Paul lock: **as long as the job is properly priced, cost volume is acceptable — the client pays.**

Implications for analytic orchestration:

| Challenge | Direction |
|-----------|-----------|
| Variable cohort size | Quote should incorporate **discoverable work**, not a blind flat fee |
| Multi-hop (warehouse → N × bio research → aggregate) | Line items: cohort discovery, cache hits vs research misses, aggregate compute |
| Step-1 quote timing | May need **quote after cohort discovery** (or priced estimate + reconcile) — open design |
| Repeat delivers | Bio cache hits reduce marginal cost — quote/entitlement should reflect cache |

**Action:** Review metering from orchestration perspective before shipping cohort-scale analytic delivers. See `TODO.md` → **Metering — orchestrated multi-specialist quotes**.

Related: [`docs/architecture/whys/metering-economics.md`](../../architecture/whys/metering-economics.md), entity metering implementation plan.

---

## Example walkthrough (Red Sox 1985)

1. Client accepts quote for `best_batting_group_by_race` with team + year scope.
2. `analytic_specialist` queries Lahman: player IDs with 1985 BOS batting rows.
3. For each ID: read `race` from bio storage; on miss, bio runs warehouse-then-Tavily; caches result.
4. Pool H and AB by race bucket for 1985; compute group BA; pick best group.
5. Return assembled result + shallow computation provenance.

Second query same players: bio cache hits → faster, cheaper deliver.

---

## Dependencies / ordering

| Prerequisite | Notes |
|--------------|-------|
| Bio research hybrid (`2410`) | `research_on_miss`, `WarehouseResearchPlayerSpecialist`; add `race` after bio path proven |
| Metering review | Before live analytic guinea pig with large cohorts |
| `ProductTeamSpecialist` framework tier | Optional parallel — roster/franchise + orchestration hooks |
| Manifest derivative promotion | Separate track — `career_avg`/`ops` promotion vs analytic tier |

---

## Open (small)

- Exact analytic attr label + category name in `categories.json`
- Quote mechanics: pre-cohort estimate vs post-discovery quote vs two-phase step-1
- `guide.md` race/ethnicity policy text
- Gate strategy for analytic scenario (mocked bio + fixture cohort vs live Tavily subset)

---

*Archived June 2026.*