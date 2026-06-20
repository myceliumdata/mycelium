# Output — fuzzy bind-field suggestion upgrade

## Summary

Composite fuzzy bind-field scorer replaces single `SequenceMatcher.ratio()` gate. `{"player": "Tie Cobb"}` now yields `lookup_suggested` with `Ty Cobb`; `{"employer": "645"}` yields `645 Ventures` via first-token prefix shorthand. Suggestions only — no auto-resolve.

## Changes

| Area | Change |
|------|--------|
| `entity_resolution.py` | Inline Levenshtein; `_fuzzy_bind_field_similarity()` on normalized strings; public `fuzzy_bind_field_similarity()` normalizes inputs; OR-rules: last-token anchor (lev ≤ 2), first-token prefix (score 0.88); dropped CRM first-token gate on `_rank_name_suggestions`; unified reason `fuzzy_bind_field_match` |
| `models/state.py` | `LookupSuggestion.reason` docstring updated |
| `responses.py` | Accepts `fuzzy_bind_field_match` (+ legacy `bind_field_fuzzy_match`) |
| `docs/plans/fuzzy-lookup-policy.md` | Composite signals, Tie Cobb + 645 rows; reversed old 645 negative |
| `tests/test_fuzzy_bind_field_suggestions.py` | New unit + Tie Cobb integration |
| `tests/test_fuzzy_bind_field_suggestion_matrix.py` | Uses public scorer; baseball matrix clears `OPENAI_API_KEY` to avoid alias-expansion flake |
| `tests/test_target_step1_lookup_clarity.py` | `645` → `lookup_suggested`; reason updates |
| `bin/smoke-crm-e2e` | Reason assertion updated |

## Scorer API

```python
def _fuzzy_bind_field_similarity(query_norm: str, candidate_norm: str) -> float | None: ...

def fuzzy_bind_field_similarity(query: str, candidate: str) -> float | None:
    """Normalizes via normalize_field_index_value, then scores."""
```

Internal rankers call `_fuzzy_bind_field_similarity` on already-normalized values; matrix tests call `fuzzy_bind_field_similarity` with raw strings.

## Hard rejects (documented)

- Multi-token pairs where no signal passes and neither last-token anchor nor prefix rule applies (e.g. `John Cobb` vs `Ty Cobb`).
- Zero-token-overlap nicknames (`Dodgers`, `Bronx Bombers`) — alias expansion path only, not fuzzy.

## Verification

| Check | Result |
|-------|--------|
| `./bin/ci-local` | **552** smoke passed |

## For Grok + Paul

- **Hand-retest:** `{"player": "Tie Cobb"}` → `lookup_suggested` / `Ty Cobb`; `{"employer": "645"}` → `645 Ventures`; `{"team": "Red Sox"}` partial → `not_found` (no fuzzy on city-less fragment).
- Confirm Andrea Kalman / CRM fuzzy regressions still feel right.
- Mark **Improving fuzzy matching** done in `TODO.md` (Grok/Paul — Cursor did not edit `TODO.md`).
- **Follow-up:** indexed fuzzy pre-filter if 24k-player scan latency matters; optional phonetic layer (out of scope).
- No commit (per workflow).

**Suggested commit message:**

```
feat(resolve): composite fuzzy bind-field suggestions

Multi-signal typo scoring with last-token anchor and first-token prefix
shorthand; Tie Cobb → Ty Cobb; 645 → 645 Ventures.
```
