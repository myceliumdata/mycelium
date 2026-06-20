# Review — baseball bio manifest aliases (M7)

**Verdict:** **Approved + polish nits**  
**Reviewer:** Grok  
**Date:** 2026-06-20  
**Commit:** `e765e66` (bundled with M8)

## Context

Cursor slice claimed from `prompts/cursor/next/2026-06-20-2200-baseball-bio-manifest-aliases-m7.md`. Pack-only manifest + `warehouse_resolve` work; `bio_specialist` unchanged (thin `pack_common` wrapper). Full diff read before verdict.

## CI

| Check | Result |
|-------|--------|
| `./bin/ci-local` | **628** smoke passed, ruff clean, admin-ui build ok |
| `uv run pytest tests/test_baseball_bio_specialist.py -m smoke -q` | **9** passed (4 prior + 5 new) |
| `uv run pytest tests/test_live_gate_runner_unit.py -q` | **16** passed |

## Delivery

`output.md` matches files on disk. Implementation complete.

## Spec compliance

| Criterion | Result |
|-----------|--------|
| `height`, `weight`, `birth_country`, `final_game` → `people_column` | Pass |
| `death_date` → `people_compose` / iso_date | Pass — uses shared `people_compose_iso_date` |
| `people_birth_date` refactored to delegate (no behavior change) | Pass — `birth_date` smoke + provenance still green |
| `birth_date` manifest now lists explicit `columns` | Pass — required for generalized compose resolver |
| Minimal fixture People.csv extended | Pass — shared `baseball_minimal_fixture.py` |
| One smoke test per new alias | Pass — deliver-only, no provenance per alias |
| Live gate `bb-bio-01` + anchors + drift | Pass — height/weight/birth_country |
| No new specialist file | Pass |
| Framework `src/` untouched | Pass |
| `TODO.md` untouched | Pass |

## Legacy / dual-path

- Existing `birth_date` / `bats` / `birth_date` provenance tests unchanged in behavior; birth_date provenance inline assertion widened to accept `people_compose_iso_date` wrapper — correct.
- `warehouse_domains.json` committed shape now requires `columns` on `people_compose` aliases. Live roots must `--sync-only` to pick up manifest; stale manifest would break `birth_date` resolve (fail loud → `N/A`).

## Tests

**Covered:** deliver path for all five new aliases on shared minimal fixture (Aaron: height **72**, weight **180**, birth_country **USA**, final_game **1976-10-03**, death_date **2021-01-22**).

**Gaps (non-blocking):**

- No provenance-shape test for any new alias (contrast `test_birth_date_provenance_shape`).
- No `N/A` path for partial `deathYear`/`deathMonth`/`deathDay` (contrast `test_birth_date_missing_birth_month_na`).
- `test_baseball_bio_specialist.py` still carries a **local** thin `_write_minimal_lahman_fixture` (no bio columns) for legacy birth_date/bats tests while new tests use `refresh_shared_fixture` — pre-existing split, slightly confusing for readers.

## Design critique

**Strong:** `people_compose_iso_date(columns, …)` is the right abstraction — one SQL shape, safe column quoting, shared by `birth_date` and `death_date`. Inline provenance correctly picks `PEOPLE_BIRTH_DATE_INLINE` vs `PEOPLE_COMPOSE_ISO_DATE_INLINE` based on column set. Manifest entries are minimal and consistent with M2b patterns. Live gate drift extended for Aaron bio attrs in `gate_runner.py` without duplicating scenario logic.

**Sub-optimal (non-blocking):**

- `people_compose` resolver returns `column=None` in `ResolvedField` — provenance cannot cite which People columns were read (same gap as M2b P3 for compose attrs).
- `final_game` in fixture is stored as Lahman’s native `finalGame` string (`1976-10-03`) not a computed value — fine for Lahman, but hand-test doc should not imply compose for that row.
- Live gate covers 3 of 5 new aliases; compose attrs (`death_date`) and `final_game` rely on smoke only.

## Polish nits (non-blocking)

| # | Nit | Follow-up |
|---|-----|-----------|
| N1 | `bb-bio-01` omits `final_game` / `death_date` | Extend scenario or add `bb-bio-02` on live root |
| N2 | No provenance test for `death_date` compose inline | One test mirroring `test_birth_date_provenance_shape` |
| N3 | No partial-death-column → `N/A` test | Mirror birth_month gap test for `deathMonth` |
| N4 | Bio test module duplicate fixture helpers vs `baseball_minimal_fixture` | Consolidate legacy tests onto shared fixture in a polish slice |
| N5 | Drift loop queries `final_game`/`death_date` but catalog does not gate them | Align drift with `bb-bio-01` attrs or add gate paths |

## Diff reviewed

- `examples/networks/baseball/warehouse_domains.json`
- `examples/networks/baseball/specialists/warehouse_resolve.py` — `people_compose_iso_date`, compose branch, `people_birth_date` delegate
- `tests/baseball_minimal_fixture.py`
- `tests/test_baseball_bio_specialist.py`
- `tests/live/catalogs/baseball.yaml` — `bb-bio-01`
- `tests/live/anchors/baseball_aaron_lahman_v2025.json`
- `tests/live/gate_runner.py` — Aaron bio drift attrs
- `tests/test_live_gate_runner_unit.py` — scenario count ≥ 21
- `prompts/cursor/done/2026-06-20-2200-baseball-bio-manifest-aliases-m7/` (`prompt.md`, `output.md`)

## For Paul

- **Operator:** `./bin/refresh-example-network baseball --sync-only` then `./bin/gate-live baseball`.
- **Next slice:** `2026-06-20-2220-baseball-query-scope-yearid-m9.md` (unless bootstrap perf `2280` is prioritized).
- **Commit:** bundled in `e765e66` with M8.