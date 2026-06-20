# Why the warehouse factory stack (three layers)

**Status:** M1–M2 shipped (June 2026); M3 derive codegen queued  
**Mechanics:** [`baseball-example-program.md`](../../plans/baseball-example-program.md) · `warehouse_domains.json` · `warehouse_manifest.py` · `warehouse_resolve.py`

---

## The short answer

Baseball does not put hundreds of Lahman columns into `categories.json`. Instead:

```text
Discovery   →  describe_network + guide.md (schema catalog, conventions)
Routing     →  coarse ontology (batting, bio, …) — not 500 attribute names
Execution   →  specialist reads manifest + warehouse, computes, caches
```

Clients request named attrs (`career_hr`, `birth_date`); the framework routes to domain specialists; **manifest aliases and recipes** map attrs to warehouse operations — not a flat ontology explosion.

---

## What problem we were solving

| Anti-pattern | Cost |
|--------------|------|
| One ontology entry per Lahman column | Unmaintainable `categories.json`; classification LLM on every new stat name |
| Agent discovers SQL per query | Factory insight — repeated expensive discovery (see [data-factory-origin.md](data-factory-origin.md)) |
| Web research for ground truth stats | Wrong sources; masks warehouse path (hand-test lesson: stale research cache returned pre-warehouse values) |
| Central framework hardcodes baseball SQL | Blocks other tabular networks; violates pack vs framework split |

The warehouse factory keeps **framework generic** and **pack declarative**.

---

## Layer 1 — Discovery

`describe_network` (MCP) and `guide.md` expose:

- Record types, MVR bind fields, `new_records` policy
- Warehouse capability summary from `warehouse_domains.json`
- Example queries and naming conventions (`career_*` sums, raw People columns)

Agents learn what the network *can* answer without scanning CSV headers at query time.

---

## Layer 2 — Routing

Supervisor + classification map `requested_attributes` to **categories** (`batting`, `bio`, …) — same mechanism as CRM.

- Unknown attr on research networks → lazy Agent Factory stub (CRM path)
- Baseball pack **installs** `batting_specialist` / `bio_specialist` up front — warehouse categories must not lose to research stubs

Routing is coarse domain grain, not per-stat ontology entries.

---

## Layer 3 — Execution

On cache miss, specialist (or shared resolver) consults manifest:

| Manifest entry | Resolves to |
|----------------|-------------|
| Alias `career_hr` | `career_sum` over `Batting.HR` |
| Alias `birth_date` | raw `People.birthDate` formatted |
| Miss (M3+) | LLM codegen in sandbox → run once → cache |

Provenance records `sources[]` (dataset snapshot) + `computation` + full `parameters` including `warehouse` path and `lahman.playerID`.

**Bind fields** (`debut_team`, `debut_year`): registry ground truth — identity reads entity row, not web research, when requested as attrs.

---

## Ground truth vs web (baseball policy)

| Type | Path |
|------|------|
| Pack warehouse categories | Lahman sqlite only; unimplemented → `N/A` |
| Factory research template | Web only — CRM-shaped networks |

Baseball target waterfall:

1. Warehouse / registry when attr has declared tables or bind
2. `N/A` or explicit policy when missing
3. Web **only** for supplemental bio — never for batting stats

Clearing `agents/batting/storage.json` research history was required in hand-test when stale v1/v2 research masked M2 warehouse results.

---

## Storage policy (now vs future)

| Now | Future |
|-----|--------|
| **Always cache** `found` on deliver | Specialists evict/recompute from telemetry + metering |

Retention agent (deferred) weighs compute cost, access frequency, and storage cost — humans should not tune per-field TTL.

---

## Specialist emergence (two kinds)

**A — Lazy category (framework):** unknown attr → classify → `create_specialist` → research stub. Right for CRM; **wrong** for baseball warehouse stats.

**B — Product specialist (manual slices today):** `franchise_specialist`, cross-domain metrics when single computation + unified cache + repeat demand. Future: derive telemetry recommends promotion; human approves slice until automated.

---

## Evolution path (M1 → M5)

| Phase | Client asks | Execution |
|-------|-------------|-----------|
| M1 (done) | `career_hr` | Committed pack Python |
| M2 (done) | Named attrs | Manifest + generic resolver |
| M3 (queued) | Named attr, manifest miss | LLM codegen + sandbox |
| M4b (done) | Free-form label + intent slug | Derive on miss; synonym dedup via `intent_map.json` |
| M5 (unlikely) | NL `question` on wire protocol | **Not shipping** — host agent maps NL → `requested_attributes`; see [`unlikely/README.md`](../../plans/unlikely/README.md) |

Constant: computation-centric provenance envelope across phases.

---

## What we deliberately did not do

| Alternative | Why we rejected it |
|-------------|-------------------|
| 500-entry `attribute_map` | Classification and maintenance collapse |
| Per-query LLM schema inference | Token and latency disaster at Lahman scale |
| Tavily for `career_hr` | Violates source-first network policy |
| Framework-owned baseball SQL | Pack rules belong in `examples/networks/baseball/` |

---

## Related

- Product motivation: [data-factory-origin.md](data-factory-origin.md)
- Provenance envelope: [computation-centric-provenance.md](computation-centric-provenance.md)
- Multi-record routing: [multi-record-type-routing.md](multi-record-type-routing.md)