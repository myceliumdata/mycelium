# Baseball warehouse stat specialist base class (M14) — output

## Summary

Promoted warehouse player/team stat graph orchestration and derive-on-miss into framework base classes. Baseball pack specialists are thin subclasses declaring `category`, `domain`, and Lahman resolver hooks via `baseball_warehouse_hooks.py`.

## Hierarchy

```text
SpecialistAgent
├── WarehousePlayerStatSpecialist     # src/agents/specialists/warehouse_stat.py
│   ├── BattingSpecialist             # category=batting, domain=batting
│   ├── PitchingSpecialist
│   ├── BioSpecialist
│   └── FieldingSpecialist
└── WarehouseTeamStatSpecialist
    └── TeamSeasonSpecialist          # category=team_season, domain=team_season

Pack hooks (examples/.../baseball_warehouse_hooks.py):
  BaseballWarehousePlayerHooks → _load_warehouse_resolve(), _load_derive_resolve()
  BaseballWarehouseTeamHooks   → _load_warehouse_resolve()
```

See also: [`docs/architecture/whys/specialist-class-hierarchy.md`](../../../docs/architecture/whys/specialist-class-hierarchy.md).

## Line counts

| File | Before | After |
|------|--------|-------|
| `batting_specialist.py` | ~195 | **36** |
| `pitching_specialist.py` | ~44 | **36** |
| `bio_specialist.py` | ~44 | **36** |
| `fielding_specialist.py` | ~44 | **36** |
| `team_season_specialist.py` | ~44 | **36** |
| **New** `warehouse_stat.py` (framework) | — | **649** |
| **New** `baseball_warehouse_hooks.py` | — | **28** |

## Manifest derive flags

| Domain | `derive_on_miss` | Notes |
|--------|------------------|-------|
| `batting` | `true` | LLM derive on manifest miss (unchanged) |
| `pitching` | absent / false | Warehouse aliases only |
| `bio` | absent / false | People column reads |
| `fielding` | absent / false | career_sum aliases |
| `team_season` | N/A | team specialist has no derive v1 |

Enable derive on any player domain by setting `"derive_on_miss": true` in `warehouse_domains.json` — no Python change required.

## `pack_common` — still in pack vs promoted

| Symbol | Location |
|--------|----------|
| `coerce_state`, `resolve_entity_id`, `resolve_owned_fields`, `identity_from_context`, `overall_field_status`, `query_year_id`, `now_iso` | **Promoted** → re-exported from `warehouse_stat.py` |
| `run_warehouse_player_graph`, `run_warehouse_team_graph` | **Legacy wrappers** delegating to framework agent `.run()` |
| `evaluate_*_warehouse_fields` | **Promoted** → methods on framework base classes |
| `product_common`, `registry_identity_common` | Still import shared helpers via `pack_common` re-exports |

**Follow-on (not M14):** `ProductTeamSpecialist` for roster/franchise; promote `warehouse_resolve.py` / `derive_resolve.py` into `src/` after extraction review.

## Files

| Area | Files |
|------|--------|
| Framework | `src/agents/specialists/warehouse_stat.py`, `__init__.py` exports |
| Pack | Thin specialists, `baseball_warehouse_hooks.py`, slim `pack_common.py` |
| Tests | `tests/test_warehouse_stat_specialist.py` |

## Verification

```text
./bin/ci-local                              # 643 smoke passed
uv run pytest tests/test_warehouse_stat_specialist.py tests/test_baseball_* -m smoke -q
```

Live gate: **N/A** — refactor only; existing scenarios unchanged after `--sync-only`.

## For Grok + Paul

- Mark M14 warehouse stat hierarchy shipped; update program slice map.
- Next queued: polish capstone `2350`.
- Operator: `./bin/refresh-example-network baseball --sync-only` picks up thin specialists on live root.

## Suggested commit message

```
feat(specialists): warehouse stat base classes + baseball thin subclasses (M14)
```
