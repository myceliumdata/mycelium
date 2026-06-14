# Employer fuzzy: suggest corrected employer string (parity with name fuzzy)

> **READY** — Move to `in-progress/` before starting (see `prompts/cursor/WORKFLOW.md`).

**Context:** Slice `1435` added employer fuzzy on partial 0-hit lookups. Typo detection works (`645 Venture` → `645 Ventures`, score 0.96) but the **suggestion shape is wrong**: it returns one arbitrary **person** (Aaron Holiday) instead of the corrected **employer string** (`645 Ventures`).

**Design principle (locked):** [`docs/plans/entity-key-suggestions-phase1.md`](../../docs/plans/entity-key-suggestions-phase1.md) — **suggest, don't resolve**. Same as name fuzzy: `Andrea Kalman` → `lookup_suggested` with `Andrea Kalmans`, whether or not `requested_attributes` are present. **Never** auto-complete the request as if we knew what the caller meant.

**Repro (CRM):**

```json
{"lookup": {"employer": "645 Venture"}, "requested_attributes": ["title", "email"]}
```

→ `lookup_suggested`, 1 suggestion with `entity_key: "Aaron Holiday"`. **Wrong.**

**Expected (parity with name fuzzy):**

```json
{"lookup": {"employer": "645 Venture"}}
```

→ `lookup_suggested`, `total_matches: 0`, `delivery: null`, suggestion points at **`645 Ventures`** (the corrected bind-field value). Caller retries:

```json
{"lookup": {"employer": "645 Ventures"}, "requested_attributes": ["title", "email"]}
```

→ **then** `lookup_resolved`, `total_matches: 3`, step-2 batch proceeds.

**Name analogue (already correct):**

```json
{"lookup": {"name": "Andrea Kalman"}, "requested_attributes": ["email"]}
```

→ `lookup_suggested`, `suggestions[0].entity_key == "Andrea Kalmans"`, no delivery, no research.

**Root cause:** `_rank_employer_suggestions` sets `entity_key=entity.name` (person) instead of the matched employer string. Message copy says *"Near-miss registry **names** found"* for employer path.

**Prerequisite:** Slices `1430` + `1435` approved on `main`.

**Out of scope:** Auto-resolve / batch-expand on fuzzy hit; shorthand aliases (`645` → 645 Ventures).

---

## Read first

- [`docs/plans/entity-key-suggestions-phase1.md`](../../docs/plans/entity-key-suggestions-phase1.md) — suggest, don't resolve
- [`docs/plans/fuzzy-lookup-policy.md`](../../docs/plans/fuzzy-lookup-policy.md)
- [`src/agents/entity_resolution.py`](../../src/agents/entity_resolution.py) — `_rank_suggestions` (name), `_rank_employer_suggestions`
- [`src/models/state.py`](../../src/models/state.py) — `EntityKeySuggestion`
- [`src/agents/responses.py`](../../src/agents/responses.py) — `_lookup_suggested_message`
- [`tests/test_target_step1_lookup_clarity.py`](../../tests/test_target_step1_lookup_clarity.py)

---

## Required fix

### A. Employer suggestion shape

Fix `_rank_employer_suggestions` so each suggestion represents the **corrected employer string**, not a person:

| Field | Employer fuzzy value |
|-------|---------------------|
| `entity_key` | Canonical registry employer string (e.g. `645 Ventures`) — retry key for lookup map |
| `employer` | Same canonical string |
| `name` | `null` or omit when suggestion is employer-level (prefer `null` if model allows; else empty string — document choice in `output.md`) |
| `id` | Optional: omit from `public_dict` when employer-only suggestion, **or** keep a representative id but document that retry is via **corrected lookup**, not `suggestions[].id` for batch employer search |
| `reason` | `employer_sequence_ratio` (new) or `sequence_ratio` — pick one and test consistently; prefer distinct reason so message routing is clear |
| `score` | Unchanged |

**Do not** return N person rows (one per employee). One distinct employer string → one suggestion, like one distinct name → one suggestion.

### B. Retry contract

Document in `output.md` (and one line in fuzzy policy doc):

> On employer `lookup_suggested`, retry with `lookup` map using `suggestions[0].entity_key` (or `.employer`) as the corrected `employer` value. Same `requested_attributes` / `delivery_id` flow as name fuzzy confirmation.

### C. Messaging

`_lookup_suggested_message`: when suggestions have `reason` of `employer_sequence_ratio` (or employer-only path), use employer copy:

> "Near-miss registry employer found. Retry with a corrected lookup map."

Not *"Near-miss registry names found"*.

### D. No auto-resolve

**Do not** expand fuzzy employer hit into `lookup_resolved` with all employees. That violates suggest-don't-resolve and breaks parity with Andrea Kalman.

---

## Tests (smoke — mandatory)

Update `tests/test_target_step1_lookup_clarity.py`:

| Test | Assert |
|------|--------|
| **Update:** `test_partial_fuzzy_employer_lookup_suggested` | `654 Ventures` → `lookup_suggested`, `suggestions[0].entity_key == "645 Ventures"` (not a person name), `total_matches == 0`, `delivery is None` |
| **New:** `test_partial_fuzzy_employer_plural_typo_suggests_employer` | `645 Venture` → `lookup_suggested`, `entity_key` / `employer` == `645 Ventures` |
| **New:** `test_partial_fuzzy_employer_with_attrs_still_suggested` | `645 Venture` + `requested_attributes=["title","email"]` → still `lookup_suggested`, no delivery, suggests `645 Ventures` |
| **New:** `test_partial_fuzzy_employer_retry_then_resolved` | Step 1 typo → suggested; step 2 `lookup={"employer":"645 Ventures"}` + same attrs → `lookup_resolved`, `total_matches == 3` |
| **Keep:** shorthand `645` → `lookup_incomplete` |
| **Keep:** name fuzzy tests unchanged |

---

## Docs

- [`docs/plans/fuzzy-lookup-policy.md`](../../docs/plans/fuzzy-lookup-policy.md): employer typo → `lookup_suggested` with corrected **employer string**; slice `1440` row; explicit **no auto-resolve**.
- CRM README one-liner if step-1 table exists.

---

## Verification

```bash
./bin/ci-local
```

**Manual:**

```bash
# Step 1 — suggest only
MYCELIUM_NETWORK=crm uv run mycelium query --network crm \
  --lookup-json '{"employer":"645 Venture"}' \
  --attrs-json '["title","email"]'
# lookup_suggested; suggestion employer 645 Ventures; no delivery

# Step 2 — caller confirms
MYCELIUM_NETWORK=crm uv run mycelium query --network crm \
  --lookup-json '{"employer":"645 Ventures"}' \
  --attrs-json '["title","email"]'
# lookup_resolved; total_matches: 3
```

---

## Governance

- Do not edit `TODO.md`.
- In `output.md` → **For Grok + Paul**: employer fuzzy suggestion shape fixed; shorthand alias still open.
- Do not commit or push.

## When finished

1. `./bin/ci-local` green
2. `prompts/cursor/done/2026-06-14-1440-employer-fuzzy-suggestion-shape/`
3. Remove from `in-progress/` and `next/`
4. Tell Paul **slice ready for review**

---

## Exit criteria

- Employer typo → `lookup_suggested` with **645 Ventures** as suggestion (not Aaron Holiday)
- `requested_attributes` do not change step-1 fuzzy outcome (parity with Andrea Kalman)
- No auto-resolve on fuzzy employer hit
- Employer-aware message copy
- `./bin/ci-local` green

Suggested commit message:

```
fix(query): employer fuzzy suggests corrected employer string

Align employer typo suggestions with name fuzzy: suggest the bind-field
value for retry, do not pick a representative person or auto-resolve.
```