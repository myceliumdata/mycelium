# Review — baseball pitching career_era (M8)

**Verdict:** **Approved + polish nits**  
**Reviewer:** Grok  
**Date:** 2026-06-20  
**Commit:** `e765e66` (bundled with M7)

## Context

Cursor slice from `prompts/cursor/next/2026-06-20-2210-baseball-pitching-era-rate-m8.md`. Adds manifest-driven **`career_era`** via new convention `career_era_weighted`; includes manual gate doc sync deferred from M5–M6. Full diff read before verdict.

## CI

| Check | Result |
|-------|--------|
| `./bin/ci-local` | **628** smoke passed, ruff clean, admin-ui build ok |
| `uv run pytest tests/test_baseball_pitching_specialist.py -m smoke -q` | **4** passed |
| Baseball catalog scenarios | **21** (unit test `test_load_catalog_baseball_has_minimum_scenarios`) |

## Delivery

`output.md` matches files on disk. Implementation complete.

## Spec compliance

| Criterion | Result |
|-----------|--------|
| `career_era` alias → `career_era_weighted` convention | Pass |
| Formula: `9 * SUM(ER) / (SUM(IPouts)/3)` pool-then-divide | Pass — matches manifest note |
| Resolver in `warehouse_resolve.py` | Pass — `career_era_weighted()` + `resolve_domain_attribute` branch |
| `pitching_specialist` picks up via manifest (no specialist edit) | Pass |
| Fixture ERA **3.000** (Aaron: 9 ER, 81 IPouts) | Pass — verified arithmetic on two pitching rows |
| Smoke + provenance test | Pass |
| Live gate `bb-pitch-03` Nolan Ryan ≈ **3.194** | Pass — `approx` + tolerance 0.001 |
| Drift check with float tolerance for `career_era` | Pass |
| Manual gate docs synced (hand-test + live-gate-program) | Pass — pitching/team_season ✅, catalog **21** |
| Season `era` / `derive_on_miss` deferred | Pass per prompt |
| `TODO.md` untouched | Pass |

## Legacy / dual-path

- `career_wins` / `career_sum` paths unchanged; `_deliver_attr` refactor is rename-only for existing tests.
- Rate stat correctly omits `parameters.column` (no single Lahman column); `attribute` + `lahman.playerID` + `warehouse` still flow via `provenance_parameters`.
- Manual doc correctly updates M8 prompt’s stale “19 scenarios” to **21** in `2026-06-20-live-gate-program.md`.

## Tests

**Covered:** deliver + provenance for `career_era`; fixture exercises **two** pitching rows pooled (not a single-row shortcut).

**Gaps (non-blocking):**

- No test for `ipouts == 0` → `None` → specialist `N/A` (Aaron fixture always has outs).
- Provenance test asserts `attribute` and inline contains `career_era_weighted` **or** `IPouts` — loose OR weakens regression (either substring passes).
- Provenance test does not assert `parameters.warehouse` (birth_date/batting tests do elsewhere).
- No live-gate unit test for `approx` path on `bb-pitch-03` (catalog integration only at gate runtime).

## Design critique

**Strong:** Convention is documented in manifest `conventions.career_era_weighted` and implemented as a single warehouse aggregate query — correct pool-then-divide semantics, not per-season ERA averaged. Table name comes from `_domain_table(manifest, domain)` so pitching domain stays table-aware. Gate uses existing `approx`/`tolerance` machinery in `tests/live/assertions.py`. Drift check mirrors catalog tolerance (0.001) for Ryan — good operator UX.

**Sub-optimal (non-blocking):**

- `CAST("ER" AS INTEGER)` / `CAST("IPouts" AS INTEGER)` — fine for Lahman integers; would truncate if fractional ER ever appeared.
- `career_era_weighted` returns formatted string `f"{era:.3f}"` — deliver compares as string; gate drift uses `float()` — consistent but implicit typing.
- Float drift logic duplicated inline in `gate_runner.py` (special-case `key == "career_era"`) rather than shared with assertion helper — acceptable for one rate attr, will multiply if more rate gates land (M9 `career_avg` already uses catalog `approx`).
- `test_baseball_pitching_specialist.py` missing trailing newline at EOF (pre-existing file, still true after edit).

## Polish nits (non-blocking)

| # | Nit | Follow-up |
|---|-----|-----------|
| N1 | Provenance test uses loose `or` on inline substring | Assert `career_era_weighted` in inline specifically |
| N2 | No `warehouse` key assert on `career_era` provenance test | Match `test_birth_date_provenance_shape` / career_wins pattern |
| N3 | No zero-IPouts / no-pitching-rows → `N/A` smoke | Minimal fixture row with `IPouts=0` |
| N4 | `gate_runner` float drift special-case | Extract `rate_attrs` set if M9 adds more rate drift checks |
| N5 | File ends without newline (`test_baseball_pitching_specialist.py`) | Trivial formatter pass |
| N6 | `bin/smoke-baseball-e2e` still has no inline `career_era` row | Optional parity with pytest (same nit family as M5–M6 P1) |

## Diff reviewed

- `examples/networks/baseball/warehouse_domains.json` — pitching convention + alias
- `examples/networks/baseball/specialists/warehouse_resolve.py` — `career_era_weighted`, resolve branch, inline constants
- `tests/baseball_minimal_fixture.py` — Pitching ER/IPouts for 3.000 ERA
- `tests/test_baseball_pitching_specialist.py`
- `tests/live/catalogs/baseball.yaml` — `bb-pitch-03`
- `tests/live/anchors/baseball_aaron_lahman_v2025.json` — `pitcher_career_era`
- `tests/live/gate_runner.py` — ERA drift tolerance
- `docs/manual-checks/2026-06-19-baseball-specialist-hand-test.md`
- `docs/manual-checks/2026-06-20-live-gate-program.md`
- `docs/plans/baseball-example-program.md` — M6b/M7 ✅
- `prompts/cursor/done/2026-06-20-2210-baseball-pitching-era-rate-m8/` (`prompt.md`, `output.md`)

## For Paul

- **Operator:** `--sync-only` on live root; `./bin/gate-live baseball` — expect **21** scenarios; `bb-pitch-03` on Nolan Ryan.
- **Commit:** `e765e66` (`baseball: M7 bio aliases + M8 career_era`).
- **Next:** M9 query scope (`2026-06-20-2220-baseball-query-scope-yearid-m9.md`) or bootstrap perf (`2280`) if refresh time blocks you.