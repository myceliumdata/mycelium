# Baseball bio manifest aliases (M7)

> **READY** — Claim per `prompts/cursor/WORKFLOW.md`. **Do not edit `TODO.md`.**

## Objective

Add remaining **bio** warehouse aliases to `examples/networks/baseball/warehouse_domains.json` and verify via smoke tests. No new specialist file — `bio_specialist` + `warehouse_resolve` already handle `people_column` / compose conventions.

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

## Constraints

- Baseball logic in pack only; framework unchanged except shared `warehouse_resolve` compose helper if death_date needs it.
- CRM unchanged. `./bin/ci-local` must pass.