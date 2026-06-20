# Review — baseball warehouse stat specialist base class (M14)

**Verdict:** **Approved + polish nits**  
**Reviewer:** Grok  
**Date:** 2026-06-21

## Context

Cursor slice from `prompts/cursor/next/2026-06-20-2340-baseball-warehouse-stat-specialist-base-class-m14.md`. Promotes warehouse player/team stat graph orchestration and manifest-driven derive-on-miss into framework `WarehousePlayerStatSpecialist` / `WarehouseTeamStatSpecialist`; baseball pack becomes thin subclasses + `baseball_warehouse_hooks.py`. Full diff read (including untracked new files) before verdict.

**Show-stoppers for 2350:** **None.**

## CI

| Check | Result |
|-------|--------|
| `./bin/ci-local` | **643** smoke passed, ruff clean, admin-ui build ok |
| `uv run pytest tests/test_warehouse_stat_specialist.py tests/test_baseball_* -m smoke -q` | 12 passed (warehouse + batting/derive subset) |

## Delivery

`output.md` matches files on disk. Implementation complete — framework bases in `src/`, not pack-only.

## Spec compliance

| Criterion | Result |
|-----------|--------|
| `WarehousePlayerStatSpecialist` + `WarehouseTeamStatSpecialist` in `src/agents/specialists/` | Pass — `warehouse_stat.py` (649 lines) |
| `run(state)` canonical graph entry | Pass — moved from `pack_common` evaluate loops |
| `derive_on_miss_enabled()` reads manifest for `self.domain` | Pass — uses `domain_meta()` |
| `resolve_derive_on_miss()` from batting derive path | Pass — logic matches pre-M14 `_batting_derive_on_miss_resolve` |
| Pack hooks — no `src/` → `examples/` imports | Pass — only comment in `example.py`; hooks live in pack |
| Baseball thin subclasses (~15–36 lines) | Pass — batting 195 → 36 |
| `batting` manifest `derive_on_miss: true` unchanged | Pass |
| `product_common` / roster / franchise untouched | Pass |
| Framework unit test for `derive_on_miss_enabled` | Pass — `tests/test_warehouse_stat_specialist.py` |
| Exports from `src/agents/specialists/__init__.py` | Pass |
| Live gate | N/A — refactor only |
| `TODO.md` untouched | Pass |
| CRM regression | Pass — new module only; no CRM specialist edits |

## Legacy / dual-path

- **Derive gating improved:** Pre-M14 `_batting_derive_on_miss()` always returned `True`; manifest gate lived only inside `_batting_derive_on_miss_resolve`. M14 gates at the evaluate loop via `derive_on_miss_enabled(manifest)` — same outcomes, cleaner contract.
- **`pack_common` legacy wrappers:** `run_warehouse_player_graph` / `run_warehouse_team_graph` delegate to `agent.run()`; `on_miss` / `on_miss_resolve` params accepted but ignored (no remaining callers in repo).
- **Helper promotion:** `coerce_state`, `query_year_id`, `evaluate_*` loops promoted to framework; `pack_common` re-exports for `product_common` / `registry_identity_common`.
- **Mixin pattern:** `BaseballWarehousePlayerHooks` / `BaseballWarehouseTeamHooks` supply Lahman source keys + resolver loaders; specialists use `(Hooks, FrameworkBase)` MRO.

## Tests

**Covered:**

- Framework manifest flag unit tests (true/false/missing/wrong domain).
- `NotImplementedError` when `_load_warehouse_resolve` missing.
- Existing baseball batting/derive smokes unchanged (12 passed in targeted run).

**Gaps (non-blocking):**

- No framework-level mocked test for full `resolve_derive_on_miss` pipeline (baseball smokes cover end-to-end).
- No test that legacy `run_warehouse_*` wrappers reject non-framework agents (TypeError path).

## Design critique

**Strong:** Delivers Paul’s hierarchy lock — framework middle tier between `SpecialistAgent` and pack thin subclasses. Batting derive logic lifted once; enabling derive on pitching/bio is manifest-only. Pack hooks keep Lahman modules out of `src/`. Line-count reduction (~700 lines net) without behavior change.

**Sub-optimal (non-blocking):**

- `derive_on_miss_enabled` duplicated in framework (`warehouse_stat.py`) and pack (`derive_resolve.py`) — same semantics, two homes.
- `pending` list in `_evaluate_*_warehouse_fields` is never populated (carried from old `pack_common`; dead weight).
- `baseball_warehouse_hooks.py` imports `specialist_loader` without its own `pack_bootstrap` block — safe today because specialists bootstrap first, fragile if imported standalone.
- `warehouse_stat.py` is ~650 lines — candidate to split helpers vs classes in a follow-on, not blocking.

## Polish nits (non-blocking)

| # | Nit | Follow-up |
|---|-----|-----------|
| N1 | `docs/architecture/whys/specialist-class-hierarchy.md` “Current state” still shows pre-M14 fat batting / pack_common wrappers | Update diagram in `2350` §8 docs |
| N2 | Duplicated `derive_on_miss_enabled` (framework + `derive_resolve.py`) | Consolidate or document single source in `2350` |
| N3 | Legacy `run_warehouse_*` silently drops `on_miss` args | Remove params or emit deprecation warning — `2350` |
| N4 | Unused `pending` list in evaluate loops | Remove or wire pending-field path — `2350` |
| N5 | Framework integration test for `resolve_derive_on_miss` (mocked derive) | Optional — `2350` |
| N6 | M9 N1 still open: `year_id` passed to all `provenance_parameters` | Already in `2350` §6 |

Folded into `2350` where noted.

## Diff reviewed

- `src/agents/specialists/warehouse_stat.py` (new)
- `src/agents/specialists/__init__.py`
- `examples/networks/baseball/specialists/baseball_warehouse_hooks.py` (new)
- `examples/networks/baseball/specialists/batting_specialist.py`
- `examples/networks/baseball/specialists/pitching_specialist.py`
- `examples/networks/baseball/specialists/bio_specialist.py`
- `examples/networks/baseball/specialists/fielding_specialist.py`
- `examples/networks/baseball/specialists/team_season_specialist.py`
- `examples/networks/baseball/specialists/pack_common.py`
- `tests/test_warehouse_stat_specialist.py` (new)
- `prompts/cursor/done/2026-06-20-2340-baseball-warehouse-stat-specialist-base-class-m14/` (`prompt.md`, `output.md`)

## For Paul

- **M14 hierarchy shipped** — warehouse stat tier is framework-owned; baseball pack is thin hooks + declarations.
- **Operator (after pull / sync):**
  ```bash
  ./bin/refresh-example-network baseball --sync-only
  ./bin/gate-live baseball
  ```
  Your live root still needs full refresh for `bb-field-01` (`Fielding` table) — unrelated to M14 but blocks 26/26.
- **Next Cursor slice:** `2026-06-20-2350-baseball-program-polish-capstone.md` — prerequisites now include M14 Approved.
- **Commit message:** `feat(specialists): warehouse stat base classes + baseball thin subclasses (M14)`