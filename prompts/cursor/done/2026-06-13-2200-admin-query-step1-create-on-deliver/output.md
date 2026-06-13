# Admin query UX + step-1 `create_on_deliver` API field

## Summary

Step-1 responses now expose `delivery.create_on_deliver: true` only when step 2 will create a provisional entity (full MVR, 0 registry hits). Existing matches omit the field. `response_lookup_resolved` messages are operator/agent-friendly. Public JSON uses `exclude_none` (CLI, MCP, admin). Admin UI shows `(full MVR)` and terse deliver copy.

**No auto-deliver** — two explicit Run clicks unchanged.

## Example step-1 JSON

**Create-pending (Road Runner @ Acme):**

```json
{
  "outcome": "lookup_resolved",
  "total_matches": 0,
  "delivery": {
    "delivery_id": "d_…",
    "expires_at": "2026-06-13T…",
    "create_on_deliver": true
  },
  "results": [],
  "message": "No registry match. Full MVR lookup — step 2 will create a provisional entity, then deliver."
}
```

**Existing match (Nichanan Kesonpat):**

```json
{
  "outcome": "lookup_resolved",
  "total_matches": 1,
  "delivery": {
    "delivery_id": "d_…",
    "expires_at": "2026-06-13T…"
  },
  "results": [],
  "message": "1 registry match. Use delivery_id on step 2 to deliver."
}
```

Note: `create_on_deliver` is **absent** (not `false`) for existing matches.

## Changes

| Area | Change |
|------|--------|
| **`src/models/state.py`** | `DeliveryPayload.create_on_deliver`, `from_scope()`, `QueryResponse.public_dict()` / `public_json()` |
| **`src/agents/responses.py`** | Locked step-1 `message` strings in `response_lookup_resolved` |
| **`src/agents/target_resolve.py`**, **`target_metering.py`** | `DeliveryPayload.from_scope(scope)` |
| **`src/mycelium_admin/server.py`**, **`mycelium_mcp/server.py`**, **`main.py`** | `exclude_none` public serialization |
| **`src/network/introspection.py`** | Policy text mentions `delivery.create_on_deliver` |
| **`admin-ui/src/App.tsx`**, **`types.ts`** | `(full MVR)` suffix; `Run again to deliver.` |
| **Tests** | `test_mvr_create_on_deliver`, `test_mvr_target_resolve`, `test_admin_daemon`, `test_mvr_entity_query_models` |

## Verification

```bash
./bin/ci-local
cd admin-ui && npm run build
# uv sync OK · admin-ui build OK · ruff OK · 360 passed, 26 deselected
```

Auto-deliver: **absent** — `runQueryRequest` still requires explicit step-2 Run when `delivery_id` is pre-filled.

## For Grok + Paul

- **Slice complete** — admin two-step UX + `create_on_deliver` API field.
- **Hands-on:** Nichanan → `total_matches: 1`, no `(full MVR)`; Road Runner @ Acme → `0 (full MVR)`, `create_on_deliver` in JSON; lookup fields clear after step 1; terminal outcomes clear tokens.
- **Not committed** — awaiting review.

Suggested commit message:

```
feat: expose delivery.create_on_deliver on step-1 and polish admin query UX

Add create_on_deliver to DeliveryPayload (true only); update lookup_resolved
messages; omit field in public JSON for existing matches; admin UI (full MVR) copy.
```
