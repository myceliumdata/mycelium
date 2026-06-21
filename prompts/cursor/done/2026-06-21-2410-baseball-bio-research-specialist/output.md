# Baseball bio warehouse + Tavily research — output

## Summary

Added framework **`WarehouseResearchStatSpecialist`** (extends `WarehousePlayerStatSpecialist`): warehouse manifest reads first, then sync Tavily research for unaliased bio labels when `research_on_miss: true`. **`BioSpecialist`** is now a thin subclass. **`hall_of_fame_year`** resolves from Lahman `HallOfFame` (Aaron **1982**) — no Tavily.

## Hierarchy

```text
WarehousePlayerStatSpecialist
└── WarehouseResearchStatSpecialist
    └── BioSpecialist (pack)
```

## Manifest / ontology

| Item | Detail |
|------|--------|
| `research_on_miss: true` | bio domain only |
| `hall_of_fame_year` | `hof_election_year` convention → `HallOfFame.yearid` where `inducted='Y'` |
| Ontology | `primary_nickname`, `hall_of_fame_year` → bio |

## Anchors

| Attribute | Anchor | Path |
|-----------|--------|------|
| `hall_of_fame_year` | **1982** | Warehouse (`SELECT yearid FROM HallOfFame WHERE playerID='aaronha01' AND inducted='Y'`) |
| `primary_nickname` | **Hammer** | Research gate (Tavily); common Hank Aaron nickname for live anchor |

## Live gate

| ID | Phase | Notes |
|----|-------|-------|
| `bb-bio-03` | `m2` | `hall_of_fame_year` equals 1982 |
| `bb-bio-research-01` | `bio_research` | `primary_nickname`; requires `OPENAI_API_KEY` + `TAVILY_API_KEY` |

Total baseball catalog: **34** scenarios (shared count with `2400`).

## Key changes

| Area | Change |
|------|--------|
| Framework | `WarehouseResearchStatSpecialist` in `warehouse_stat.py`; versioned `mark_pending` via research_handlers |
| Pack | `BioSpecialist` base class swap; `hof_election_year` in `warehouse_resolve.py` |
| Fixture | `HallOfFame.csv` in minimal Lahman fixture |
| Tests | `test_hall_of_fame_year_warehouse_manifest`, `test_primary_nickname_research_mocked` |

## Verification

```text
./bin/ci-local    # 655 passed
```

## For Grok + Paul

- Mark **2410** shipped.
- Run `./bin/gate-live baseball` with Tavily keys for `bb-bio-research-01`.
- **Deferred:** `bb-bio-research-02` nickname synonym/normalization (Grok follow-on).
- **Follow-on:** ontology hand-add vs lazy self-creating network review.

Suggested commit message:

```
feat(baseball): bio warehouse + Tavily research on miss (framework tier)
```
