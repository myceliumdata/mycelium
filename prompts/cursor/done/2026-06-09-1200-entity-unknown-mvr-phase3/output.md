# Output — Unknown entity + MVR policy (Phase 3, slice `1200`)

## Summary

Per-network **MVR** policy from `network.json`; **`entity_unknown`** + **`required_fields`** on unknown entities; supervisor short-circuit before classification/specialists. No persistence, no `binding`.

## Changes

| File | Change |
|------|--------|
| `src/network/mvr.py` | **New** — `MvrPolicy`, `load_mvr()` with CRM default fallback |
| `src/agents/entity_resolution.py` | `unknown` resolution kind (no match, no suggestions, non-UUID) |
| `src/agents/supervisor.py` | Short-circuit on `unknown` — no classify, no specialists |
| `src/agents/dispatch.py` | `assemble_response` → `response_entity_unknown()` |
| `src/agents/responses.py` | `response_entity_unknown()` with MVR-driven message + `required_fields` |
| `src/models/state.py` | `QueryResponse.required_fields`; outcome docs include `entity_unknown` |
| `src/network/introspection.py` | `policy.mvr`, `policy.entity_unknown`; outcome list updated |
| `src/mycelium_mcp/server.py` | Docstring + schema description for `required_fields` |
| `examples/networks/crm/network.json` | Committed `mvr` block |
| `tests/test_entity_unknown_mvr.py` | **New** — 9 smoke tests (Paul Murphy, Kalman, Aaron Holiday, etc.) |
| `tests/test_entity_key_suggestions.py` | `NoSuchPerson` → `entity_unknown`; network root isolation |
| `tests/test_core_graph.py`, `test_query_messages.py` | Unknown-entity expectations + MVR env |
| `tests/test_query_response_outcomes.py` | `response_entity_unknown` builder + schema `required_fields` |

## Resolution order (after slice 3)

1. Exact seed match → existing flow  
2. Near-miss → `entity_key_unresolved` (slice 1)  
3. No match, no suggestions → `entity_unknown` + `required_fields`  
4. Empty / invalid UUID → `not_found`

## Example — Paul Murphy + email

```json
{
  "outcome": "entity_unknown",
  "required_fields": ["employer"],
  "results": [],
  "suggestions": [],
  "message": "No record for 'Paul Murphy'. To research email, provide employer (who they work for). ..."
}
```

## Tests

```bash
uv run pytest tests/test_entity_unknown_mvr.py -m smoke -q   # 9 passed
uv run pytest -m smoke -q                                     # 184 passed
```

## For Grok + Paul

- Mark **Slice 3 (`1200`)** done in `TODO.md` when reviewed.
- **`entity_under_specified`** and **`EntityQuery.binding`** remain Slice 4.
- Admin UI outcome badges for `entity_unknown` / `required_fields` still deferred per `admin-ui-backlog.md`.
- Queue **Slice 4 (`1300` entity-registry-bind)** when ready.

## Exit criteria

- [x] MVR in `examples/networks/crm/network.json`
- [x] `entity_unknown` short-circuit (no classify/specialists)
- [x] `required_fields` on `QueryResponse`
- [x] MCP/describe_network policy exposes MVR + entity_unknown
- [x] Smoke matrix from spec passes
