# Baseball bio specialist — warehouse + Tavily research (design conversation)

**Date:** 2026-06-21  
**Status:** Direction sketched — **open questions for Paul** before Cursor claims slice
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

**Morning prep:** [`2026-06-21-baseball-morning-decision-brief.md`](2026-06-21-baseball-morning-decision-brief.md) — inventory, training-wheels checklist, Q1–Q8 with examples and answer sheet.

## Open questions (Paul + Grok — resolve before implement)

1. **Framework shape** — `WarehouseResearchPlayerSpecialist` (warehouse then research in one `run()`) vs separate `bio_research` category vs CRM-style generated research specialist only for bio misses?
2. **Research trigger** — Any unaliased bio label (`research_on_miss: true`) vs explicit allowlist in manifest/ontology vs “research only when client sends `research: true`” flag?
3. **Guinea-pig gate attrs** — `hall_of_fame_year` (verifiable, boring) vs `primary_nickname` (fuzzy normalization) vs both? Who picks anchors after Tavily discovery?
4. **Ontology** — New attrs need `categories.json` / routing entries before step-1 can request them — ship ontology generator pass or hand-add?
5. **Provenance on mixed deliver** — Step-2 with `birth_date` (warehouse) + `hall_of_fame_year` (Tavily) in one query: OK to mix computation-centric + URL sources in one `results[]` row?
6. **Latency / cost** — Always sync Tavily on miss (CRM default) or async/pending for bio follow-ups?
7. **Ordering vs derive slice** — Bio research before `2400` multi-domain derive, or derive expansion first?
8. **Boundary** — Facts that *could* be Lahman manifest aliases later (e.g. `hall_of_fame_year` from `Hall of Fame` table) — research-only by policy, or ingest path preferred?

## Cursor slice (draft — do not claim until above resolved)

`prompts/cursor/next/2026-06-21-2410-baseball-bio-research-specialist.md`