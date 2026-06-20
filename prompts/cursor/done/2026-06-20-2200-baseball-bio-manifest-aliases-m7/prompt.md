# Baseball bio manifest aliases (M7)

> **READY** — Claim per `prompts/cursor/WORKFLOW.md`. **Do not edit `TODO.md`.**

## Objective

Add remaining **bio** warehouse aliases to `examples/networks/baseball/warehouse_domains.json` and verify via smoke tests. No new specialist file — `bio_specialist` is already a thin `pack_common` wrapper; manifest + `warehouse_resolve` changes only.

## Aliases to add

| Attribute | Convention | Lahman |
|-----------|------------|--------|
| `height` | `people_column` | `height` |
| `weight` | `people_column` | `weight` |
| `birth_country` | `people_column` | `birthCountry` |
| `final_game` | `people_column` | `finalGame` |
| `death_date` | `people_compose` | death Y/M/D → iso_date (extend `warehouse_resolve` if needed) |

## Tests

- Extend `tests/baseball_minimal_fixture.py` People.csv with columns for height/weight/death.
- `tests/test_baseball_bio_specialist.py` — one test per new alias (smoke).

## Live gate (required)

Add **`bb-bio-01`** to `tests/live/catalogs/baseball.yaml` (phase `m2` or new `bio` phase):

- Aaron `height` + `weight` (or `birth_country`) — two-step deliver with template anchors.
- Extend `tests/live/anchors/baseball_aaron_lahman_v2025.json` with values from live Lahman root (`./bin/gate-live baseball --drift-only` or manual step-1/2 on Paul's root).
- Extend `gate_runner.py` baseball drift checks for new anchor attrs if drift-only should catch regressions.

`@pytest.mark.live_gate` only — never default CI.

## Constraints

- Baseball logic in pack only; framework unchanged except shared `warehouse_resolve` compose helper if death_date needs it.
- CRM unchanged. `./bin/ci-local` must pass.