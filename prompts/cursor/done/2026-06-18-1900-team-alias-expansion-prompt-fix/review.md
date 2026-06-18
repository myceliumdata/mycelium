# Review — team alias expansion prompt fix

**Verdict:** Approved + polish nits

## CI

| Step | Result |
|------|--------|
| `uv sync --all-extras` | Pass |
| `admin-ui` build | Pass |
| `ruff` | Pass |
| smoke tests | **509 passed**, 98 deselected |

## Delivery

`output.md` matches disk: 4 implementation files changed; `target_resolve.py` untouched per scope.

## Diff reviewed

| File | Read |
|------|------|
| `src/agents/bind_alias_expansion.py` | Full |
| `examples/networks/baseball/guide.md` | Full |
| `tests/test_closed_identity_lazy_aliases.py` | Full |
| `tests/test_strict_record_type_routing.py` | Mock section |
| `prompts/cursor/done/.../output.md` | Full |

`/review` subagent: not used (small focused diff).

## Spec compliance

| # | Criterion | Result |
|---|-----------|--------|
| E1 | Prompt: canonical values only; no entity ids in list | Pass |
| E2 | Structured `canonical_values`; framework maps to ids | Pass |
| E3 | `Washington Red Sox` → `not_found`, no alias pollution | Pass |
| E4 | `Boston Red Sox` exact resolve; expander not called | Pass |
| E5 | `Dodgers` / `Bronx Bombers` unchanged | Pass |
| E6 | `guide.md` updated | Pass |
| E7 | `./bin/ci-local` green | Pass |
| E8 | `output.md` documents prompt + mapping + hand-retest | Pass |

## Legacy / dual-path

- CRM `create_pending` smoke unchanged.
- `target_resolve` wiring unchanged; behavior improved via expansion module only.
- Injectable `AliasExpander` contract updated consistently in both test files.

## Tests

New smoke coverage is strong: mashup guard, exact-hit expander skip (`pytest.fail` expander), multi-word nickname (`The Miracle Mets`). Mock returns canonical strings end-to-end through `_canonical_values_to_entity_ids`.

Gap (non-blocking): no unit test that LLM-returned values outside `allowed` set are dropped — defense is straightforward in `_llm_propose_canonical_values`; live behavior depends on prompt + filter.

## Design critique

**Strong**

- Correct split: LLM proposes canonical strings; registry owns identity mapping. Eliminates uuid hallucination class.
- Post-LLM `allowed` set filter is cheap, effective guard even if model drifts.
- Deduping canonical values in `_canonical_field_values` shrinks prompt noise (bonus, not scope creep).
- `Washington Red Sox` negative example baked into prompt aligns with the live bug.

**Sub-optimal (non-blocking)**

- `_build_alias_expansion_prompt` examples are team-specific (`Dodgers`, `Red Sox`) while the builder is generic for any bind field. Player-grain expansion will see irrelevant team examples until a follow-up parameterizes examples by record type or moves them to `guide.md`.

## Nits

| Severity | Item |
|----------|------|
| Polish | Parameterize prompt examples by `record_type` or drop inline examples and rely on `guide.md` for domain flavor. |
| Polish | Optional `Field(description=...)` on `_FieldAliasProposal.canonical_values` for clearer structured-output schema. |

Program polish backlog: entity-protocol post-8 doc if applicable — nits above are alias-module only; no MVR row needed.

## For Paul

- **Commit:** Grok committed locally after this review.
- **Hand-retest** (refreshed root): `{"lookup": {"team": "Washington Red Sox"}}` → `not_found`; re-run Q15 (`Dodgers`, `Bronx Bombers`) with `OPENAI_API_KEY` to confirm live LLM respects new prompt.
- **Push:** unchanged — Paul only, when ready.

**Suggested commit message** (used):

```
fix(aliases): LLM returns canonical bind values, not entity ids

Rewrite team nickname expansion prompt to reject mashups; map canonical
strings to registry ids in framework. Prevents Washington Red Sox-style
alias pollution on bootstrap_only teams.
```