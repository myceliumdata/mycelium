# Review: 2026-06-14-1450-suggestion-suggested-lookup-rename

**Verdict: Approved**

## CI

| Step | Result |
|------|--------|
| `./bin/ci-local` (Grok, 2026-06-14) | **Pass** — 419 smoke passed, 26 deselected; ruff clean; admin-ui build ok |
| Cursor `output.md` claim | 419 passed — matches |

## Delivery

| Artifact | Present |
|----------|---------|
| `EntityKeySuggestion` → `LookupSuggestion` | ✅ (no remaining references in `src/` or `admin-ui/`) |
| `lookup_suggestion()` central builder | ✅ |
| All rankers + `same_name_different_employer` use `suggested_lookup` | ✅ |
| Messages + introspection policy updated | ✅ |
| Checkpoint allowlist → `LookupSuggestion` | ✅ |
| Admin `lookupFromSuggestion` merges `suggested_lookup` | ✅ |
| Employer public JSON omits `id`/`name` (1440 nit) | ✅ |
| Docs (architecture, fuzzy policy, CRM README, phase1 note) | ✅ |
| `prompt.md` / `output.md` | ✅ |

## Diff reviewed

- `src/models/state.py`
- `src/agents/entity_resolution.py`
- `src/agents/target_resolve.py`
- `src/agents/responses.py`
- `src/graphs/core.py`
- `src/network/introspection.py`
- `admin-ui/src/types.ts`, `mvr.ts`, `App.tsx`, `EntityDrilldown.tsx`
- `tests/test_target_step1_lookup_clarity.py`
- `tests/test_mvr_target_public.py`
- `tests/test_entity_key_suggestions.py`
- `tests/test_network_status.py`
- `tests/test_query_response_outcomes.py`
- `docs/architecture.md`, `docs/plans/fuzzy-lookup-policy.md`, `docs/plans/entity-key-suggestions-phase1.md`
- `examples/networks/crm/README.md`
- `prompt.md`, `output.md`

## Spec compliance

| Exit criterion | Pass |
|----------------|------|
| No `entity_key` on public `suggestions[]` | ✅ |
| Every suggestion path populates `suggested_lookup` | ✅ |
| Employer fuzzy `public_dict()` smoke: `id`/`name` absent | ✅ (`test_employer_fuzzy_suggested_lookup_shape` + `test_mcp_employer_fuzzy_public_json_omits_person_fields`) |
| Introspection + messages reference `suggested_lookup` | ✅ |
| Admin suggestion click uses `suggested_lookup` | ✅ |
| Legacy smokes green | ✅ |
| `./bin/ci-local` green | ✅ |

## Legacy / dual-path

| Check | Pass |
|-------|------|
| `entity_key_unresolved` suggestions use `suggested_lookup` | ✅ |
| Same-thread checkpoint serde (`LookupSuggestion` allowlist) | ✅ |
| Target protocol name/employer fuzzy unchanged semantically | ✅ |

## Tests

| Test | Coverage |
|------|----------|
| `test_public_json_suggestions_exclude_entity_key` | Name fuzzy public shape |
| `test_employer_fuzzy_suggested_lookup_shape` | Employer + `public_dict` id/name absent |
| `test_mcp_employer_fuzzy_public_json_omits_person_fields` | MCP path (1440 nit) |
| `test_name_fuzzy_suggested_lookup_shape` | Name may include `id`/`name` |
| `test_same_name_different_employer_suggested_lookup` | Full bind map |
| Legacy `test_entity_key_suggestions.py` | Updated |

## Design critique

**Strong:** `suggested_lookup` is the right abstraction — matches step-1 `lookup` retry contract and reads clearly for both name and employer typos. Central `lookup_suggestion()` prevents drift. Admin UI fix (merge map into bind fields, `formatSuggestedLookup` display, stable list keys without requiring `id`) completes the 1440 admin gap. Breaking change is clean — no alias.

**Note:** `lookup_suggestion()` normalizes bind keys to lowercase — consistent with field indexes; fine for CRM v1.

## Nits

None.

## For Paul

**Commit message:**

```
refactor(query): replace suggestions[].entity_key with suggested_lookup

Rename EntityKeySuggestion to LookupSuggestion; suggestion retry hints
use target-protocol lookup maps instead of retired entity_key vocabulary.
```

**Manual check (your original confusion point):**

```bash
MYCELIUM_NETWORK=crm uv run mycelium query --network crm \
  --lookup-json '{"employer":"645 Venture"}' --json
# suggestions[0].suggested_lookup == {"employer": "645 Ventures"}
# no entity_key, id, or name keys on employer suggestion
```

**Restart MCP** — agent consumers must pick up `suggested_lookup` (breaking vs `entity_key`).

**Next:** Program 2 manual gate when ready (`docs/manual-checks/2026-06-13-program2-post-program-gate.md`).

**Push:** Local only until you ask.