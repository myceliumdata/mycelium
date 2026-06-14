# Program 3 — Slice 1540: Legacy test migration and cleanup

## Summary

Migrated the entity_key-era test corpus to the target protocol (`lookup` / `id` / `delivery_id`). Removed conftest collection skips and legacy env flag machinery.

## Deleted modules (coverage merged elsewhere)

| File | Reason |
|------|--------|
| `tests/test_entity_key_suggestions.py` | Fuzzy/suggest/incomplete covered by `test_target_step1_lookup_clarity.py` + `test_mvr_target_resolve.py` |
| `tests/test_supervisor_routing.py` | `agents.routing` removed in 1530; supervisor deliver path covered by target deliver tests |

## Migrated modules (22 files)

All remaining legacy modules rewritten to target step-1/step-2 flows:

- `test_entity_unknown_mvr.py` — MVR unit tests kept; e2e → `lookup_incomplete` / `lookup_suggested`
- `test_entity_validation.py`, `test_entity_registry_bind.py`, `test_entity_research_gate.py`, `test_entity_growth.py`
- `test_entity_metering.py`, `test_query_messages.py`, `test_query_provenance.py`, `test_network_integration.py`
- `test_core_graph.py`, `test_agent_factory.py`, specialist integration tests, `test_entity_boundary.py`
- `test_network_create.py`, `test_trace_capture.py`
- `test_query_response_outcomes.py` — target response builders only

## New helpers

`tests/registry_helpers.py` extended with:

- `step1_resolve`, `step2_deliver`, `resolve_and_deliver`

## conftest.py

- Removed `_LEGACY_ENTITY_KEY_TEST_MODULES`, `pytest_ignore_collect`, `pytest_collection_modifyitems`
- No `MYCELIUM_ALLOW_LEGACY_ENTITY_KEY` (removed in 1530; confirmed absent from tests)

## Grep hygiene

- `EntityQuery(entity_key=…)` in tests: **only** intentional rejection tests with `# type: ignore[call-arg]` in `test_mvr_entity_query_models.py` and `test_mvr_polish_m10.py`
- `MYCELIUM_ALLOW_LEGACY_ENTITY_KEY` remains only in docs / historical `prompts/cursor/done/` (slice **1550** will scrub docs)

## Test counts

| Metric | Before (1530 skip) | After |
|--------|-------------------|-------|
| Smoke CI | 288 passed | **400 passed**, 26 deselected |
| Collected (all marks) | ~301 | **426 collected** |

## Verification

```bash
./bin/ci-local
# CI local: all steps passed.
# 400 passed, 26 deselected
```

## For Grok + Paul

- Docs still mention legacy env flag (`docs/architecture.md`, etc.) — **1550** scope.
- **Committed** after Grok review (see `review.md`).

Suggested commit message:

```
test: migrate suite to target protocol; remove legacy entity_key tests
```
