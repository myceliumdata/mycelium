# Baseball bio manifest aliases (M7) — output

## Summary

Added five bio warehouse aliases (`height`, `weight`, `birth_country`, `final_game`, `death_date`) to the baseball pack manifest. Extended `warehouse_resolve.people_compose_iso_date` for generic Y/M/D compose (death_date reuses birth_date delegation). Live gate scenario **`bb-bio-01`** and anchor drift checks cover height, weight, birth_country, final_game, death_date.

## Files

| Area | Files |
|------|--------|
| Manifest | `examples/networks/baseball/warehouse_domains.json` — bio aliases |
| Resolver | `examples/networks/baseball/specialists/warehouse_resolve.py` — `people_compose_iso_date`, `people_birth_date` delegate |
| Fixture | `tests/baseball_minimal_fixture.py` — People.csv columns for new attrs |
| Tests | `tests/test_baseball_bio_specialist.py` — 5 smoke tests (one per alias) |
| Live gate | `tests/live/catalogs/baseball.yaml` (`bb-bio-01`), anchors JSON, `gate_runner.py` drift |

## Verification

```text
./bin/ci-local                              # 628 smoke passed
uv run pytest tests/test_baseball_bio_specialist.py -m smoke -q  # 9 passed
uv run pytest tests/test_live_gate_runner_unit.py -q             # 16 passed
```

Live anchors (Paul root): Aaron height **72**, weight **180**, birth_country **USA**, final_game **1976-10-03**, death_date **2021-01-22**.

## For Grok + Paul

- Mark M7 bio aliases shipped in program slice map when reviewing batch.
- Next queued slice: `2026-06-20-2220-baseball-query-scope-yearid-m9.md`.
- Operator: `./bin/refresh-example-network baseball --sync-only` on live root before `./bin/gate-live baseball --phase m2`.

## Suggested commit message

```
baseball: bio manifest aliases (M7)
```
