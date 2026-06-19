# Review — baseball batting specialist + computation provenance (M1b)

**Verdict:** **Approved**  
**Reviewer:** Grok  
**Date:** 2026-06-19

## Scope checked

Full read of M1b deliverables against prompt and [`2026-06-18-computation-centric-provenance.md`](../../docs/plans/conversations/2026-06-18-computation-centric-provenance.md):

| Area | Assessment |
|------|------------|
| `computed.py` + `write_computed_field` | Correct version body (`sources`, `computation`, `parameters`); pass-through provenance unchanged |
| `dataset_source.py` | Generic git pin from `seed.source.json`; `dataset_id: lahman` in pack |
| `warehouse.py` | Read-only URI sqlite; generic `query_warehouse` |
| `registry_bridge.py` | Generic `entity_source_key` |
| `pack_ontology.py` | `_install_pack_specialists` copies pack modules after stub render |
| `batting_specialist.py` | Pack-only Lahman SQL; cache via `write_computed_field`; no research |
| Fixtures + tests | `career_hr==3`, provenance shape, cache, missing warehouse graceful |
| Smoke | Routes + value + provenance keys |

## CI

| Check | Result |
|-------|--------|
| `./bin/ci-local` | **560** smoke passed, ruff clean, admin-ui build ok |
| `./bin/smoke-baseball-e2e` (clean env) | **7** scenarios passed |

## Architecture fit

- Supervisor/classification unchanged; warehouse logic stays in pack specialist.
- M1a ontology routing + M1b deliver compose correctly.
- Framework default `warehouse/lahman.sqlite` in `default_warehouse_path` is a mild baseball-shaped default but overridable via `relative=` — acceptable for v1.

## Polish nits (non-blocking)

| # | Nit | Note |
|---|-----|------|
| P1 | `CAREER_HR_COMPUTATION_INLINE` differs slightly from `_compute_career_hr` SQL (quotes, `CAST`) | Provenance records canonical recipe; actual execute path uses `query_warehouse`. Align in M1c or a polish slice if strict byte-for-byte matters. |
| P2 | `_mark_na` uses full `storage.load()` / `save()` | Fine at low volume; align with incremental path if batting storage crosses minisql threshold. |
| P3 | Dead branch in overall-status logic (`na_attrs and not found_attrs` inside `found_attrs` block) | Harmless; simplify when touching file next. |

## Commit plan

Commit **M1b files only** (exclude unrelated fuzzy/docs working-tree edits).

**Suggested message:** `baseball: batting specialist career_hr + computation provenance (M1b)`