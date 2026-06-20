# Baseball bootstrap perf — deferred index rebuild + player_debut (M14) — output

## Summary

Two profile-driven bootstrap optimizations:

1. **Deferred field-index rebuild** — during `bootstrap_deferred_save()`, `_save()` no longer calls `_rebuild_field_indexes()` on every write; one rebuild at `commit_deferred_save()` (eliminates O(n²) scans on ~24k new player binds).
2. **`player_debut` materialization** — warehouse ingest builds indexed `player_debut` table once; `distinct_player_debut_rows()` reads it in O(rows) instead of re-running the heavy join every bootstrap.

Optional warehouse skip-on-unchanged-seed **not implemented** (scope risk; defer to follow-up if needed).

## Design (locked)

| Change | Behavior |
|--------|----------|
| `_save()` under defer | Skips field-index rebuild; `commit_deferred_save()` still rebuilds once before persist |
| `player_debut` | Created at end of `ingest_warehouse()`; index on `playerID` |
| Identity binds | Unchanged — still `distinct_player_debut_rows` → one bind per player |
| CRM / other networks | Generic framework fix; no baseball-only branching |

## Files

| Area | Files |
|------|--------|
| Framework | `src/agents/entity_registry.py` — defer path skips field-index rebuild |
| Pack | `examples/networks/baseball/bootstrap_handlers/lahman_common.py` — `_materialize_player_debut`, simplified `distinct_player_debut_rows` |
| Tests | `tests/test_entity_store_evolution.py` — `test_bootstrap_deferred_save_single_field_index_rebuild` |
| Tests | `tests/test_lahman_seed_handler.py` — `test_lahman_warehouse_materializes_player_debut` |

## Verification

```text
./bin/ci-local                              # 640 smoke passed
uv run pytest tests/test_entity_store_evolution.py tests/test_lahman_seed_handler.py -m smoke -q
```

Live gate: **N/A** — no query behavior change.

## Manual verification (Paul — required)

**Cold bootstrap timing** (compare to Test 9 ~1579 s):

```bash
time ./bin/refresh-example-network baseball --yes --no-default
```

Target: **< 600 s** cold bind (stretch); **< 480 s** excellent.

**Warm handler profile:**

```bash
MYCELIUM_BOOTSTRAP_PROGRESS=0 ./bin/profile-lahman-bootstrap ~/mycelium-networks/baseball
```

Expect `distinct_player_debut_rows` negligible and `build_field_indexes` ~1× at commit.

**Note:** Live root must refresh (`--sync-only` or `--yes`) to pick up `player_debut` materialization — old warehouses without `player_debut` return empty debut rows until reload.

## For Grok + Paul

- Mark bootstrap perf slice shipped; record Test 10 timing in `docs/manual-checks/2026-06-17-storage-evolution-timing-gates.md` after Paul runs cold bootstrap.
- Update program slice map / TODO when approved.

## Suggested commit message

```
perf(baseball): bootstrap deferred index rebuild + player_debut table
```
