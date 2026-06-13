# MVR redesign — Slice M5 (step-2 deliver, metering off)

## Summary

Step-2 `delivery_id` loads `DeliveryScope` and returns registry `results[]` — `found` (identity-only) or `assembled` (bound attrs via existing specialist path). Legacy `entity_key` unchanged.

## Changes

| Area | Change |
|------|--------|
| **`src/agents/target_deliver.py`** | **New** — `load_delivery_scope()`, `delivery_scope_has_attributes()` |
| **`src/agents/dispatch.py`** | `target_resolve_node` handles delivery step; identity short-circuit or attrs → supervisor |
| **`src/agents/supervisor.py`** | Skip legacy resolve when delivery step + preloaded `matched_records` |
| **`src/models/state.py`** | `delivery_scope_attrs`, `delivery_scope_provenance`; `graph_requested_attributes()` / `graph_provenance_requested()` |
| **`src/agents/metering_gate.py`** | Use graph attr/provenance helpers (step-2 scope) |
| **`src/agents/research_gate.py`** | Use `graph_requested_attributes()` |
| **`src/agents/query_provenance.py`** | Optional provenance/attrs overrides for step-2 |
| **`src/agents/specialists/*.py`** + **jinja** | Specialists read attrs via `graph_requested_attributes(state)` |
| **`tests/test_mvr_target_deliver.py`** | **New** — 7 smoke tests (roundtrip, multi-match, attrs, expired, legacy) |
| **`docs/architecture.md`** | M5 deliver paragraph |

**Untouched:** metering `quote_id` gate on step 2 (M6), create-on-0 (M7).

## Metering (M5 choice)

`quote_id` on step-2 is **ignored** when metering is on/off. Quote/payment gate deferred to **M6**.

## Step-2 attrs binding

Public `EntityQuery` stays step-2 pure (`delivery_id` only). Bound `requested_attributes` / `provenance` flow via internal `delivery_scope_attrs` on graph state (avoids Pydantic step validation conflict).

## Verification

```bash
./bin/ci-local
# uv sync OK · admin-ui build OK · ruff OK · 330 smoke passed, 26 deselected
```

## For Grok + Paul

- **M5 complete** — step-2 deliver (metering off).
- **M6 unblocked** — metering `quote_required` / `quote_id` on step 1 and step 2.
- **TODO.md:** mark M5 done; queue M6 (`mvr-redesign-slice-m6`).
- **Not committed** — awaiting review.

Suggested commit message:

```
feat: step-2 delivery_id deliver path (MVR redesign M5)

Load DeliveryScope at graph entry; return found/assembled results;
bind step-1 attrs via delivery_scope_attrs on graph state.
```
