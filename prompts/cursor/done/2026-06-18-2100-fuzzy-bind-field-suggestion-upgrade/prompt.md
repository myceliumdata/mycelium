# Fuzzy bind-field suggestions — composite scorer upgrade

> **READY** — Claim per `prompts/cursor/WORKFLOW.md` (move to `in-progress/` before starting).

**Parent:** Paul hand-test June 2026 — `{"lookup": {"player": "Tie Cobb"}}` → `not_found`; should → `lookup_suggested` with `{"player": "Ty Cobb"}`. [`TODO.md`](../../../TODO.md) **Improving fuzzy matching**.

**Paul (locked, June 2026):** Suggestions only — caller confirms. **False positives OK** unless outlandish (e.g. wrong person same last name). **Prefix shorthand is in scope** — `645` must suggest `645 Ventures`. Do **not** auto-resolve. Prefer stdlib / small inline helpers — **no new dependencies** (no `rapidfuzz`, no Soundex library).

**Principles:**

- **Suggest, never resolve** — `lookup_suggested` + `suggested_lookup` retry contract unchanged.
- **Typos + shorthand** — fuzzy bind-field ranker handles **typos** (SequenceMatcher, edit distance, last-token anchor) and **first-token prefix shorthand** (`645` → `645 Ventures`, `ibm` → `IBM Corporation` when listed). **Nickname aliases** without token overlap (`Dodgers` → Brooklyn + LA teams, `Bronx Bombers`) stay on **lazy LLM alias expansion**.
- **Framework generic** — one shared scorer for all bind fields (`name`, `employer`, `player`, `team`, …).

---

## Problem (posterity)

Today (`entity_resolution.py`):

- Single signal: `difflib.SequenceMatcher.ratio()` on normalized full string.
- Threshold: `SUGGESTION_MIN_SCORE = 0.85`.
- CRM `name` path also requires **first-token equality** before scoring.

| Query | Candidate | SequenceMatcher | @ 0.85 |
|-------|-----------|-----------------|--------|
| `Tie Cobb` | `Ty Cobb` | **0.80** | ❌ |
| `Andrea Kalman` | `Andrea Kalmans` | 0.96 | ✅ |
| `645` | `645 Ventures` | 0.40 | ❌ today — **must suggest** (Paul) |
| `John Cobb` | `Ty Cobb` | 0.625 | ❌ (want keep) |

Full-string Levenshtein distance `tie cobb` → `ty cobb` is **2** (not 1). Normalized Levenshtein similarity = 0.75 — still below 0.85.

Routing is **not** the bug: partial `bootstrap_only` `{player}` runs `_rank_bind_field_fuzzy_suggestions` before alias expansion (`target_resolve.py`).

---

## Locked design — composite scorer

Replace per-candidate score with a shared helper, e.g. `_fuzzy_bind_field_similarity(query_norm: str, candidate_norm: str) -> float | None`:

- Return **`None`** = hard reject (do not suggest).
- Return **`float` in [0, 1]`** = similarity; include when `>= SUGGESTION_MIN_SCORE` (keep **0.85** unless tests prove Tie Cobb needs a named OR-rule below).

### Normalization (unchanged)

Reuse `normalize_name_for_comparison` / `normalize_field_index_value` rules (strip, lower, collapse whitespace, drop `'` / `-`).

### Similarity signals (take **max** of passing signals)

Implement small inline **Levenshtein** (no dependency). For each pair:

1. **`sequence_ratio`** — `SequenceMatcher.ratio()` (preserve CRM behavior).
2. **`normalized_levenshtein`** — `1 - lev(a,b) / max(len(a), len(b), 1)`.
3. **`token_average`** — when query and candidate have the **same token count** ≥ 1: mean of per-token `SequenceMatcher.ratio()`.

### OR-rule — last-token anchor (typo in first name)

When **both** have ≥ 2 tokens **and** **last tokens match exactly**:

- Include if **full-string** `lev(query_norm, candidate_norm) <= 2`.

Catches `Tie Cobb` → `Ty Cobb` (lev=2). Rejects `John Cobb` → `Ty Cobb` (lev=4).

Do **not** apply this rule when token counts differ (pair with first-token prefix rule below for shorthand).

### OR-rule — first-token prefix shorthand

When query is **exactly one token**, candidate has **≥ 2 tokens**, and `candidate_tokens[0] == query_tokens[0]` (normalized):

- Include with score **`0.88`** (fixed; passes `SUGGESTION_MIN_SCORE`; ranks below typo near-misses at ~0.96).

Catches `645` → `645 Ventures`, `ibm` → `IBM Corporation` (when canonical values exist in registry). Suggests the **full canonical bind string** in `suggested_lookup` (e.g. `{"employer": "645 Ventures"}`) — **not** all employees at that employer (retry contract unchanged).

**Distinct from alias expansion:** no token overlap nicknames (`Dodgers`, `Yanks`) remain LLM alias path only.

### Hard rejects

Return `None` only for clearly outlandish pairs (document in `output.md`), e.g.:

- Multi-token query where **no** signal passes and last-token / prefix rules do not apply.
- Do **not** add a blanket reject for single-token vs multi-token pairs (old `645` policy is **reversed**).

### CRM `name` path — drop first-token gate

`_rank_name_suggestions` must **not** skip candidates on first-token mismatch. Use the shared scorer instead (last-token anchor handles first-name typos; full-string lev + hard rejects limit noise).

### Suggestion `reason` field

Use a single reason string for composite matches, e.g. **`fuzzy_bind_field_match`**. Update `models/state.py` docstring / any reason lists if needed. Keep reporting **max signal** in tests only if helpful (optional `score` float on suggestion — already exists).

---

## Files

| File | Change |
|------|--------|
| `src/agents/entity_resolution.py` | Composite scorer; wire into `_rank_name_suggestions` + `_rank_bind_field_fuzzy_suggestions` |
| `tests/test_target_step1_lookup_clarity.py` | Update `reason` assertions if changed; keep Andrea Kalman / employer tests green |
| `tests/test_fuzzy_bind_field_suggestion_matrix.py` | **Pre-written mistake matrix (Grok)** — green **all** parametrized rows; extend, do not delete |
| `docs/plans/fuzzy-lookup-policy.md` | Add `Tie Cobb` + `645` rows; document composite signals, last-token anchor, first-token prefix; **reverse** old `645` negative |

**Do not modify:** `target_resolve.py` (unless import-only), alias expansion, bootstrap, `TODO.md`.

---

## Tests (smoke)

| Test | Assert |
|------|--------|
| `Tie Cobb` partial player | Registry with `Ty Cobb` (+ debut binds); `resolve_target_step1({"player":"Tie Cobb"})` → `lookup_suggested`, `suggested_lookup={"player":"Ty Cobb"}` |
| Andrea Kalman CRM | Still `lookup_suggested` (regression) |
| `645` employer partial | `{"employer":"645"}` → `lookup_suggested`, `suggested_lookup={"employer":"645 Ventures"}` — **flip** `test_partial_employer_shorthand_still_incomplete` |
| `John Cobb` vs `Ty Cobb` | **No** suggestion (homonym last name) |
| `645` vs `645 Ventures` scorer | Score ≥ 0.85 (prefix rule) |
| Matrix file | 15 scorer pairs + 6 CRM + 9 baseball step-1 rows — **E7: all green** |

Mark `@pytest.mark.smoke`. Matrix is the acceptance table; document row tweaks in `output.md`.

---

## Exit criteria

| # | Criterion |
|---|-----------|
| E1 | `Tie Cobb` → `lookup_suggested` → `Ty Cobb` |
| E2 | CRM fuzzy tests still pass |
| E3 | `645` → `645 Ventures` suggested; `Dodgers`-style zero-token-overlap nicknames still **not** fuzzy (alias path only) |
| E4 | `John Cobb` / `Ty Cobb` not suggested |
| E5 | `fuzzy-lookup-policy.md` updated |
| E6 | `./bin/ci-local` green |
| E7 | `tests/test_fuzzy_bind_field_suggestion_matrix.py` fully green |

---

## Explicit non-goals

- Soundex / phonetic libraries (optional future; not this slice)
- Auto-resolve on high score
- LLM alias expansion changes
- Indexed fuzzy (performance pre-filter) — note in `output.md` if 24k player scan is a follow-up

---

## Governance (mandatory)

- **Do not edit `TODO.md`.**
- **For Grok + Paul** in `output.md`: mark fuzzy matching item done; note any follow-up (phonetic, index).

## When finished (mandatory — see WORKFLOW.md §3)

1. `./bin/ci-local` green
2. `prompts/cursor/done/2026-06-18-2100-fuzzy-bind-field-suggestion-upgrade/` with `prompt.md` + `output.md`
3. Remove claimed file from `in-progress/`; no duplicate in `next/`
4. **Do not commit or push**

**Suggested commit message:**

```
feat(resolve): composite fuzzy bind-field suggestions

Multi-signal typo scoring with last-token anchor and first-token prefix
shorthand; Tie Cobb → Ty Cobb; 645 → 645 Ventures.
```