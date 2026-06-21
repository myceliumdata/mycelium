# Review — baseball bio warehouse + Tavily research (2410)

**Verdict:** **Approved + polish nits**  
**Reviewer:** Grok  
**Date:** 2026-06-21

## Context

Design-locked slice: framework **`WarehouseResearchStatSpecialist`**, bio `research_on_miss`, `hall_of_fame_year` warehouse alias (Lahman wins), `primary_nickname` research gate. Implemented in parallel with `2400` — shared gate/catalog files reviewed in both reviews.

## CI

| Check | Result |
|-------|--------|
| `./bin/ci-local` | **655** smoke passed, ruff clean, admin-ui build ok |

## Delivery

`output.md` matches files on disk. Framework class, pack hooks, fixture `HallOfFame.csv`, gate scenarios, and smoke tests all present.

## Diff reviewed

| File | Read |
|------|------|
| `src/agents/specialists/warehouse_stat.py` | Full — `defer_miss_to_research`, `WarehouseResearchStatSpecialist` |
| `src/agents/specialists/__init__.py` | Full |
| `examples/networks/baseball/specialists/bio_specialist.py` | Full |
| `examples/networks/baseball/specialists/warehouse_resolve.py` | Full — `hof_election_year` |
| `examples/networks/baseball/warehouse_domains.json` | Full — bio `research_on_miss`, HOF alias |
| `examples/networks/baseball/categories.json` | Full |
| `examples/networks/baseball/README.md` | Full |
| `docs/architecture/whys/specialist-class-hierarchy.md` | Full |
| `tests/baseball_minimal_fixture.py` | Full |
| `tests/test_baseball_bio_specialist.py` | Full |
| `tests/test_warehouse_stat_specialist.py` | Full — research defer unit test |
| `tests/live/catalogs/baseball.yaml` | Bio scenarios (`bb-bio-03`, `bb-bio-research-01`) |
| `tests/live/anchors/baseball_aaron_lahman_v2025.json` | Full |
| `tests/live/gate_runner.py` | HOF + fielding drift rows |
| `tests/live/networks.yaml` | `bio_research` phase |
| `tests/test_live_gate_runner_unit.py` | Minimum count 34 |

## Spec compliance

| Criterion | Result |
|-----------|--------|
| `WarehouseResearchStatSpecialist` in `src/` (not pack-only) | Pass |
| No `derive_on_miss` on bio | Pass |
| `research_on_miss: true` on bio domain | Pass |
| `hall_of_fame_year` → `hof_election_year` / Aaron **1982** | Pass |
| `BioSpecialist` thin subclass only | Pass |
| Ontology: `primary_nickname`, `hall_of_fame_year` → bio | Pass |
| `bb-bio-03` warehouse gate | Pass |
| `bb-bio-research-01` Tavily gate + env skip | Pass |
| `bio_research` phase in `networks.yaml` | Pass |
| Framework unit: research only on unaliased miss | Pass |
| Pack smoke: HOF manifest + mocked nickname research | Pass |
| `birth_date` / existing bio paths unchanged | Pass (fixture + existing tests green) |
| Hierarchy doc updated | Pass |
| `TODO.md` untouched | Pass |
| `./bin/ci-local` green | Pass |

## Legacy / dual-path

- Warehouse manifest aliases (People, compose dates) unchanged — fast path preserved.
- `hall_of_fame_year` never hits Tavily once aliased — matches Paul Q8 lock.
- CRM `run_field_research` shared; no CRM edits in diff.

## Tests

**Strong:** `test_hall_of_fame_year_warehouse_manifest`, `test_primary_nickname_research_mocked`, `test_research_on_miss_defers_unaliased_fields`, minimal fixture HallOfFame seed.

**Gaps (non-blocking):** No `discover_anchor_drift` row for `primary_nickname` (research-sourced; acceptable v1). No live-gate unit test for `bb-bio-03` beyond catalog minimum.

## Design critique

**Strong:** Correct hierarchy placement — `defer_miss_to_research` hook on `WarehousePlayerStatSpecialist` keeps the research tier opt-in without forking the warehouse loop. `hof_election_year` convention is narrow and testable. Peer context in `_research_context` aligns with peer-aware orchestration doc (forward-compatible).

**Sub-optimal (non-blocking):** `WarehouseResearchStatSpecialist.run()` duplicates the parent `run()` (~150 lines) instead of extending post-`_evaluate_player_warehouse_fields` — works, but a follow-on refactor to `super().run()` + research pass would reduce drift risk.

## Polish nits (non-blocking)

| Item | Note |
|------|------|
| `docs/manual-checks/2026-06-20-live-gate-program.md` phases table | Still lists phases without `bio_research` (count updated to 34) |
| `WarehouseResearchStatSpecialist.run()` duplication | Refactor to shared post-warehouse hook when a second research consumer appears |
| `bb-bio-research-02` | Deferred nickname synonym gate — queue when ready |

## For Paul

- **Commit:** Combined with `2400` in one working tree (see `2400` review) — message includes bio bullet.
- **Manual gate:** `./bin/gate-live baseball` with `OPENAI_API_KEY` + `TAVILY_API_KEY` for `bb-bio-research-01`; target **34/34**.
- **Push:** Local only until you request program push.