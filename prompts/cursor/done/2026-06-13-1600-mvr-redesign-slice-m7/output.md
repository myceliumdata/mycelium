# MVR redesign — Slice M7 (create-on-0 + retire name_source)

## Summary

Step-1 with **full MVR lookup**, **0 matches**, and **requested_attributes** now issues a `delivery_id` scoped for provisional create (`create_on_deliver=true`). Step-2 deliver calls `bind_provisional` from scope `lookup`, then runs validation → specialists. Partial lookup with 0 matches stays `not_found`. **`name_source`** removed from MVR policy, example `network.json` files, and tests; legacy `entity_key` path unchanged until M9.

## Changes

| Area | Change |
|------|--------|
| **`src/network/delivery.py`** | `DeliveryScope.create_on_deliver`; `issue_delivery(..., create_on_deliver=)` |
| **`src/network/mvr.py`** | `is_full_mvr_lookup`, `can_create_on_zero_matches`; `MvrPolicy` without `name_source` |
| **`src/network/quotes.py`** | `WorkloadSpec.create_on_deliver`; scope hash; batch count = 1 for create-pending |
| **`src/agents/target_resolve.py`** | `create_pending` step-1 kind; issue delivery with create intent |
| **`src/agents/target_deliver.py`** | `create_pending` load; `bind_provisional_from_scope`; `hydrate_matches_for_deliver` |
| **`src/agents/target_metering.py`** | Workload includes `create_on_deliver` |
| **`src/agents/dispatch.py`** | Step-1 create-pending path; step-2 create-on-deliver hydration |
| **`src/agents/responses.py`** | `response_assembled` / `build_query_message` use delivery-scope attrs on step-2 |
| **`src/models/state.py`** | `required_fields` description (no `name_source`) |
| **`examples/networks/*/network.json`** | Removed `name_source` from crm, crm-metering, empty-crm |
| **`docs/architecture.md`** | M7 create-on-deliver paragraph |
| **`tests/test_mvr_create_on_deliver.py`** | **New** — 4 smoke tests |
| **Tests (name_source cleanup)** | `test_entity_unknown_mvr`, `test_research`, `test_query_*`, `test_core_graph`, `test_network_integration` |

**Untouched:** batch provenance shape (M8), CLI/MCP migration (M9), `TODO.md`.

## Protocol behavior

| Condition | Step-1 | Step-2 |
|-----------|--------|--------|
| Partial lookup, 0 matches | `not_found` | — |
| Full MVR, 0 matches, no attrs | `not_found` | — |
| Full MVR, 0 matches, attrs | `lookup_resolved` (`total_matches=0`, `create_on_deliver` scope) | `bind_provisional` → `assembled` |
| Legacy `entity_key` | Supervisor path (unchanged) | — |

## Verification

```bash
./bin/ci-local
# uv sync OK · admin-ui build OK · ruff OK · 339 smoke passed, 26 deselected
```

## For Grok + Paul

- **M7 complete** — create-on-deliver for full MVR + attrs; `name_source` retired.
- **M8 unblocked** — batch provenance JSON shape on step-2 deliver.
- **TODO.md:** mark M7 done; queue M8 (`mvr-redesign-slice-m8`).
- **Legacy note:** `entity_key` / `entity_resolution` still active for CLI until M9.
- **Not committed** — awaiting review.

Suggested commit message:

```
feat: create-on-deliver for full MVR zero-match lookups (MVR redesign M7)

Step-1 issues create_on_deliver delivery scope; step-2 bind_provisional;
remove name_source from MVR policy and example networks.
```
