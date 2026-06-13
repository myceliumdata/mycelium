# MVR redesign — Slice M4 (indexes + step-1 resolve)

## Summary

Per-field inverted indexes on registry MVR bind fields; graph `target_resolve` node wires step-1 `id` / `lookup` → `lookup_resolved` + `issue_delivery()`. Legacy `entity_key` path unchanged.

## Changes

| Area | Change |
|------|--------|
| **`src/agents/field_index.py`** | **New** — normalize, `build_field_indexes`, `intersect_lookup` (AND, exact match) |
| **`src/agents/entity_registry.py`** | Rebuild indexes on load/save; `lookup_by_target_lookup()`, `field_indexes()` |
| **`src/agents/target_resolve.py`** | **New** — `resolve_target_step1()`, `issue_target_delivery()` |
| **`src/agents/responses.py`** | `response_lookup_resolved()`; `response_not_found()` optional `message` |
| **`src/agents/dispatch.py`** | `target_resolve_node`; assemble passthrough when `response` preset |
| **`src/graphs/core.py`** | START → `target_resolve` → supervisor \| assemble_response |
| **`src/models/state.py`** | `entity_query_is_target_resolve_step()` helper |
| **`tests/test_mvr_target_resolve.py`** | **New** — 7 smoke tests (index AND, id/lookup resolve, legacy path) |
| **`docs/architecture.md`** | M4 dual-path status |

**Untouched:** step-2 deliver (M5), metering `quote_required` on step 1 (M6), `entity_resolution` legacy behavior.

## Metering (M4 choice)

When `metering.enabled`, step-1 target queries still return **`lookup_resolved`** (same as metering off). **`quote_required` on step 1** deferred to **M6** — target resolve short-circuits before `metering_gate`.

## Index normalization

Strip, lower-case, collapse whitespace, remove `'` / `-` / `'` (aligned with `bind_index` name rules). No fuzzy widening (R13).

## Verification

```bash
./bin/ci-local
# uv sync OK · admin-ui build OK · ruff OK · 323 smoke passed, 26 deselected
```

## For Grok + Paul

- **M4 complete** — indexes + step-1 target resolve wired.
- **M5 unblocked** — step-2 deliver via `delivery_id`.
- **TODO.md:** mark M4 done; queue M5 (`mvr-redesign-slice-m5`).
- **Not committed** — awaiting review.

Suggested commit message:

```
feat: per-field indexes and step-1 lookup_resolved (MVR redesign M4)

Add registry field indexes, target_resolve graph node, and delivery issuance
for id/lookup queries; legacy entity_key path unchanged.
```
