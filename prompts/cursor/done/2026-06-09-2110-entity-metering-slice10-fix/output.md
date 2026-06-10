# Output — Entity metering Slice 10 fix (`2110`)

## Summary

Closed five review nits from Slice 10: `EntityQuery.provenance`, policy E2E tests (`full_duplicate`, `meter_first_delivery: false`), `principal_required` outcome, and introspection/doc touch-ups.

## Fixes

| Fix | Change |
|-----|--------|
| **F1** | `EntityQuery.provenance`; wired in `build_workload_spec()`; `test_provenance_meter_on_quote` |
| **F2** | `test_full_duplicate_cache_hit_includes_production` |
| **F3** | `test_meter_first_delivery_false_first_quote` |
| **F4** | `principal_required` outcome + `response_principal_required()`; `metering_principal_required` on graph state |
| **F5** | `test_sponsor_public_principal_required_e2e` |

## Tests

```bash
uv run pytest tests/test_entity_metering.py -q                    # 20 passed
uv run pytest tests/test_entity_research_gate.py tests/test_entity_growth.py -q  # regression OK
```

## For Grok + Paul

- Mark **Metering Slice 10 fix** done in `TODO.md` after review.
- Suggested commit message: `fix(metering): provenance, principal_required, and policy E2E tests (slice 10 fix)`

## Exit criteria

- [x] F1–F5 implemented
- [x] 4 new tests; full metering suite green (20 total)
- [x] Entity protocol regression green
- [x] Ruff clean; no `TODO.md` edit
