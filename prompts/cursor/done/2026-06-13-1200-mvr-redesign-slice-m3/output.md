# MVR redesign — Slice M3 (EntityQuery + outcomes)

## Summary

Target-protocol shapes are in `EntityQuery` / `QueryResponse` with step-1/step-2 Pydantic validation, MCP schema updates, and unit tests. **Graph runtime unchanged** — still resolves via legacy `entity_key` until M4.

## Changes

| Area | Change |
|------|--------|
| **`src/models/state.py`** | `DeliveryPayload`; `EntityQuery` gains `id`, `lookup`, `delivery_id`; `entity_key`/`binding` kept with defaults + deprecated descriptions; `@model_validator` for step rules; `entity_query_is_delivery_step()` helper |
| **`src/models/state.py`** | `QueryResponse` gains `total_matches`, `delivery`; outcome docs include **`lookup_resolved`** |
| **`src/mycelium_mcp/server.py`** | `_neutral_json_schema` — target field descriptions, legacy deprecation notes |
| **`src/main.py`** | `query` subcommand epilog documents target protocol; `--entity-key` help marks legacy |
| **`tests/test_mvr_entity_query_models.py`** | **New** — 15 smoke tests (step validation, serialization, MCP schema) |
| **`tests/test_query_response_outcomes.py`** | Assert `total_matches` / `delivery` / `lookup_resolved` in MCP schema |
| **`docs/architecture.md`** | M3 paragraph: models accept target fields; runtime still legacy until M4 |

**Untouched:** LangGraph resolve/deliver nodes, `entity_resolution`, `dispatch` behavior.

## Validation rules (locked)

- **Step 1:** `id` OR non-empty `lookup` OR `entity_key` (including whitespace-only legacy); optional `requested_attributes`, `provenance`, `principal`; no `delivery_id`.
- **Step 2:** `delivery_id` + optional `quote_id` only; rejects resolve fields, `requested_attributes`, `provenance`.

## Verification

```bash
./bin/ci-local
# uv sync OK · admin-ui build OK · ruff OK · 316 smoke passed, 26 deselected
```

## For Grok + Paul

- **M3 complete** — models + schema + tests; no graph wiring.
- **M4 unblocked** — per-field indexes, step-1 resolve → `lookup_resolved` + `issue_delivery()`.
- **TODO.md:** mark M3 done; queue M4 (`mvr-redesign-slice-m4`).
- **Not committed** — awaiting review.

Suggested commit message:

```
feat: MVR target EntityQuery/QueryResponse models (redesign M3)

Add id/lookup/delivery_id step validation, lookup_resolved outcome fields,
and MCP schema docs; legacy entity_key path unchanged until M4.
```
