# M2b output — manifest-driven warehouse resolver

## Done

- **`examples/networks/baseball/specialists/warehouse_resolve.py`** — pack resolver: `career_sum`, `people_column`, `people_birth_date`; reads aliases from live `warehouse_manifest.json`.
- **`warehouse_domains.json`** — batting aliases (`career_hr`, `career_rbi`, `career_hits`) and bio aliases (`birth_date`, `debut`, `bats`, `throws`, `birth_city`).
- **Refactored** `batting_specialist.py` and `bio_specialist.py` — generic manifest loop; no per-attr `if key == "career_hr"` branches.
- **Provenance** — `parameters` now include `lahman.playerID` and `warehouse` (`warehouse/lahman.sqlite`); inline from `inspect.getsource` on convention functions.
- **Tests** — `career_rbi`/`career_hits` on minimal fixture; provenance asserts `warehouse` param.
- **Smoke** — `career_rbi_routes_batting_specialist` scenario (9 scenarios total).

## Fixture expected values (minimal Aaron rows)

| Attribute | Value | Notes |
|-----------|-------|-------|
| `career_hr` | 3 | HR 1 + 2 |
| `career_rbi` | 3 | RBI 1 + 2 |
| `career_hits` | 4 | H 2 + 2 |
| `birth_date` | 1934-02-05 | unchanged |

Unknown attrs / rate stats (`career_avg`, `ops`) → `N/A`.

## Verification

```text
./bin/ci-local                    # 567 smoke passed
uv run pytest tests/test_baseball_batting_specialist.py tests/test_baseball_bio_specialist.py -q
./bin/smoke-baseball-e2e          # 9 scenarios
```

## Next

Queue **M2c** — identity bind fields + remaining provenance gaps.

## Suggested commit message

```
baseball: manifest-driven warehouse resolver for career stats (M2b)
```
