# Output — Research gate (Phase 6, slice `1500`)

## Summary

Formalized a single research gate: specialists/Tavily run only when `current_id` is set and the entity is a seed match (pre-validated) or a registry row with `validation_state == validated`. Provisional + requested attributes → `found` with identity-only `results` and the locked gate message (no `research_gated` outcome). Same-turn bind → validate → research unchanged from Slice 5.

## Changes

| File | Change |
|------|--------|
| `src/agents/research_gate.py` | **New** — `research_gate_allows()`, `is_research_gated()`, `RESEARCH_GATE_MESSAGE` |
| `src/agents/supervisor.py` | Uses `research_gate_allows`; removed `_research_allowed()` |
| `src/agents/dispatch.py` | Gate in `validate_entity_node` (post-promotion), `invoke_specialists_node` (defense), `assemble_response_node`; duplicate-bind message respects validated state |
| `src/agents/responses.py` | `response_research_gated()`; removed unused `response_registry_provisional_identity()` |
| `src/models/state.py` | Removed dead `registry_provisional_only` field |
| `src/network/introspection.py` | `policy.research_gate`; fixed `entity_bind` policy text |
| `tests/test_entity_research_gate.py` | **New** — 6 smoke + 1 unit test (spec matrix) |

## Gate rule

```
current_id set
AND (seed match OR registry validation_state == validated)
```

**Gate message:** *"Record is provisionally bound; core validation must complete before researching requested attributes."*

## Tests

```bash
uv run pytest tests/test_entity_research_gate.py -m smoke -q   # 6 passed
uv run pytest -m smoke -q                                      # 205 passed
```

| Test | Expectation |
|------|-------------|
| Validated Murphy + email | `assembled` (specialist path) |
| Provisional Murphy + email, validation fail | `found`, no invoke |
| Provisional Murphy + email, same-turn pass | `assembled` |
| Seed Andrea Kalmans + email | `assembled` |
| Kalman unresolved + email | `entity_key_unresolved`, no invoke |

## For Grok + Paul

- Mark **Slice 6 (`1500`)** done in `TODO.md` when reviewed.
- Slice 7 (`1600`) entity boundary cleanup is next in queue.
- P8/P9 dead-code cleanup from Slice 5 review included here (`registry_provisional_only`, `response_registry_provisional_identity`).

## Exit criteria

- [x] Single gate enforced in supervisor, validate, invoke, assemble
- [x] Provisional + attrs → `found` + gate message, identity-only results
- [x] No `research_gated` outcome
- [x] Same-turn validate + research when validation passes
- [x] Seed path unchanged
- [x] Smoke green (205)
