# Team alias expansion — prompt fix (canonical values, no mashup aliases)

> **READY** — Claim per `prompts/cursor/WORKFLOW.md` (move to `in-progress/` before starting).

**Priority:** Fix production bug where lazy LLM alias expansion persisted bogus `field_aliases` (e.g. `Washington Red Sox` → both `Cleveland Red Sox` and `Washington Nationals`). Paul is refreshing the live baseball root to clear polluted aliases; this slice prevents re-pollution.

**Parent:** Slice `2026-06-17-2000-baseball-closed-identity-lazy-aliases`; hand-test follow-up June 2026.

**Principles (Paul + Grok, locked):**

- **Prompt/policy fix only** — no MVR/manifest changes, no Lahman bootstrap changes, no word-count or string-length gates (those would block real nicknames like `The Miracle Mets`, `The Big Red Machine`).
- **Closed-world aliases** — expansion answers a historical question: “Is this query a real nickname/shorthand for existing catalog row(s)?” Mashups and nonexistent combos return empty.
- **Framework owns identity** — LLM returns **canonical bind field strings** from the registry list; the framework maps strings → entity ids. LLM must never choose or invent entity uuids.
- **Official Lahman labels** — team bind values are full canonical `Teams.name` strings (e.g. `Boston Red Sox`, `Brooklyn Dodgers`). There is no separate `city` field on team MVR.

---

## Problem (posterity)

**Repro (live root before refresh):**

1. Query `{"lookup": {"team": "Washington Red Sox"}}` — 0-hit on field index, fuzzy below threshold.
2. `bootstrap_only` path calls `expand_field_aliases` → LLM structured output returns entity ids.
3. LLM invents a mashup mapping; framework writes `field_aliases.team: ["Washington Red Sox"]` on unrelated rows (`Cleveland Red Sox`, `Washington Nationals`).
4. Subsequent queries exact-match both → spurious 2-match step-2.

**Root cause:** `_build_alias_expansion_prompt()` in `bind_alias_expansion.py` asks the model to return entity ids and includes ids in the canonical list. The model can hallucinate ids or split city/team fragments across unrelated entities.

**Correct outcomes:**

| Query | Expected |
|-------|----------|
| `Washington Red Sox` | `not_found`; **no** alias written |
| `Boston Red Sox` | Exact resolve on canonical bind value; expander **not** called |
| `Dodgers` | Multi-match (Brooklyn + LA) after expansion |
| `Bronx Bombers` | Single match (Yankees) after expansion |
| `The Miracle Mets` | Single match (New York Mets) when mock/LLM maps nickname → canonical name |

---

## Locked scope

| # | Decision |
|---|----------|
| A1 | **Rewrite alias prompt** — frame as historical nickname/shorthand resolution against the provided canonical value list only. Explicit negatives: do not invent teams; do not split unrelated fragments (e.g. `Washington` + `Red Sox`); mashups/nonexistent combos → empty list. |
| A2 | **Remove entity ids from prompt** — canonical list shows bind field values only (e.g. `- team='Boston Red Sox'`), not `id=...`. Model must not see or return uuids. |
| A3 | **Structured output** — replace `_FieldAliasProposal.entity_ids` with canonical bind values, e.g. `canonical_values: list[str]` (field name flexible; document in `output.md`). |
| A4 | **Framework mapping** — in `expand_field_aliases` (or `_llm_expand_field_aliases` then shared helper): for each returned canonical string, `registry.lookup_by_bind_values({field: canonical})`; collect unique entity ids; drop strings with no catalog hit. Empty list → no `add_field_alias` writes. |
| A5 | **`AliasExpander` contract** — injectable expander returns **canonical bind field values** (same shape as LLM); `expand_field_aliases` maps values → ids for both paths. Update test mocks in `test_closed_identity_lazy_aliases.py` and `test_strict_record_type_routing.py`. |
| A6 | **`guide.md` bullet** — full team labels must match Lahman exactly; bogus multi-word strings that are not real nicknames → `not_found`; real nicknames resolve via lazy expansion. |
| A7 | **Tests** — mock-only (no live OpenAI in CI); extend fixtures as needed. |

**Out of scope (do not implement):**

- Word-count / token-length / “looks like full name” pre-gates before LLM call
- MVR or `network.json` schema changes
- `lahman_seed.py` or bootstrap alias seeding
- `TODO.md`, manual gate timing docs, MCP health_check
- Player-grain prompt redesign beyond keeping generic `{field}` wording in the prompt builder

---

## Read first

- `prompts/cursor/WORKFLOW.md`
- `docs/architecture.md` (read-only context)
- `TODO.md` (read-only context — do not edit)
- `src/agents/bind_alias_expansion.py` — `_build_alias_expansion_prompt`, `_llm_expand_field_aliases`, `expand_field_aliases`, `AliasExpander`
- `src/agents/target_resolve.py` — `_try_bootstrap_only_alias_expansion`, `_resolve_bootstrap_only_zero_hit` (wire unchanged; behavior changes via expansion module)
- `examples/networks/baseball/guide.md`
- `tests/test_closed_identity_lazy_aliases.py`
- `tests/test_strict_record_type_routing.py` — `_mock_team_alias_expander`
- `prompts/cursor/done/2026-06-17-2000-baseball-closed-identity-lazy-aliases/` — original lazy-alias slice

---

## Implement

### 1. Prompt rewrite (`_build_alias_expansion_prompt`)

Suggested framing (adapt wording; keep intent):

- Task: determine whether `query_value` is a **real** nickname, shorthand, or historical label for one or more rows in the canonical list.
- Return **exact** canonical `{field}` strings from the list (character-for-character match to a listed value).
- If the query is a mashup, typo-combo, or not a recognized nickname → return `[]`.
- Examples in prompt (illustrative): `Dodgers` → `Brooklyn Dodgers` + `Los Angeles Dodgers`; `Bronx Bombers` → `New York Yankees`; `The Miracle Mets` → `New York Mets`; `Washington Red Sox` → `[]`.
- Include `guide.md` and record-type description as today.

### 2. Structured output + LLM path

- Pydantic model with `canonical_values: list[str]` (default `[]`).
- `_llm_expand_field_aliases` parses structured output, then maps via registry (A4). Do not pass through raw LLM strings as entity ids.

### 3. Shared mapping in `expand_field_aliases`

Add helper, e.g. `_canonical_values_to_entity_ids(registry, field_key, canonical_values) -> list[str]`:

- Normalize/strip each value.
- `lookup_by_bind_values({field_key: value})` per value.
- Deduplicate ids; skip unknown values silently.
- Existing alias-write loop unchanged after ids resolved.

### 4. Injectable expander

- Update `AliasExpander` type annotation/docstring: returns canonical bind values, not entity ids.
- When `expander=` is provided, run through the same mapping helper as the LLM path.

### 5. `guide.md`

Add one bullet under existing identity section:

- Queries using **full official team names** must match Lahman labels exactly (`Boston Red Sox`, not `Red Sox` alone unless aliased).
- Strings that are not real nicknames and do not match catalog values → `not_found` (expansion returns empty).
- Known nicknames/shorthands may resolve via lazy field aliases on first 0-hit lookup.

### 6. Tests (smoke; mock injection only)

Update `_mock_team_alias_expander` in both test files to return **canonical team strings**:

```python
if query_value == "Bronx Bombers":
    return ["New York Yankees"]
if query_value == "Dodgers":
    return ["Brooklyn Dodgers", "Los Angeles Dodgers"]
if query_value == "The Miracle Mets":
    return ["New York Mets"]
return []
```

| Test | Assert |
|------|--------|
| `Washington Red Sox` mashup | Extend `_prepare_baseball_team_registry` with `Cleveland Red Sox` + `Washington Nationals` rows. Query with mock expander returning `[]`. `kind == "not_found"`; neither row has `Washington Red Sox` in `field_aliases`. |
| `Boston Red Sox` exact | Add `Boston Red Sox` entity to fixture. `resolve_target_step1` without custom expander → `resolved`, one id. Use expander that `pytest.fail`s if called to prove expansion skipped on exact hit. |
| Existing Bronx / Dodgers / XYZZY | Still pass after mock contract change. |
| Optional `The Miracle Mets` | Add `New York Mets` to fixture; mock returns canonical name → single `resolved`. |

Mark new/changed tests `@pytest.mark.smoke`. No `@pytest.mark.full` unless you add real-storage integration (not required).

---

## Scope boundaries (strict)

**May modify:**

- `src/agents/bind_alias_expansion.py`
- `examples/networks/baseball/guide.md`
- `tests/test_closed_identity_lazy_aliases.py`
- `tests/test_strict_record_type_routing.py` (mock expander only — no unrelated routing changes)

**Do not modify:**

- `src/agents/target_resolve.py` (unless a one-line import/type tweak is strictly required — prefer zero changes)
- `examples/networks/baseball/network.json`, MVR templates, bootstrap handlers
- `TODO.md`
- `docs/manual-checks/*` (Paul/Grok hand-test docs)
- Any other files

If you believe `target_resolve.py` must change beyond a type import, **stop** and document why in `output.md` without making the change.

---

## Exit criteria

| # | Criterion |
|---|-----------|
| E1 | Prompt asks for canonical bind values only; canonical list in prompt has no entity ids |
| E2 | LLM structured output uses canonical values; framework maps to entity ids |
| E3 | `Washington Red Sox` → `not_found`, no alias pollution (mock test) |
| E4 | `Boston Red Sox` exact resolve without calling expander |
| E5 | `Dodgers` / `Bronx Bombers` behavior unchanged (multi/single match via mock) |
| E6 | `guide.md` updated per A6 |
| E7 | `./bin/ci-local` green |
| E8 | `output.md` documents prompt shape, mapping helper, mock contract, and Paul hand-retest note (`Washington Red Sox` after DB refresh) |

---

## Governance (mandatory)

- **Do not edit `TODO.md`.** Roadmap updates are for Grok + Paul after review.
- In `output.md`, add **"For Grok + Paul"**: hand-retest `Washington Red Sox` on refreshed root; note any slice-3 / player-alias follow-ups.
- Cursor delivers: code, tests, task-scoped docs, and `output.md` only.

## When finished (mandatory — see WORKFLOW.md §3)

1. `./bin/ci-local` green
2. `prompts/cursor/done/2026-06-18-1900-team-alias-expansion-prompt-fix/` with `prompt.md` + `output.md`
3. Remove claimed file from `in-progress/` **and** ensure no duplicate remains in `next/`
4. **Do not commit or push** — tell Paul "slice ready for review"

**Suggested commit message:**

```
fix(aliases): LLM returns canonical bind values, not entity ids

Rewrite team nickname expansion prompt to reject mashups; map canonical
strings to registry ids in framework. Prevents Washington Red Sox-style
alias pollution on bootstrap_only teams.
```