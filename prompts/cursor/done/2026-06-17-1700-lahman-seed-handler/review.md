# Review — 2026-06-17-1700-lahman-seed-handler

**Verdict: Approved + polish nits**

---

## CI

| Step | Result |
|------|--------|
| `uv sync --all-extras` | Pass |
| `admin-ui` build | Pass |
| `ruff` | Pass |
| smoke pytest | **436 passed**, 93 deselected |

```bash
./bin/ci-local
# CI local: all steps passed.
```

Baseline after 1500: 433 passed. **+3** Lahman tests (including multi-team same `playerID`).

---

## Delivery

`output.md` matches working tree. `prompt.md` present (proper claim). Pack handlers, framework helpers, tests, manifest, README, program doc note delivered.

**Workflow note:** Slice followed queue correctly (`1700` prompt claimed). Contrast with improvised `1600` (no prompt, no review).

---

## Diff reviewed

| File | Notes |
|------|--------|
| `bootstrap_handlers/lahman_common.py` | Seed resolve, warehouse, `distinct_player_team_rows` with `playerID` |
| `bootstrap_handlers/lahman_seed.py` | `player_ids` map, `add_bind_alias`, conflict error path |
| `entity_registry.py` | `add_bind_alias()` |
| `category_mvr_bootstrap.py` | All-grain bind field merge; `team` → `professional` |
| `attribute_write.py` | `write_bind_fields` → `reg._mvr` |
| `network.json`, README | Pack bootstrap documented |
| `tests/test_lahman_seed_handler.py` | 3 smoke tests |
| `tests/test_multi_mvr_entity_stores.py` | `lahman_seed` handler_id |
| `docs/plans/baseball-example-program.md` | Slice 2 shipped note |

---

## Spec compliance

| # | Criterion | Result |
|---|-----------|--------|
| E1 | Pack handler; manifest points at it | Pass |
| E2 | Seed → warehouse + team/player grains | Pass |
| E3 | Multi-team same `playerID` → one uuid, 2 bind keys | Pass (`test_lahman_seed_handler_multi_team_same_player_id`) |
| E4 | No seed → 0 entities | Pass |
| E5 | `reg._mvr` + category merge for `team` | Pass |
| E6 | CRM capstones unchanged | Pass |
| E7 | `./bin/ci-local` green | Pass |

L1–L10 locked decisions implemented. Non-goals respected (no query orchestrator, no zip in git).

---

## Compare to stashed improvised work (`stash@{0}`)

| Area | Stash (option A) | This slice (1700) |
|------|------------------|-------------------|
| **Process** | No `next/` prompt | Prompt + `prompt.md` in `done/` |
| **Player teams** | `distinct_player_team_pairs(name, team)` — **one entity per pair** | `distinct_player_team_rows(playerID, …)` — **one uuid per `playerID`** |
| **Alias index** | None; repeated `ensure_entity_bind_fields` | `add_bind_alias()` + `player_ids` map |
| **Framework** | `category_mvr_bootstrap`, `write_bind_fields` only | Same + **`entity_registry.add_bind_alias`** |
| **Tests** | 2 tests | **3 tests** (+ multi-team same id) |
| **README** | Shorter bootstrap note | Full seed layout, grains, category mapping |
| **lahman_common** | `distinct_player_team_pairs` | `distinct_player_team_rows` includes `playerID` in SQL |
| **lahman_seed** | ~85 lines, flat pair loop | ~109 lines, dedup + error on bind conflict |

**Shared (~identical):** warehouse ingest tables, seed zip resolution, team label commit loop, manifest bootstrap block, `attribute_write` / `category_mvr_bootstrap` changes, minimal Aaron fixture test.

**Bottom line:** Improvised work was a useful spike (~80% overlap on ingest/teams); the **spec-mandated gap** is **L6/L7 player dedup + multi-team bind aliases**, which only the proper slice implements.

---

## Design critique

**Strong**

- `add_bind_alias` is minimal and reusable for bootstrap.
- Conflict detection when bind key maps to wrong entity (fail loud).
- `distinct_player_team_rows` stable ordering aids reproducible bootstrap.
- README documents CRM `team` → `professional` mapping honestly.

**Sub-optimal (non-blocking)**

- `add_bind_alias` has no direct unit test (covered via integration test only).
- `entities_committed` counts new players only — correct, but `entities_by_grain.player` does not count alias keys (fine for v1).
- `TODO.md` edited by Cursor (workflow violation) — Grok corrects on commit.

---

## Nits

| ID | Item |
|----|------|
| N1 | Optional unit test for `EntityRegistry.add_bind_alias` |
| N2 | Cursor edited `TODO.md` — reverted/corrected in Grok commit |

---

## For Paul

- **Commit:** Grok committing locally.
- **Stash:** Keep `stash@{0}` for archaeology or `git stash drop` after you're satisfied with comparison.
- **Next:** Queue query orchestrator grain selection slice.
- **Live baseball:** `refresh-example-network baseball --yes` + seed under `~/mycelium-networks/baseball/seed/`.