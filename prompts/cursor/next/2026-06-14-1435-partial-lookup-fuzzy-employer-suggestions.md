# Partial employer lookup: fuzzy suggestions before lookup_incomplete

> **READY** — Move to `in-progress/` before starting (see `prompts/cursor/WORKFLOW.md`).

**Context:** Slice `1430` adds name fuzzy on partial 0-hit lookups. Same gap exists for **`employer`**: `{"lookup": {"employer": "654 Ventures"}}` should suggest **645 Ventures** (digit typo), not jump to `lookup_incomplete`.

**Design policy:** [`docs/plans/fuzzy-lookup-policy.md`](../../docs/plans/fuzzy-lookup-policy.md) — fuzzy on **all bind fields** now; fuzzy on **any field** when that TODO ships.

**Prerequisite:** Slice `1430` approved (or landed on `main` with same `target_resolve` pattern).

**Out of scope:** Short aliases (`{"employer": "645"}` → 645 Ventures) — SequenceMatcher ~0.40; document limitation; separate alias/prefix design later.

---

## Read first

- [`docs/plans/fuzzy-lookup-policy.md`](../../docs/plans/fuzzy-lookup-policy.md)
- [`src/agents/entity_resolution.py`](../../src/agents/entity_resolution.py) — `_rank_suggestions` (name); add employer analogue
- [`src/agents/target_resolve.py`](../../src/agents/target_resolve.py) — partial 0-hit branch (post-`1430`)
- [`src/agents/field_index.py`](../../src/agents/field_index.py) — `normalize_field_index_value` (align employer normalization with index)
- [`tests/test_target_step1_lookup_clarity.py`](../../tests/test_target_step1_lookup_clarity.py)

---

## Required fix

### A. Employer fuzzy ranker

Add `_rank_employer_suggestions(employer: str) -> list[EntityKeySuggestion]` (or generalize to `_rank_bind_field_suggestions(field, value)` shared by name + employer — prefer **one helper** if it keeps normalization/score policy consistent).

- Compare query employer to **distinct** registry `employer` values (or per-entity rows — dedupe by normalized employer string).
- Use same `SUGGESTION_MIN_SCORE` / `SUGGESTION_MAX_COUNT` as name fuzzy unless tests prove otherwise.
- `reason`: `"sequence_ratio"` (or `"employer_sequence_ratio"` if you need to distinguish in tests).
- Suggestions should include `id`, `name`, `employer` on representative entity per matched employer string.

**Do not** apply name `_first_token` filter to employer matching.

### B. Wire into `resolve_target_step1`

When partial lookup has 0 exact hits and `not is_full_mvr_lookup`:

1. Keep existing **name** fuzzy pass (`1430`).
2. If lookup includes non-empty **`employer`** and name fuzzy did not fire (or no `name` key), run employer fuzzy ranker.
3. Suggestions → `lookup_suggested`; else → `lookup_incomplete` as today.

Order when **both** `name` and `employer` present with 0 AND hits: try name fuzzy first, then employer fuzzy (document in `output.md`).

### C. Tests (smoke — mandatory)

Add to `tests/test_target_step1_lookup_clarity.py`:

| Test | Assert |
|------|--------|
| **New:** `test_partial_fuzzy_employer_lookup_suggested` | `lookup={"employer": "654 Ventures"}` → `lookup_suggested`, suggestion employer **645 Ventures**, `sequence_ratio` |
| **New:** `test_partial_employer_shorthand_still_incomplete` | `lookup={"employer": "645"}` → `lookup_incomplete` (no suggestion — alias gap) |
| Existing `test_partial_fuzzy_name_lookup_suggested` | Still passes |
| Existing employer exact batch test if any | Unchanged |

### D. Docs

- One-line add to [`docs/plans/fuzzy-lookup-policy.md`](../../docs/plans/fuzzy-lookup-policy.md) slice table when done (status row only).
- Brief CRM README step-1 row for employer typo → `lookup_suggested` if listed.

---

## Verification

```bash
./bin/ci-local
```

**Manual:**

```bash
MYCELIUM_NETWORK=crm uv run mycelium query --network crm \
  --lookup-json '{"employer":"654 Ventures"}'
# lookup_suggested → 645 Ventures
```

---

## Governance

- Do not edit `TODO.md`.
- In `output.md` → **For Grok + Paul**: employer fuzzy done; shorthand alias still open.
- Do not commit or push.

## When finished

1. `./bin/ci-local` green
2. `prompts/cursor/done/2026-06-14-1435-partial-lookup-fuzzy-employer-suggestions/`
3. Remove from `in-progress/` and `next/`
4. Tell Paul **slice ready for review**

---

## Exit criteria

- Employer typo partial 0-hit → `lookup_suggested`
- Shorthand `645` still `lookup_incomplete`
- Name fuzzy (`1430`) unchanged
- `./bin/ci-local` green

Suggested commit message:

```
fix(query): suggest fuzzy employer matches on partial lookup 0-hit

Extend bind-field fuzzy suggestions to employer (sequence_ratio);
shorthand aliases remain lookup_incomplete until alias design.
```