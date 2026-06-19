# M2c output — registry bind attrs + warehouse parameters

## Done

**Approach:** Option **A** — pack `player_identity_specialist.py` reads bind values from graph context / entity registry and writes `found` versions with `actor.kind: registry` (no Tavily). Replaces factory stub that ran web research for `debut_team` / `debut_year`.

- **`examples/networks/baseball/specialists/player_identity_specialist.py`** — registry bind delivery; rewrites cached `research` versions on deliver.
- **Warehouse `parameters.warehouse`** — already complete from M2b (`warehouse/lahman.sqlite` on batting/bio writes).
- **`tests/test_baseball_player_identity_specialist.py`** — deliver + provenance (registry or seed_bootstrap, not research).
- **`bin/smoke-baseball-e2e`** — `bind_attrs_registry_provenance` scenario (10 scenarios).

## Provenance behavior

| Field | Source | Actor kinds |
|-------|--------|-------------|
| `debut_team`, `debut_year` | Registry `bind_values` | `seed_bootstrap` (bootstrap write) or `registry` (specialist deliver) |
| `career_hr`, `birth_date`, … | Warehouse | `specialist` + dataset/computation + `parameters.warehouse` |

No `research` actor or external URLs on bind attrs.

## Verification

```text
./bin/ci-local                    # 569 smoke passed
uv run pytest tests/test_baseball_batting_specialist.py tests/test_baseball_bio_specialist.py tests/test_baseball_player_identity_specialist.py -q
./bin/smoke-baseball-e2e          # 10 scenarios
```

## For Grok + Paul

M2c done — re-run multi-attr hand-test with `provenance: true` (`debut_team`, `debut_year`, `career_hr`, `birth_date`).

## Suggested commit message

```
baseball: registry bind attrs on deliver + full warehouse parameters (M2c)
```
