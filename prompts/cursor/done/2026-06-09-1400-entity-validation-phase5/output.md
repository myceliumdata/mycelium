# Output — Core validation orchestration (Phase 5, slice `1400`)

## Summary

Rule-based MVR validation for provisional registry entities: demographic (name) + professional (employer) checks, registry promotion to `validated`, outcome **`entity_validated`**. Same graph turn: **bind → validate → research** when attrs requested and validation passes (aligned with Slice 6 gate).

## Changes

| File | Change |
|------|--------|
| `src/agents/entity_validation.py` | **New** — rule-based validators, `run_mvr_validation()` |
| `src/agents/entity_registry.py` | `promote_validated()` updates `validation_state` + `field_states` |
| `src/agents/dispatch.py` | **`validate_entity_node`**; assemble paths for validated / failed |
| `src/agents/responses.py` | `response_entity_validated`, `response_validation_failed` |
| `src/agents/supervisor.py` | Classify attrs on bind; defer specialists until validated; `_research_allowed()` |
| `src/graphs/core.py` | Graph: `supervisor → validate_entity → build_context \| assemble` |
| `src/models/state.py` | `validation_contributions`; outcome docs for `entity_validated` |
| `src/network/introspection.py` | `policy.entity_validated` |
| `tests/test_entity_validation.py` | **New** — 5 smoke tests |
| `tests/test_entity_registry_bind.py` | Updated for bind→validate same turn |

## Graph flow

```
START → supervisor → validate_entity → build_context → invoke_specialists → assemble
                              └──────────────────────────────→ assemble
```

## Outcomes

| Situation | `outcome` |
|-----------|-----------|
| Provisional + MVR pass, identity-only | `entity_validated` |
| Provisional + MVR pass + attrs | `assembled` (same turn) |
| Provisional + MVR fail | `found` + validation failure message (Q5b) |
| Already validated / seed | `found` / `assembled` |

## Tests

```bash
uv run pytest tests/test_entity_validation.py -m smoke -q   # 5 passed
uv run pytest -m smoke -q                                    # 199 passed
```

## For Grok + Paul

- Mark **Slice 5 (`1400`)** done in `TODO.md` when reviewed.
- Slice 6 (`1500`) can formalize the research gate (much of same-turn behavior already works).
- Admin UI validation badges deferred per `admin-ui-backlog.md`.

## Exit criteria

- [x] Rule-based validation (no Tavily/LLM)
- [x] Registry promotion on pass
- [x] `entity_validated` outcome
- [x] Bind → validate → assembled same turn with attrs
- [x] Seed path unchanged (no validation invoke)
- [x] Smoke green
