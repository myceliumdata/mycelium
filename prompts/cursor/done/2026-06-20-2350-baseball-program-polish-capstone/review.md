# Review — baseball program polish capstone (2350)

**Verdict:** **Approved + polish nits**  
**Reviewer:** Grok  
**Date:** 2026-06-21

## Context

Final slice of the baseball example program. Closes accumulated M5–M14 polish nits: live gate alignment, test gaps, roster scope cache, provenance scope rules, M14 doc/hygiene, program docs. Full diff read before verdict.

**Program status:** M1–M14 + polish **complete** pending Paul's live gate sign-off.

## CI

| Check | Result |
|-------|--------|
| `./bin/ci-local` | **648** smoke passed, ruff clean, admin-ui build ok |
| `LANGCHAIN_TRACING_V2=false uv run pytest -m full -q` | **18** passed (program final gate) |

## Delivery

`output.md` matches files on disk. Nits table is accurate; deferred items correctly documented.

## Spec compliance

| Criterion | Result |
|-----------|--------|
| §1 Live gate — `bb-bio-02` + rate drift helper | Pass — catalog **27** scenarios; anchors in `baseball_aaron_lahman_v2025.json` |
| §1 README `--with-pytest` note | Pass |
| §2 Bio/pitching test gaps | Pass — death_date provenance, zero IPouts, fixture consolidation |
| §3 `attendance` alias | Pass — deferred (not in manifest) |
| §4 `people_compose` columns in provenance | Pass — `parameters.columns` on compose resolves |
| §5 Roster scope cache + 1957/1958 isolation test | Pass — `roster::1957` storage keys |
| §5 Live gate phase minimums | Pass — fielding, roster, franchise added |
| §6 M9 scope provenance (`yearID` only when scoped) | Pass — `scope_in_provenance` flag on `ResolvedField` |
| §6 M9 N2 career_hr lacks `yearID` | Pass |
| §6 M9 N4 deliveries.json assert | Pass |
| §6 M9 N5 unknown year → N/A | Pass — `test_season_wins_unknown_scoped_year_na` (optional, shipped) |
| §7 M13 LAHMAN_CSV_TABLE_COUNT + docs | Pass |
| §8 M14 hierarchy doc + derive doc + deprecation warning + pending cleanup | Pass |
| §9 Program docs sync | Pass — hand-test, live-gate-program, baseball-example-program |
| No new specialists | Pass |
| No bootstrap perf work | Pass |
| CRM unchanged | Pass |
| `TODO.md` untouched | Pass |

## Legacy / dual-path

- **Roster scope cache:** Product fields now use `attr::yearID` storage keys when `scope_sensitive_fields` is set; framework `query_provenance` reads scoped keys on deliver and normalizes `attribute` in response — necessary companion to M11 N1.
- **Provenance scope:** `career_sum` / `career_era_weighted` omit `yearID` (default `scope_in_provenance=False`); `season_column` and scoped `team_latest_column` include it — matches M9 design lock.
- **Bio tests:** Consolidated onto `baseball_minimal_fixture`; `test_bats` now expects `R` from shared fixture (was `L` with local override — correct).
- **Legacy `run_warehouse_player_graph`:** DeprecationWarning when `on_miss` args passed.

## Tests

**Strong additions:**

- Roster 1957 vs 1958 cache isolation
- career_hr provenance lacks `yearID` under scope
- death_date provenance shape + missing deathMonth → N/A
- career_era zero IPouts → N/A
- season_wins unknown year → N/A

**Gaps (non-blocking):**

- No unit test for `rate_value_drift()` / `RATE_DRIFT_ATTRS` in `gate_runner.py`
- `bb-bio-02` not covered by unit catalog test beyond minimum count (live gate only)

## Design critique

**Strong:** Capstone does what it should — closes the nit backlog without new domains. Roster scope fix is the highest-value change (M11 design lock). Framework provenance read for scoped storage keys is the right companion and stays narrow (candidate key list + attribute normalization). Doc sync brings program plan current.

**Sub-optimal (non-blocking):**

- `SCOPE_PROVENANCE_CONVENTIONS` defined in `warehouse_resolve.py` but unused — dead constant.
- `warehouse_stat.py` `write_computed_field(..., parameters=...)` block has misaligned indentation (valid Python, sloppy).
- `baseball_minimal_fixture.reset_runtime`: `reset_fn(    )` stray whitespace.
- M13 test imports `LAHMAN_CSV_TABLE_COUNT` via `importlib` instead of direct module import — works but verbose.

## Polish nits (non-blocking)

| # | Nit | Notes |
|---|-----|-------|
| N1 | Unused `SCOPE_PROVENANCE_CONVENTIONS` | Remove or wire into resolve helpers |
| N2 | `warehouse_stat.py` indentation on `parameters=` kwarg | Formatting only |
| N3 | `reset_fn(    )` in `baseball_minimal_fixture.py` | Trivial whitespace |
| N4 | `rate_value_drift` unit test | Optional — live drift paths exercised manually |

No follow-on slice required — program complete after Paul's live gate.

## Diff reviewed

- `docs/architecture/whys/specialist-class-hierarchy.md`
- `docs/manual-checks/2026-06-19-baseball-specialist-hand-test.md`
- `docs/manual-checks/2026-06-20-live-gate-program.md`
- `docs/plans/baseball-example-program.md`
- `docs/seed-bootstrap.md`
- `examples/networks/baseball/README.md`
- `examples/networks/baseball/specialists/derive_resolve.py`
- `examples/networks/baseball/specialists/pack_common.py`
- `examples/networks/baseball/specialists/product_common.py`
- `examples/networks/baseball/specialists/roster_specialist.py`
- `examples/networks/baseball/specialists/warehouse_resolve.py`
- `src/agents/dispatch.py`
- `src/agents/query_provenance.py`
- `src/agents/specialists/warehouse_stat.py`
- `tests/baseball_minimal_fixture.py`
- `tests/live/catalogs/baseball.yaml`
- `tests/live/gate_runner.py`
- `tests/test_baseball_*.py` (batting, bio, pitching, roster, team_season)
- `tests/test_delivery_store.py`
- `tests/test_lahman_seed_handler.py`
- `tests/test_live_gate_runner_unit.py`
- `prompts/cursor/done/2026-06-20-2350-baseball-program-polish-capstone/` (`prompt.md`, `output.md`)

## For Paul

- **Baseball program code complete.** Manual sign-off path:
  1. Finish pre/post-2280 bootstrap timing if still in flight
  2. `./bin/refresh-example-network baseball --sync-only` (or full re-bootstrap if warehouse stale)
  3. `./bin/gate-live baseball` — expect **27/27** on fresh Lahman root
  4. Update `TODO.md` when satisfied (Grok/Paul only)
- **Website update** still queued separately per program plan.
- **Commit message:** `polish(baseball): program capstone — gate alignment, test gaps, smoke parity`