# Review: 2026-06-14-1440-employer-fuzzy-suggestion-shape

**Verdict: Approved + polish nits**

## CI

| Step | Result |
|------|--------|
| `./bin/ci-local` (Grok, 2026-06-14) | **Pass** — 414 smoke passed, 26 deselected; ruff clean; admin-ui build ok |
| Cursor `output.md` claim | 414 passed — matches |

## Delivery

| Artifact | Present |
|----------|---------|
| `_rank_employer_suggestions` — canonical employer, not person | ✅ |
| `employer_sequence_ratio` reason | ✅ |
| Employer-aware `_lookup_suggested_message` | ✅ |
| `EntityKeySuggestion` optional `id`/`name` | ✅ |
| Four employer tests (typo, plural, attrs, retry→resolved) | ✅ |
| `fuzzy-lookup-policy.md` + CRM README | ✅ |
| `prompt.md` / `output.md` | ✅ |

## Diff reviewed

- `src/agents/entity_resolution.py`
- `src/agents/responses.py`
- `src/models/state.py`
- `tests/test_target_step1_lookup_clarity.py`
- `docs/plans/fuzzy-lookup-policy.md`
- `examples/networks/crm/README.md`
- `prompts/cursor/HOLD.md`
- `prompt.md`, `output.md`

## Spec compliance

| Exit criterion | Pass |
|----------------|------|
| Employer typo → `lookup_suggested` with `645 Ventures` (not Aaron Holiday) | ✅ |
| `requested_attributes` do not change step-1 fuzzy outcome | ✅ |
| No auto-resolve on fuzzy employer hit | ✅ |
| Employer-aware message copy | ✅ |
| Shorthand `645` still `lookup_incomplete` | ✅ (CI) |
| Name fuzzy unchanged | ✅ (CI) |
| `./bin/ci-local` green | ✅ |

## Legacy / dual-path

| Check | Pass |
|-------|------|
| Name fuzzy still `sequence_ratio` + person-shaped suggestions | ✅ |
| Exact `645 Ventures` → `lookup_resolved` batch (3) | ✅ (`test_partial_fuzzy_employer_retry_then_resolved`) |
| Legacy `entity_key` graph tests | ✅ (CI) |

## Tests

| Test | Coverage |
|------|----------|
| `test_partial_fuzzy_employer_lookup_suggested` | Digit typo `654 Ventures` |
| `test_partial_fuzzy_employer_plural_typo_suggests_employer` | User repro `645 Venture` |
| `test_partial_fuzzy_employer_with_attrs_still_suggested` | Parity with Andrea Kalman + attrs |
| `test_partial_fuzzy_employer_retry_then_resolved` | Two-step suggest → resolve |
| Gap | No smoke asserting `public_dict()` omits `id`/`name` on employer suggestions (verified manually — see below) |

**Manual public JSON check (Grok):** `645 Venture` → `suggestions[0]` has `entity_key` + `employer` only; `id`/`name` absent; message employer-specific.

## Design critique

**Strong:** Correctly implements suggest-don't-resolve. Dedupes by normalized employer string and stores **canonical** registry spelling (not first-seen row). Distinct `employer_sequence_ratio` enables message routing. Optional `id`/`name` on the model is the right shape for employer-only hints.

**Sub-optimal (non-blocking, queued):**

- `suggestions[].entity_key` still reads like the retired query field when the value is an employer string — **slice 1450** (`suggested_lookup`) addresses this.
- Admin `lookupFromSuggestion` maps `entity_key` → `name` bind field; employer suggestions need `employer` from `reason` — **1450** + admin path in that slice.

## Nits

| Severity | Item |
|----------|------|
| Non-blocking | Add smoke test for employer suggestion `public_dict()` shape (no `id`/`name` keys). |
| Non-blocking | Update `fuzzy-lookup-policy.md` slice `1440` row status to **Approved** after commit. |
| Non-blocking | `HOLD.md` queue metadata in same diff as code — fine; keep queue state accurate. |

## For Paul

**Commit message:**

```
fix(query): employer fuzzy suggests corrected employer string

Align employer typo suggestions with name fuzzy: suggest the bind-field
value for retry, do not pick a representative person or auto-resolve.
```

**Manual repro (your original bug):**

```bash
MYCELIUM_NETWORK=crm uv run mycelium query --network crm \
  --lookup-json '{"employer":"645 Venture"}' \
  --attrs-json '["title","email"]'
# lookup_suggested; suggestions[0].employer == "645 Ventures"; no delivery

MYCELIUM_NETWORK=crm uv run mycelium query --network crm \
  --lookup-json '{"employer":"645 Ventures"}' \
  --attrs-json '["title","email"]'
# lookup_resolved; total_matches: 3
```

**Next:** Slice **1450** (`suggestions[].entity_key` → `suggested_lookup`) queued in `next/`. Restart MCP after 1440 + 1450 land for agent consumers.

**Push:** Local only until you ask.