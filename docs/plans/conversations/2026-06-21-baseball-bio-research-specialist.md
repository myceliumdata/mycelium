# Baseball bio specialist — warehouse + Tavily research (design conversation)

**Date:** 2026-06-21  
**Status:** Direction locked for slice; implementation via Cursor  
**Builds on:** M1c bio warehouse reads, M14 `WarehousePlayerStatSpecialist`, CRM `run_field_research` + Tavily

---

## Problem

`BioSpecialist` today is **warehouse-only** (`People` column / compose via manifest). That answers canonical Lahman bio attrs (`birth_date`, `height`, `bats`, …).

**Follow-up bio questions** are outside Lahman:

- Hall of Fame induction year / narrative
- Nicknames, awards context, obituary color
- “Where did he go to college?” (not in People)
- Contemporary web-sourced facts

**Derive-on-miss is the wrong tool** — it generates Python against sqlite. Bio misses are **research** problems (Tavily + LLM), like CRM `email`.

---

## Direction (Paul, June 2026)

**Hybrid bio tier:**

```text
BioSpecialist
├── Warehouse path (existing) — manifest aliases, fast, computation-centric provenance
└── Research path on miss — run_field_research + Tavily when label ∉ warehouse manifest
```

**Not in v1:**

- `derive_on_miss` on bio domain (LLM codegen against People)
- Team bio / franchise narrative (separate product tier later)

---

## Framework placement

| Option | Verdict |
|--------|---------|
| A — `BioSpecialist` overrides `run()` with warehouse-then-research | Pack-only; duplicates CRM pattern |
| B — `WarehouseResearchPlayerSpecialist` in `src/` | **Preferred** — warehouse first, research fallback hook |
| C — Split `bio` / `bio_research` categories | Heavier ontology; defer unless routing fights |

Align with [`specialist-class-hierarchy.md`](../../architecture/whys/specialist-class-hierarchy.md): promote pattern to framework; baseball pack stays thin.

---

## Provenance split (locked)

| Path | `sources[]` | `computation` |
|------|-------------|---------------|
| Warehouse hit | Pack dataset source | Python inline / compose |
| Research hit | Tavily URLs | LLM research metadata (CRM pattern) |

Do not mix Tavily URLs into warehouse computation-centric fields.

---

## Gate / smoke strategy

- **Smoke:** mocked Tavily (CRM pattern); warehouse attrs unchanged
- **Live gate:** new phase `bio_research` or extend `m2` with `skip_if_missing_env: TAVILY_API_KEY`
- **Guinea pigs:** Aaron — `hall_of_fame_year` (1999) or `primary_nickname` (“Hammer” / “Bad Henry” — pick one verifiable anchor from discovery)

---

## Cursor slice

`prompts/cursor/next/2026-06-21-2410-baseball-bio-research-specialist.md`