# Warehouse factory — layer 3, stats surface, specialist emergence

**Date:** 2026-06-19  
**Participants:** Paul + Grok  
**Status:** Direction locked; M1 warehouse specialists shipped; layer 3 not implemented  
**Related:** [`2026-06-18-computation-centric-provenance.md`](2026-06-18-computation-centric-provenance.md), [`2026-06-14-data-factory-origin.md`](2026-06-14-data-factory-origin.md), [`baseball-example-program.md`](../baseball-example-program.md), [`2026-06-19-baseball-specialist-hand-test.md`](../../manual-checks/2026-06-19-baseball-specialist-hand-test.md)

---

## Context (what shipped before this conversation)

- **M1a** — committed baseball `categories.json` + pack ontology install  
- **M1b** — `career_hr` via `batting_specialist` + computation-centric provenance  
- **M1c** — `birth_date` via `bio_specialist` (raw `People`, `YYYY-MM-DD`)  
- **Polish** — `inspect.getsource` for inline provenance; `write_na_field`; status helper  
- **Paul hand-test** — full Lahman root: warehouse path validated after clearing research cache; `career_hr=755`, `birth_date=1934-02-05` with dataset + `computation.inline` provenance  

---

## Locked: three-layer stack (Paul’s diagram)

```text
Client / MCP          →  discovery (describe_network schema catalog)
Routing               →  coarse ontology (batting, bio, …) — not 500 attr names
Execution             →  specialists inspect manifest + warehouse, compute, cache
```

**Do not** flatten every Lahman column into `categories.json` `attribute_map`. Expose **schema + conventions**; materialize answers on demand.

---

## How auditors know inputs (provenance)

Every `found` version must list **all** runtime parameter **values** in `parameters`, even when `computation` is a URI:

- Entity bridge: `lahman.playerID`  
- Infrastructure: `warehouse` path (e.g. `warehouse/lahman.sqlite`)  
- Scope when relevant: `yearID`, `teamID`, …  

`computation` = which program; `parameters` = which inputs; `sources[]` = which dataset snapshot.

**M1 gap:** `warehouse` not yet in `parameters` — follow-up slice.

---

## Storage policy (Paul, June 2026)

| Now | Future |
|-----|--------|
| **Always cache** computed `found` on deliver | Specialists manage own storage economically |

Retention agent (deferred) uses:

- **Compute cost** — expensive → more likely to cache  
- **Access patterns** — frequent access → keep even if cheap to recompute  
- **Storage cost** — needs metering signals  

Humans should not tune per-field retention.

---

## Ground truth vs research (baseball)

Two specialist models exist today — **not** a single “ground truth then web” waterfall:

| Type | Path |
|------|------|
| Pack warehouse (`batting`, `bio`) | Lahman sqlite only; unimplemented → `N/A` |
| Factory research template | Web only; no warehouse step |

**Target for source-first networks (baseball):**

1. Warehouse / registry when attr has declared tables  
2. `N/A` or explicit policy when missing  
3. Web **only** for supplemental bio (policy-gated), never for batting stats  

**Hand-test lesson:** Research cache on baseball root masked warehouse path until `agents/batting` + `agents/bio` storage cleared + `--sync-only` + MCP restart.

**Bind fields** (`debut_team`, `debut_year`): registry ground truth — must not route to web research when requested as attrs (yellow flag in provenance run).

---

## Edge cases (summary)

| Case | Mitigation |
|------|------------|
| Bind vs warehouse | Identity reads registry; stats read warehouse |
| Grain (career vs season) | `parameters.scope` + manifest defaults |
| Rate / derived stats | Manifest **recipes**, not column introspection alone |
| Multi-column (OPS) | Recipe in one domain specialist |
| Parallel tables (Batting vs Pitching) | Table → specialist + record type |
| Team-season vs player career | `team_season_specialist` + record type routing |
| Franchise vs two team rows | `franchise_specialist` (deferred product) |
| Stints | Pool-then-divide for rates |
| Multi-specialist deliver | Graph merge — per-attr provenance |
| Cross-domain **product** | New specialist only when single computation + unified cache + repeat demand |

Full detail: Grok session 2026-06-19 (this doc + Paul hand-test transcripts).

---

## Path to LLM-generated programs (five phases)

| Phase | Client | Execution |
|-------|--------|-----------|
| **M1 (done)** | `requested_attributes: ["career_hr"]` | Committed pack Python |
| **M2** | Named attrs | Manifest conventions + generic resolver (still committed logic) |
| **M3** | Named attrs, cache miss | LLM codegen + sandbox |
| **M4** | `derive` / free-form label | LLM program; cache key from intent hash |
| **M5** | Natural language `question` | Classify intent → codegen; ontology routes domains not stat names |

Constant: `sources[]` + `computation` + `parameters` provenance envelope.

---

## Specialist emergence — two kinds

### A — Lazy category (in framework today)

Unknown attr → `classify()` LLM → new category → `factory.create_specialist` → **research stub**.

Appropriate for **CRM research networks**. **Not** for baseball warehouse stats — pack install must win.

### B — Product specialist (deferred automation)

Cross-domain capabilities (`franchise_specialist`, `team_roster`, advanced metrics) when:

- Single coherent computation / artifact  
- Cross-domain ground truth  
- Repeat demand + unified cache  
- Clear provenance unit  

**Promotion policy (future):** derive telemetry + compute/storage costs → agent **recommends** promotion; Paul/Grok approve slice until automated.

**Now:** manual program slices only; suppress research stub for warehouse categories on baseball.

---

## Program slices (recommended order)

| Slice | Objective |
|-------|-----------|
| **M2a** | Warehouse capability manifest + `describe_network` surfacing |
| **M2b** | Generic batting/bio resolver (conventions: `career_sum`, raw People columns) |
| **M2c** | Full `parameters` in provenance; identity bind read (no research for `debut_*`) |
| **M3** | Derive API + LLM codegen sandbox (one attr guinea pig) |
| **Later** | `franchise_specialist`, derive telemetry → promotion agent |

Cursor prompt: `prompts/cursor/next/2026-06-19-1400-baseball-warehouse-manifest-m2a.md`

---

## Open (non-blocking)

- Dataset manifest vs warehouse manifest merge  
- Ontology LLM generator from schema  
- Research path migration to computation-centric envelope  
- `docs/manual-checks/2026-06-19-baseball-specialist-hand-test.md` — operator gate  

---

*Archived June 2026.*