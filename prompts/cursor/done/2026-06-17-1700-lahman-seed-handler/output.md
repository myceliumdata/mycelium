# LahmanSeedHandler — baseball pack bootstrap (v1 identity + warehouse)

## Summary

Shipped **`LahmanSeedHandler`** under `examples/networks/baseball/bootstrap_handlers/`. Bootstrap ingests Lahman CSV seed into `warehouse/lahman.sqlite`, commits **team** grain (distinct `Teams.name`), and **player** grain with **one uuid per Lahman `playerID`** and **multiple `bind_index` keys** for multi-team aliases (L7).

## Key changes

| Area | Change |
|------|--------|
| `bootstrap_handlers/lahman_common.py` | Seed resolution, warehouse ingest, `distinct_team_labels`, `distinct_player_team_rows` |
| `bootstrap_handlers/lahman_seed.py` | `LahmanSeedHandler` — team commits + playerID dedup + `add_bind_alias` for extra teams |
| `entity_registry.py` | `add_bind_alias()` for bootstrap multi-team bind keys |
| `category_mvr_bootstrap.py` | All manifest MVR bind fields merged; `team` → `professional` |
| `attribute_write.py` | `write_bind_fields` uses `reg._mvr` |
| `examples/networks/baseball/network.json` | Bootstrap → `bootstrap_handlers.lahman_seed` |
| `tests/test_lahman_seed_handler.py` | No seed, minimal fixture, multi-team same `playerID` |

## Locked behavior (verified)

- No seed → `handler_id="lahman_seed"`, 0 entities
- Seed → warehouse + `entities/team.json` + `entities/player.json`
- Same `playerID` on two teams → 1 entity, 2 `bind_index` keys, both lookups return same `id`
- CRM capstones unchanged

## Verification

```bash
./bin/ci-local
# CI local: all steps passed.
# 436 passed, 93 deselected
```

## For Grok + Paul

- Improvised stash `cursor-improvised lahman seed handler (option A — compare later)` — compare if needed.
- **Next slice after approval:** query orchestrator grain selection (`target_resolve`, supervisor).
- Suggested commit:

```
feat(baseball): LahmanSeedHandler pack bootstrap

Ingest Lahman CSV seed into warehouse/lahman.sqlite; commit team and
player entity grains with playerID dedup and multi-team bind aliases.
Extend category MVR merge and write_bind_fields grain policy.
```

- Do **not** commit from this slice deliverable.
