# Output — baseball batting specialist + computation provenance (M1b)

## Summary

End-to-end warehouse-backed `career_hr` deliver for bootstrap fixture player Hank Aaron (`aaronha01`): step 2 returns `found` with value `"3"`, computation-centric provenance (`sources`, `computation.inline`, `parameters`), and specialist storage cache on re-deliver.

## Changes

| Area | Change |
|------|--------|
| `src/agents/specialists/computed.py` | `build_computed_version_body`, `append_computed_version` |
| `src/agents/specialists/agent.py` | `write_computed_field()` for computed provenance shape |
| `src/network/dataset_source.py` | `load_pack_dataset_source()` from `seed.source.json` |
| `src/network/warehouse.py` | `default_warehouse_path`, `query_warehouse` (read-only sqlite) |
| `src/agents/registry_bridge.py` | `entity_source_key()` |
| `examples/networks/baseball/specialists/batting_specialist.py` | Warehouse `SUM(HR)` compute + cache; no research |
| `examples/networks/baseball/seed.source.json` | `"dataset_id": "lahman"` |
| `src/network/pack_ontology.py` | Copy pack `specialists/*.py` over factory stubs on install |
| `examples/networks/baseball/bootstrap_handlers/lahman_common.py` | Export `LAHMAN_PLAYER_ID`, `LAHMAN_TEAM_ID` |
| Fixtures | `Batting.csv` in minimal Lahman fixtures (HR 1+2=3) |
| `tests/test_baseball_batting_specialist.py` | Compute, provenance, cache, missing warehouse |
| `bin/smoke-baseball-e2e` | Assert `career_hr==3` + provenance keys |
| `examples/networks/baseball/README.md` + `queries/03-career-hr.json` | Step-2 example |

## Verification

| Check | Result |
|-------|--------|
| `./bin/ci-local` | **560** smoke passed |
| `./bin/smoke-baseball-e2e` | **7** scenarios passed |

## For Grok + Paul

- Mark **M1b** done in `TODO.md` when approved.
- Live roots: `./bin/refresh-example-network baseball --sync-only` picks up pack `batting_specialist.py`.
- **Next:** `bio_specialist` warehouse `birth_date` or web supplemental with full `computation` on research path.
- No commit (per workflow).

**Suggested commit message:**

```
baseball: batting specialist career_hr + computation provenance (M1b)
```
