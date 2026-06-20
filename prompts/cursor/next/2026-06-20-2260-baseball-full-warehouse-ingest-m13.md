# Baseball full Lahman warehouse ingest (M13)

> **READY** — Bootstrap expansion. **Do not edit `TODO.md`.**

## Objective

Extend `BOOTSTRAP_TABLES` in `examples/networks/baseball/bootstrap_handlers/lahman_common.py` to ingest **all 27 Lahman CSV tables** (or documented subset per readme2025.txt), not the current 6-table sliver.

## Constraints

- Keep bootstrap time measurable — document row counts in bootstrap report.
- `warehouse_manifest.json` regeneration must include new tables/domains as needed.
- Do not change uuid stability rules on player/team registries.

## Tests

- `tests/test_lahman_seed_handler.py` — assert additional table counts > 0 on minimal fixture (add tiny CSV stubs per table).
- Smoke refresh still completes in seconds on minimal fixture.

## Live gate

**N/A for new scenarios** — M13 expands bootstrap tables; existing gate scenarios (`bb-pitch-*`, `bb-team-*`, etc.) should keep passing after Paul runs `--sync-only` on the live root.

**Required follow-up in `output.md`:**

- Ask Paul to run `./bin/gate-live baseball` on the live root after reload.
- If any anchor drifts (row-count or stat changes), update `baseball_aaron_lahman_v2025.json` + drift checks — do not weaken assertions without documenting why.

## Manual

- Note in `output.md` for Paul: re-run timing test 6 after merge on full Lahman zip.