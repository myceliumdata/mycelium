# MVR redesign — Slice M8 (batch deliver + batch provenance)

## Summary

Batch step-2 deliver now researches and assembles **all N** entities in a `DeliveryScope` (no silent truncation). Per-entity specialist invocation and contribution merge fix multi-match attrs delivery. When step-1 bound `provenance=true`, step-2 returns `provenance.entities[]` with one entry per delivered id. Create-on-deliver remains N=1.

## Changes

| Area | Change |
|------|--------|
| **`src/agents/dispatch.py`** | `_entity_ids_from_state`, `_context_for_entity`; `invoke_specialists_node` loops N entities |
| **`src/agents/responses.py`** | Per-entity `_specialist_value_for_attr` / `merge_requested_record` |
| **`src/agents/entity_growth.py`** | `apply_registry_research_attribution` filters contributions by entity id |
| **`docs/architecture.md`** | M8 batch deliver + `provenance.entities[]` paragraph |
| **`tests/test_mvr_batch_deliver.py`** | **New** — 3 smoke tests (batch attrs, batch provenance, metered roundtrip) |

**Untouched:** CLI/MCP migration (M9), polish (M10), `TODO.md`.

## Protocol behavior

| Scenario | Step-2 outcome |
|----------|----------------|
| N-match scope, no attrs | `found` with N identity rows (unchanged) |
| N-match scope + attrs | `assembled` with N rows, attrs merged per entity |
| N-match + attrs + step-1 `provenance` | `assembled` + `provenance.entities[]` (N entries) |
| `create_on_deliver` | N=1 only (M7 path unchanged) |

## Verification

```bash
./bin/ci-local
# uv sync OK · admin-ui build OK · ruff OK · 342 smoke passed, 26 deselected
```

## For Grok + Paul

- **M8 complete** — batch deliver + batch `provenance.entities[]` (R9).
- **M9 unblocked** — CLI, MCP, admin status, example JSON, README migration.
- **TODO.md:** mark M8 done; queue M9 (`mvr-redesign-slice-m9`).
- **Not committed** — awaiting review.

Suggested commit message:

```
feat: batch step-2 deliver and provenance for N entities (MVR redesign M8)

Invoke specialists per entity in multi-match delivery scopes; merge
contributions per row; attach provenance.entities[] for batch deliver.
```
