# Baseball pitching career_era (M8) — output

## Summary

Shipped **`career_era`** via manifest convention `career_era_weighted`: `9 * SUM(ER) / (SUM(IPouts)/3)` across all Pitching rows, formatted to 3 decimals. `pitching_specialist` picks it up through existing `resolve_domain_attribute`. Live gate **`bb-pitch-03`** asserts Nolan Ryan career ERA ≈ **3.194** (tolerance 0.001). Manual gate docs synced for M5–M6 pitching/team live scenarios.

## Files

| Area | Files |
|------|--------|
| Manifest | `examples/networks/baseball/warehouse_domains.json` — `career_era_weighted` convention + alias |
| Resolver | `examples/networks/baseball/specialists/warehouse_resolve.py` — `career_era_weighted()` |
| Fixture | `tests/baseball_minimal_fixture.py` — Pitching ER/IPouts → fixture ERA **3.000** |
| Tests | `tests/test_baseball_pitching_specialist.py` — career_era smoke + provenance |
| Live gate | `bb-pitch-03`, anchor `pitcher_career_era: 3.194`, drift check with float tolerance |
| Docs | `docs/manual-checks/2026-06-19-baseball-specialist-hand-test.md`, `2026-06-20-live-gate-program.md` |

## Verification

```text
./bin/ci-local                              # 628 smoke passed
uv run pytest tests/test_baseball_pitching_specialist.py -m smoke -q  # 4 passed
```

Baseball catalog: **21** scenarios; phases include `pitching` and `team_season`.

## Deferred

- Season-scoped `era` and `derive_on_miss` for unsupported rate labels — M9 / later.

## For Grok + Paul

- Mark M8 career_era shipped in program slice map.
- Live gate total scenarios: 21 (was 19 before M7 `bb-bio-01` + M8 `bb-pitch-03`).
- Next slice: `2026-06-20-2220-baseball-query-scope-yearid-m9.md`.

## Suggested commit message

```
baseball: career_era weighted pitching rate (M8)
```
