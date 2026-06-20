# Baseball pitching rate stats — career_era (M8)

> **READY** — Depends on M5 `pitching_specialist` in tree. **Do not edit `TODO.md`.**

## Objective

Ship **`career_era`** (and optionally season `era`) via manifest **recipe** convention on pitching domain — innings-weighted aggregate, pool-then-divide (see `warehouse_domains.json` batting `rate_from_aggregates` note).

## Implementation

1. Add `career_era` alias to `warehouse_domains.json` pitching domain with new convention e.g. `career_era_weighted` (document formula: `9 * ER / IP` with `IP = IPouts/3`, summed across Pitching rows).
2. Implement resolver in `examples/networks/baseball/specialists/warehouse_resolve.py`.
3. `pitching_specialist` picks it up automatically via `resolve_domain_attribute`.

## Tests

- Minimal fixture: Pitching rows with known ER/IPouts → expected ERA string (3 decimals).
- `tests/test_baseball_pitching_specialist.py` smoke + provenance `parameters.inline` / computation inline.

## Live gate (required)

Add **`bb-pitch-03`** to `tests/live/catalogs/baseball.yaml` (phase `pitching`):

- Nolan Ryan (`{{ anchors.pitcher_player }}`) `career_era` — two-step deliver.
- Anchor `pitcher_career_era` in `baseball_aaron_lahman_v2025.json` from live root (Ryan has non-zero pitching; Aaron ERA is not a useful gate).
- Extend `gate_runner.py` drift check for `pitcher_career_era` on Ryan.

Note: `bb-pitch-01`–`02`, `bb-multi-01`, `bb-team-01` already shipped (M5–M6 gate). Do not duplicate.

`@pytest.mark.live_gate` only — never default CI.

## Optional

- `derive_on_miss: true` on pitching for unsupported rate labels — only if small; else defer.