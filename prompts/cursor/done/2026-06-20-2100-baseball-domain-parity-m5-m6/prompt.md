# Baseball domain parity — pitching + team specialists (M5–M6)

> **Ad-hoc slice** — Implemented by Grok (Paul option 2: keep code, formal review). Not claimed via `next/`. Cursor continues from M7 queue.

## Objective

Clone batting/bio warehouse pattern for remaining **declared** ontology categories that were factory stubs:

| Slice | Module | Pattern |
|-------|--------|---------|
| M5 | `pitching_specialist.py` | `batting_specialist` — `career_sum` on `Pitching` |
| M5b | `team_identity_specialist.py` | `player_identity_specialist` — team registry bind |
| M6 | `team_season_specialist.py` | warehouse `team_latest_column` on `Teams` |

## Manifest (`warehouse_domains.json`)

- Pitching: `career_wins`, `career_losses`, `career_strikeouts`, `career_saves`
- Team season: `season_wins`, `season_losses`, `finish_rank`, `park`, `runs_scored`, `runs_allowed`
- `warehouse_resolve`: table-aware `career_sum`; `resolve_team_domain_attribute`; `team_provenance_parameters`

## Tests

- `tests/baseball_minimal_fixture.py` shared fixture (Pitching + Teams W/L columns)
- `test_baseball_pitching_specialist.py`, `test_baseball_team_season_specialist.py`, `test_baseball_multi_domain_deliver.py`
- Add pytest files to `bin/smoke-baseball-e2e`

## Constraints

- Pack-only baseball logic; CRM unchanged.
- No `career_era` (M8), no query scope (M9), no fielding/franchise/roster (M10–M12).
- Do not edit `TODO.md` (Grok owns).