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
- `tests/test_baseball_pitching_specialist.py` smoke + provenance `parameters.column` / computation inline.

## Optional

- `derive_on_miss: true` on pitching for unsupported rate labels — only if small; else defer.