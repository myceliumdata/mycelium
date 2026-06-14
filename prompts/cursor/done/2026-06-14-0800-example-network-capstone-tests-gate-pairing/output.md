# Example network capstone tests + gate ↔ CI pairing

## Summary

Added end-to-end capstone smoke tests for `crm` and `empty-crm` refresh flows, a Program 2 bootstrap path matrix (A–D), negative-fixture documentation, gate↔CI pairing in the Program 2 manual gate doc, and example-tree hygiene notes. Fixed `test_network_create` full-test expectations for intentional MVR category merge on seed bootstrap.

## New smoke tests

| Test | Gate / purpose |
|------|----------------|
| `test_crm_refresh_capstone_seed_specialist_storage` | Check 0, 7 |
| `test_empty_crm_refresh_capstone_create_on_deliver_storage` | empty-crm capstone |
| `test_matrix_a_crm_refresh_seed_bootstrap_storage` | Check 0b (crm side) |
| `test_matrix_b_empty_crm_refresh_create_on_deliver_bind` | Check 0b (empty side) |
| `test_matrix_c_crm_road_runner_create_on_deliver` | Check 4 |
| `test_matrix_d_crm_road_runner_no_duplicate_bind_version` | Check 6 |

Shared helpers live in `tests/test_example_network_capstones.py` (`apply_refreshed_root`, `run_create_on_deliver`, etc.). Matrix tests import from that module.

## Docs / hygiene

- `prompts/cursor/WORKFLOW.md` — negative-fixture rule + Grok full-suite note
- `docs/manual-checks/2026-06-13-program2-post-program-gate.md` — **Automated:** lines for checks 0, 0b, 1, 4, 6, 7
- `tests/network_helpers.py` — docstrings note seed-bootstrap vs create-on-deliver paths
- `examples/networks/crm/README.md` — do not commit runtime artifacts
- `.gitignore` — `examples/networks/**/deliveries.json`
- `tests/test_example_network.py` — layout test comment

## Full suite fix

`test_create_network_query_uses_custom_ontology_not_crm_fallback` — assert custom `telemetry`/`maintenance` categories remain; allow Program 2 MVR merge of `demographic`/`professional` only.

## Verification

```bash
./bin/ci-local
# CI local: all steps passed.
# 389 passed, 26 deselected

LANGCHAIN_TRACING_V2=false uv run pytest -m full -q
# 18 passed, 397 deselected
```

## For Grok + Paul

- **Gate pairing** — required manual checks 0, 0b, 1, 4, 6, 7 now cite smoke tests in gate doc; checks 2, 3, 5, 8–10 remain manual.
- **Regression guard** — empty-crm capstone uses refresh → query (no `ensure_categories_for_mvr_bind` in fixture); crm capstone asserts 15 `seed_bootstrap` specialist records after refresh only.
- **Full suite green** — 18 full tests pass after network_create expectation update.
- **Not committed** — awaiting review.

Suggested commit message:

```
test: add example network capstones and Program 2 gate pairing

End-to-end refresh+query smoke for crm and empty-crm; path matrix A–D;
document negative-fixture rule; pair gate checks with automated tests;
fix network_create MVR merge expectations.
```
