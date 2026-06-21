# Baseball bio specialist — warehouse + Tavily research (design conversation)

**Date:** 2026-06-21  
**Status:** **Design locked** (Paul sign-off, interactive review 2026-06-21)  
**Builds on:** M1c bio warehouse reads, M14 `WarehousePlayerStatSpecialist`, CRM `run_field_research` + Tavily

**Cursor slice:** `prompts/cursor/next/2026-06-21-2410-baseball-bio-research-specialist.md` — **READY** (may run **parallel** with `2400` per Paul Q7).

---

## Problem

`BioSpecialist` today is **warehouse-only** (`People` column / compose via manifest). That answers canonical Lahman bio attrs (`birth_date`, `height`, `bats`, …).

**Follow-up bio questions** are outside Lahman `People` or require joins to other tables:

- Nicknames, narrative color, `race` (later — [`peer-aware orchestration`](2026-06-21-peer-aware-specialists-analytic-orchestration.md))
- Hall of Fame election year — **in Lahman `HallOfFame`** (manifest path, not Tavily)
- Contemporary web-sourced facts with no sqlite row

**Derive-on-miss is the wrong tool** — bio misses are **research** (Tavily + LLM), like CRM `email`.

---

## Locked decisions (Paul, 2026-06-21)

| # | Topic | Lock |
|---|--------|------|
| — | Derivative audit | Aligned — obvious derivatives are **manifest**; LLM derive is intentional miss-path only |
| — | Training wheels | **Off** — M4 whitelist removal stands; remaining items are guardrails |
| Q1 | Framework shape | **A** — `WarehouseResearchPlayerSpecialist` in **`src/`** (extends `WarehousePlayerStatSpecialist`). Paul: standard need → **framework base class**, not pack-only override |
| Q2 | Research trigger | **A** — `research_on_miss: true` on bio domain |
| Q3 | Research gate guinea pig | **`primary_nickname`** (Aaron) — proves Tavily path. **Not** `hall_of_fame_year` for research gate (see Q8). **Follow-on:** nickname normalization + synonym gate tests (Grok committed) |
| Q4 | Ontology | **A** — hand-add gate attrs to `categories.json` / `attribute_map`. **Review later:** alignment with self-creating / lazy ontology growth (CRM pattern) — do not block v1 |
| Q5 | Mixed provenance | **A** — warehouse + research attrs in one deliver |
| Q6 | Latency | **A** — sync Tavily (CRM default); cost via metering |
| Q7 | Slice ordering | **C** — **parallel** Cursor agents (`2410` bio + `2400` derive) |
| Q8 | Warehouse vs research boundary | **Lahman wins** — if sqlite has the fact, **manifest/warehouse** answers it; research only for gaps. `hall_of_fame_year` → **manifest alias** from `HallOfFame.yearid` where `inducted='Y'` → **1982** (election) for Aaron |

### `hall_of_fame_year` (Paul principle)

Lahman `HallOfFame` has `yearid=1982` for Aaron — **report the database value**, not a ceremony year from the web. Implement as **warehouse manifest alias** in `2410` (or immediate follow-on in same slice). Live gate **warehouse regression** for HOF; **research gate** uses `primary_nickname` instead.

---

## Hybrid bio tier (implementation)

```text
BioSpecialist(WarehouseResearchPlayerSpecialist)
├── Warehouse path — manifest aliases (People + HallOfFame join for HOF year)
└── Research path on miss — run_field_research + Tavily when label ∉ aliases
```

**Not in v1:** `derive_on_miss` on bio; team bio research.

---

## Provenance (locked)

| Path | `sources[]` | `computation` |
|------|-------------|---------------|
| Warehouse hit | Pack dataset (`lahman`) | Python inline / compose / join |
| Research hit | Tavily URLs | LLM research metadata (CRM pattern) |

---

## Follow-on (not blocking `2410`)

- `race` on bio + research (`peer-aware orchestration` doc)
- Ontology generator vs hand-add — **review for self-creating network goal**
- `bb-bio-research-02` synonym / nickname normalization gate
- Metering for bio research volume

---

## Related

- [`2026-06-21-baseball-morning-decision-brief.md`](2026-06-21-baseball-morning-decision-brief.md) — Part H signoff summary
- [`2026-06-21-peer-aware-specialists-analytic-orchestration.md`](2026-06-21-peer-aware-specialists-analytic-orchestration.md)