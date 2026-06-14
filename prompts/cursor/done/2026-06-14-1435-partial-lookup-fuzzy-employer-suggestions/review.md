# Review: 2026-06-14-1435-partial-lookup-fuzzy-employer-suggestions

**Verdict: Approved**

## CI

| Step | Result |
|------|--------|
| `./bin/ci-local` (Grok, 2026-06-14) | **Pass** — 411 smoke passed, 26 deselected; ruff clean; admin-ui build ok |
| Cursor `output.md` claim | 411 passed — matches |

## Delivery

| Artifact | Present |
|----------|---------|
| `_rank_employer_suggestions` with index-aligned normalization | ✅ |
| Partial 0-hit: name fuzzy then employer fuzzy | ✅ |
| `test_partial_fuzzy_employer_lookup_suggested` | ✅ |
| `test_partial_employer_shorthand_still_incomplete` | ✅ |
| `fuzzy-lookup-policy.md` / README / introspection updates | ✅ |
| `prompt.md` / `output.md` | ✅ |

## Diff reviewed

- `src/agents/entity_resolution.py`
- `src/agents/target_resolve.py`
- `tests/test_target_step1_lookup_clarity.py`
- `docs/plans/fuzzy-lookup-policy.md`
- `examples/networks/crm/README.md`
- `src/network/introspection.py`
- `prompt.md`, `output.md`

## Spec compliance

| Exit criterion | Pass |
|----------------|------|
| Employer typo partial 0-hit → `lookup_suggested` | ✅ |
| Shorthand `645` still `lookup_incomplete` | ✅ |
| Name fuzzy (`1430`) unchanged | ✅ (CI) |
| `./bin/ci-local` green | ✅ |

## Legacy / dual-path

| Check | Pass |
|-------|------|
| Exact partial employer hit → `lookup_resolved` (batch tests) | ✅ (CI) |
| Full MVR paths unchanged | ✅ (CI) |

## Tests

| Test | Coverage |
|------|----------|
| `test_partial_fuzzy_employer_lookup_suggested` | `654 Ventures` → `645 Ventures` |
| `test_partial_employer_shorthand_still_incomplete` | Alias gap documented |
| Gap | No test for partial lookup with both wrong name + wrong employer (name wins first — acceptable) |

## Design critique

**Strong:** Employer ranker dedupes by normalized employer string, uses `normalize_field_index_value` (same as exact index), shares score thresholds with name fuzzy, and wires cleanly after name pass in `target_resolve`. Shorthand limitation explicitly tested and documented.

**Note:** Suggestions use a representative entity per employer (`entity_key` = person name) — correct for retry via `suggestions[].id`; agents should read `employer` on each suggestion for employer-driven lookups.

## Nits

None.

## For Paul

**Commit message:**

```
fix(query): suggest fuzzy employer matches on partial lookup 0-hit

Extend bind-field fuzzy suggestions to employer (sequence_ratio);
shorthand aliases remain lookup_incomplete until alias design.
```

**Manual test:**

```bash
MYCELIUM_NETWORK=crm uv run mycelium query --network crm \
  --lookup-json '{"employer":"654 Ventures"}'
# lookup_suggested → 645 Ventures

MYCELIUM_NETWORK=crm uv run mycelium query --network crm \
  --lookup-json '{"employer":"645"}'
# lookup_incomplete (alias gap)
```

**Next:** Program 2 manual gate. Restart MCP for both `1430` + `1435` commits.

**Git:** Local commit only — no push until you ask.