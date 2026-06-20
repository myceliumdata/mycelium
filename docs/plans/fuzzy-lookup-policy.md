# Fuzzy lookup policy (bind fields → any field)

**Status:** Composite bind-field scorer **shipped** (slice `2100`). Alias nicknames without token overlap remain on lazy LLM expansion.
**Owners:** Grok + Paul.

## For operators — what to expect on step 1

All of this lives in the **framework** (`entity_resolution.py`, `target_resolve.py`) — same behavior on CRM, baseball, and any network. Networks differ only by manifest bind fields and whether lazy **LLM** nicknames run (see below).

**Resolve order** (each lookup key on a 0-hit):

1. **Exact** — field index, bind values, existing `field_aliases`
2. **Fuzzy** — typos and shorthand with token overlap → `lookup_suggested` (nothing written to the registry)
3. **LLM alias expansion** — only on `bootstrap_only` record types (baseball team/player today), only if fuzzy found nothing → may write `field_aliases`, then **resolved** on retry
4. **Otherwise** — `lookup_incomplete` (CRM partial), `create_pending` (CRM full), or `not_found` (baseball)

| You typed | Typical outcome | Registry change? | You should |
|-----------|-----------------|------------------|------------|
| Typo (`Tie Cobb`, `654 Ventures`) | `lookup_suggested` | No | Retry step 1 with `suggestions[0].suggested_lookup` |
| Prefix (`645` for `645 Ventures`) | `lookup_suggested` | No | Same |
| Nickname, no token overlap (`Dodgers`) | `lookup_resolved` (multi-match) on baseball | Yes — `field_aliases` added | Use canonical name next time if you want exact hit without LLM |
| Exact canonical (`Ty Cobb`, `645 Ventures`) | `lookup_resolved` | No | Proceed to step 2 |
| Unknown (`XYZZY`) | `not_found` (baseball) or `lookup_incomplete` / `create_pending` (CRM) | No | Fix lookup or confirm create (CRM) |

**Suggestions are not matches.** Merge `suggestions[].suggested_lookup` into your retry `lookup` (or use `suggestions[].id`). Attribute data is not authoritative until step 1 resolves exactly.

**Status / inspect** (`network status`, admin entity drill-down): exact match only — no fuzzy suggestions.

Detail: [`docs/onboarding.md`](../onboarding.md) § Step-1 negotiation; baseball: [`examples/networks/baseball/guide.md`](../../examples/networks/baseball/guide.md) (LLM nickname table).

## Scope today (MVR v1)

- Step-1 `lookup` searches **MVR bind fields only** (CRM: `name`, `employer`; baseball: `player`, `debut_team`, `debut_year`, `team`) via exact per-field indexes.
- **Fuzzy suggestions** (`lookup_suggested`, `SUGGESTION_MIN_SCORE = 0.85`) apply when exact index lookup returns 0 hits — partial/full paths for any bind field via `_rank_bind_field_fuzzy_suggestions` and shared `fuzzy_bind_field_similarity()`. All fuzzy bind-field hits use `reason: fuzzy_bind_field_match`. Employer typos suggest the **corrected bind string** in `suggested_lookup` (e.g. `{"employer": "645 Ventures"}`); **do not** auto-resolve to all employees. Full-MVR bind-field conflicts use `same_bind_field_conflict`.

## Composite scorer (slice 2100)

Signals (take **max** of passing rules, threshold **0.85** unless OR-rule fixes score):

| Signal | Description |
|--------|-------------|
| `sequence_ratio` | `difflib.SequenceMatcher.ratio()` on normalized strings |
| `normalized_levenshtein` | `1 - lev(a,b) / max(len(a), len(b), 1)` |
| `token_average` | Same token count ≥ 1: mean per-token `SequenceMatcher.ratio()` |

**OR — last-token anchor (first-name typos):** both sides ≥ 2 tokens, last tokens equal, full-string Levenshtein ≤ 2 → include (e.g. `Tie Cobb` → `Ty Cobb`).

**OR — first-token prefix shorthand:** query is one token, candidate ≥ 2 tokens, first tokens equal → score **0.88** (e.g. `645` → `645 Ventures`, `ibm` → `IBM Corporation`).

**Hard rejects:** e.g. `John Cobb` → `Ty Cobb` (last name match but lev > 2); zero first-token overlap nicknames (`Dodgers` → Brooklyn Dodgers) — those stay on **lazy LLM alias expansion**, not fuzzy.

Normalization: strip, lower, collapse whitespace, drop `'` / `-` (via `normalize_field_index_value`).

## Examples

| Query | Candidate | Outcome @ 0.85 |
|-------|-----------|----------------|
| `andrea kalman` | `andrea kalmans` | ✅ typo (sequence) |
| `654 ventures` | `645 ventures` | ✅ digit typo |
| `645 venture` | `645 ventures` | ✅ plural typo |
| `645` | `645 ventures` | ✅ prefix shorthand (0.88) |
| `tie cobb` | `ty cobb` | ✅ last-token anchor |
| `john cobb` | `ty cobb` | ❌ homonym last name |
| `dodgers` | `brooklyn dodgers` | ❌ fuzzy (use alias LLM) |

## Slices

| Slice | Field | Status |
|-------|-------|--------|
| `1430` | `name` (partial 0-hit) | **Approved** |
| `1435` | `employer` (partial 0-hit) | **Approved** |
| `1440` | employer suggestion shape | **Approved** |
| `1450` | `suggested_lookup` rename | **Approved** |
| `2100` | composite scorer + prefix + last-token anchor | **Shipped** |

**Retry contract:** On `lookup_suggested`, merge `suggestions[].suggested_lookup` into step-1 `lookup` (or use `suggestions[].id` for one known row).

## Follow-ups

- Phonetic / Soundex (optional; not slice 2100)
- Indexed fuzzy pre-filter for large player registries (~24k scan today)
- Nicknames without token overlap (`Dodgers`, `Bronx Bombers`) — lazy LLM alias expansion

## References

- [`src/agents/entity_resolution.py`](../../src/agents/entity_resolution.py) — `fuzzy_bind_field_similarity`, `SUGGESTION_MIN_SCORE`
- [`src/agents/target_resolve.py`](../../src/agents/target_resolve.py) — partial vs full MVR branch
- [`TODO.md`](../../TODO.md) — Search indices; Query / search any field
