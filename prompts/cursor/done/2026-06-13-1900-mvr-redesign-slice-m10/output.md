# MVR redesign — Slice M10 (polish + doc sync + admin-ui)

## Summary

Closed the M1–M9 polish backlog: admin-ui two-step migration, doc/fixture sync, missing target-path smoke tests, shared env util, metering accept helper, legacy `entity_key` isolation behind `MYCELIUM_ALLOW_LEGACY_ENTITY_KEY`, and batch message partitioning fix.

**Final MVR redesign slice** — program ready for push after review.

## Backlog closure

| ID | Status | Notes |
|----|--------|-------|
| P1 | Closed | `src/network/env_util.py`; `delivery.py`, `quotes.py`, `research.py` import `env_int` |
| P2 | Closed | `EntityQuery.id` description clarifies registry UUID |
| P3 | Waived | WORKFLOW §3 checklist already done (process) |
| P4 | Closed | `field_index._entity_field_value` generalized via `hasattr` |
| P5 | Waived | M4 `run_query`+seed tests kept; CI green |
| P6 | Waived | Specialist jinja regen documented in architecture (no code churn) |
| P7 | Closed | `test_step2_identity_only_deliver_with_provenance_scope` |
| P8 | Closed | TTL/orphan delivery note in `architecture.md` operator section |
| P9 | Waived | `response_quote_required` parity verified; no wrapper regression |
| P10 | Closed | `_target_metering_block_response` typed `EntityQuery` |
| P11 | Closed | `accept_quote_for_workload()` in `metering_gate.py`; used by target + legacy gate |
| P12 | Closed | `test_target_principal_required_on_metered_quote` |
| P13 | Closed | `test_provenance_only_step1_quote_required` |
| P14 | Closed | `bind_provisional_from_scope` reads MVR bind fields |
| P15 | Closed | `is_full_mvr_lookup` empty-value docstring |
| P16 | Closed | `test_metered_create_on_deliver_target_path` |
| P17 | Closed | `architecture.md` M7–M10 bullets + status shipped |
| P18 | Closed | `partition_attribute_buckets` per-entity / conservative batch |
| P19 | Closed | `test_batch_step2_identity_only_found` |
| P20 | Closed | Sequential N×M note in `architecture.md` |
| P21 | Closed | M8 batch line in architecture (merged with P17) |
| P22 | Closed | `admin-ui` lookup + `delivery_id` + quote accept flow |
| P23 | Closed | `crm-metering/README.md` step 2 = lookup + `--attributes` |
| P24 | Closed | Fixture placeholder text in `03-deliver-quote.json` + queries README |
| P25 | Closed | Supervisor legacy gate; pytest sets `MYCELIUM_ALLOW_LEGACY_ENTITY_KEY=1` |
| P26 | Waived | Lightweight health ping deferred (non-blocking) |

## Changes

| Area | Change |
|------|--------|
| **`admin-ui/src/App.tsx`**, **`api.ts`**, **`types.ts`** | Two-step query form: lookup name/employer, `delivery_id`, quote accept |
| **`src/network/env_util.py`** | Shared `env_int` |
| **`src/agents/metering_gate.py`** | `accept_quote_for_workload()` helper |
| **`src/agents/responses.py`** | Batch-safe `partition_attribute_buckets` |
| **`src/agents/supervisor.py`** | Legacy `entity_key` disabled without env flag |
| **`src/models/state.py`** | Legacy helpers + outcome doc pass |
| **`tests/test_mvr_polish_m10.py`** | **New** — 6 smoke tests |
| **`tests/conftest.py`** | Default `MYCELIUM_ALLOW_LEGACY_ENTITY_KEY=1` for legacy smoke |
| **`docs/architecture.md`** | Shipped status, M10 operator notes, legacy gate |
| **`examples/networks/crm-metering/`** | README + fixture placeholder fixes |

## Verification

```bash
./bin/ci-local
# uv sync OK · admin-ui build OK · ruff OK · 352 passed, 26 deselected
```

## For Grok + Paul

- **M10 complete** — polish backlog closed; **MVR redesign program done** (M1–M10).
- **TODO.md:** mark M10 + program complete; no further MVR slices queued.
- **Not committed** — awaiting review. Program push after Grok approval.

Suggested commit message:

```
feat: MVR redesign M10 polish — admin-ui two-step, backlog tests, legacy gate

Migrate admin-ui to lookup/delivery_id flow; close P1–P25 backlog; isolate
legacy entity_key behind MYCELIUM_ALLOW_LEGACY_ENTITY_KEY for smoke tests.
```
