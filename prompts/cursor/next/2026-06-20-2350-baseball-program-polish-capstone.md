# Baseball example program — polish capstone (run last)

> **RUN LAST** — Claim only when M9–M13 and bootstrap perf (`2280`) are in `prompts/cursor/done/` with Grok **Approved** reviews. If any feature slice is **Not Approved** or awaiting fix, do **not** start this slice. **Do not edit `TODO.md`.**

## Objective

Close accumulated **non-blocking polish nits** from M5–M8 reviews and cross-cutting program debt in one pass — tests, live gate alignment, smoke script parity, small code hygiene. No new domains, no framework contract changes unless explicitly listed below.

## Prerequisites (verify before claiming)

- [ ] `2026-06-20-2220-baseball-query-scope-yearid-m9` — Approved
- [ ] `2026-06-20-2230-baseball-fielding-domain-m10` — Approved
- [ ] `2026-06-20-2240-baseball-roster-product-specialist-m11` — Approved
- [ ] `2026-06-20-2250-baseball-franchise-specialist-m12` — Approved
- [ ] `2026-06-20-2260-baseball-full-warehouse-ingest-m13` — Approved
- [ ] `2026-06-20-2280-baseball-bootstrap-perf-index-and-debut` — Approved (or Paul waives bootstrap slice)
- [ ] `2026-06-20-2340-baseball-warehouse-stat-specialist-base-class-m14` — Approved

Read polish nits in:

- `prompts/cursor/done/2026-06-20-2100-baseball-domain-parity-m5-m6/review.md`
- `prompts/cursor/done/2026-06-20-2200-baseball-bio-manifest-aliases-m7/review.md`
- `prompts/cursor/done/2026-06-20-2210-baseball-pitching-era-rate-m8/review.md`
- Plus any nits from M9–M13 reviews (fold into this slice if still open)

## Work items

### 1 — Live gate alignment (bio + rates)

| Item | Action |
|------|--------|
| M7 N1/N5 | Extend `bb-bio-01` **or** add `bb-bio-02` gating `final_game` + `death_date` (anchors already in JSON) |
| M8 N4 | Extract shared **rate drift** helper in `gate_runner.py` (used by `career_era`, existing `career_avg`/`ops` approx attrs) |
| M5–M6 P1 | Optional: add pitching/team_season/`career_era` rows to `bin/smoke-baseball-e2e` **or** document `--with-pytest` as default in baseball README |

Update `tests/test_live_gate_runner_unit.py` minimum scenario count if catalog grows.

### 2 — Test coverage gaps

| Item | Action |
|------|--------|
| M7 N2 | `test_death_date_provenance_shape` — mirror `test_birth_date_provenance_shape` |
| M7 N3 | Partial `deathMonth` missing → `N/A` smoke |
| M7 N4 | Consolidate `test_baseball_bio_specialist.py` onto `baseball_minimal_fixture.refresh_baseball_root` (remove duplicate local `_write_minimal_lahman_fixture` where possible) |
| M8 N1 | Tighten `test_career_era_provenance_shape` — require `career_era_weighted` in inline (remove loose `or IPouts`) |
| M8 N2 | Assert `parameters.warehouse` on career_era provenance |
| M8 N3 | Zero `IPouts` pitching row → `career_era` `N/A` smoke |
| M8 N5 | Trailing newline + trivial format on `test_baseball_pitching_specialist.py` |

### 3 — Manifest / ontology (only if still missing after M9–M13)

| Item | Action |
|------|--------|
| M5–M6 P2 | `attendance` team_season alias — **only if** M13 did not add it; else skip with note in `output.md` |

### 4 — Provenance metadata (optional, small)

| Item | Action |
|------|--------|
| M2b/M7 | For `people_compose` resolves, include compose column list in `parameters` (e.g. `parameters.columns` or `parameters.compose_columns`) — pack `warehouse_resolve` + provenance tests only |

Skip if M9–M13 already addressed; do not expand scope into framework provenance redesign.

### 5 — M10–M12 product/fielding polish (from review)

| Item | Action |
|------|--------|
| M11 N1 | Roster cache: storage key must include `yearID` (design lock) — scope-aware cache or recompute on scope mismatch |
| M11 N2 | Test 1957 then 1958 roster on same team after N1 |
| M11 N3 | Use or drop `roster_count_1957_bro` anchor |
| M10/M12 N | Extend `test_live_gate_runner_unit` minimum phases: `fielding`, `roster`, `franchise` |
| M12 N1 | Optional: enrich franchise labels from `TeamsFranchises` |

### 6 — M9 scope polish (from review)

| Item | Action |
|------|--------|
| M9 N1 | `provenance_parameters` / `team_provenance_parameters`: include `yearID` only when resolve convention uses scope (`team_latest_column`, `season_column`) — not `career_sum` / `career_era_weighted` |
| M9 N2 | `test_career_hr_ignores_year_scope`: assert provenance lacks `yearID` after N1 |
| M9 N3 | Trailing newline on `test_baseball_team_season_specialist.py` |
| M9 N4 | Restore `deliveries.json` exists assert on `test_issue_delivery_roundtrip` |
| M9 N5 | Optional: team scope with unknown `yearID` → `N/A` smoke |

### 7 — M13 bootstrap polish (from review)

| Item | Action |
|------|--------|
| M13 N1 | `test_lahman_seed_handler`: assert against `LAHMAN_CSV_TABLE_COUNT` import |
| M13 N2 | `docs/seed-bootstrap.md`: document `warehouse_ingest_counts` on `BootstrapResult` |
| M13 N3 | Optional: surface ingest counts in bootstrap progress/CLI output |

### 8 — M14 warehouse hierarchy polish (from review)

| Item | Action |
|------|--------|
| M14 N1 | `docs/architecture/whys/specialist-class-hierarchy.md` — refresh “Current state” diagram to post-M14 hierarchy |
| M14 N2 | Consolidate or document single source for `derive_on_miss_enabled` (framework vs `derive_resolve.py`) |
| M14 N3 | `run_warehouse_*` legacy wrappers: remove dead `on_miss` params or warn on use |
| M14 N4 | Remove unused `pending` list in `_evaluate_*_warehouse_fields` or wire pending-field path |
| M14 N5 | Optional: framework mocked test for `resolve_derive_on_miss` |

### 9 — Docs

- `docs/manual-checks/2026-06-19-baseball-specialist-hand-test.md` — ensure polish gate scenarios cited; remove any stale ⏳ rows superseded by M9–M14.
- `docs/manual-checks/2026-06-20-live-gate-program.md` — final scenario count + phase list after all catalog changes.
- `docs/plans/baseball-example-program.md` — update slice map (M9–M14 shipped, gate count 26).

## Live gate (required)

Any **new** scenarios from §1 must follow WORKFLOW §1 (anchors, drift, phases). If §1 only tightens existing scenarios, say **unchanged count** in `output.md`.

## Constraints

- No new specialists beyond what M9–M13 already shipped.
- No bootstrap perf work here (that's `2280`).
- `./bin/ci-local` must pass.
- CRM unchanged.

## Output

Follow `prompts/cursor/WORKFLOW.md`. In `output.md` **For Grok + Paul**:

- Table of nits addressed vs deferred with reason.
- Final baseball live gate scenario count.
- Ask Paul to run `./bin/gate-live baseball` on live root.
- Suggest program **manual gate** sign-off path.

Suggested commit message:

```
polish(baseball): program capstone — gate alignment, test gaps, smoke parity
```