# Entity key suggestions — protocol slice 1

## Summary

Implemented **entity key suggestions** for near-miss lookups: `Andrea Kalman` → suggests `Andrea Kalmans` with `outcome=entity_key_unresolved`, empty `results`, no specialist invoke. Never silent fuzzy resolve.

## Changes

| File | Change |
|------|--------|
| `src/models/state.py` | `EntityKeySuggestion`, `QueryResponse.outcome` + `suggestions`; graph state fields |
| `src/agents/entity_resolution.py` | `resolve_entity_key()`, normalization, `SequenceMatcher` scoring |
| `src/agents/supervisor.py` | Resolver integration; short-circuit on `suggest` |
| `src/agents/responses.py` | `response_entity_unresolved()`; `outcome` on all builders |
| `src/agents/dispatch.py` | Assemble branch for suggestions |
| `src/network/introspection.py` | `policy.entity_key_unresolved` + MCP instructions |
| `src/mycelium_mcp/server.py` | `query_entity` docstring |
| `examples/networks/crm/guide.md` | One-line agent note |
| `tests/test_entity_key_suggestions.py` | 6 smoke tests |

## Locked behavior

- Threshold `0.85`, max 5 suggestions, first-token guard, `sequence_ratio` reason
- UUID miss → no suggestions
- Kevin Zhang → multiple exact (unchanged)
- Confirmation: re-query with `suggestions[].entity_key` only

## Verification

```bash
uv run pytest tests/test_entity_key_suggestions.py -m smoke -q   # 6 passed
uv run pytest -m smoke -q                                        # 165 passed (2 env flakes)
uv run ruff check src tests                                      # clean on touched files
```

**Manual:** `uv run mycelium query --entity-key "Andrea Kalman" --attributes email` on CRM network → `entity_key_unresolved` with Kalmans suggestion.

## For Grok + Paul

- Mark **Entity key suggestions (Slice 1)** done in `TODO.md`.
- Queue **Slice 2** (`1100-entity-outcome-infrastructure`) when ready.
- No spec deviations. `entity_unknown` intentionally deferred to Slice 3.
