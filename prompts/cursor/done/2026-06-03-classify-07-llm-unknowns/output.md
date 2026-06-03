# classify-07-llm-unknowns — Output

## Claim

Moved `prompts/cursor/next/2026-06-03-classify-07-llm-unknowns.md` → `in-progress/.../prompt.md` at start; delivered to `done/2026-06-03-classify-07-llm-unknowns/`.

## Summary

Extended `CategoryTree.classify()` so **first-time unknown** attributes invoke the LLM (lazy `ChatOpenAI`, shared prompt with `refresh_from_llm`), apply conservative merge (confidence ≥ 0.7, category ≠ `unknown`), persist via `_save`, and return a real `ClassificationResult`. Garbage / low-confidence / LLM-declared `unknown` are cached in `attribute_map` as the `unknown` sentinel so later calls are fast lookups with confidence 0.0. **Known attributes unchanged** (pure map lookup, 0.95 confidence, no LLM).

### Code changes

| File | Change |
|------|--------|
| `src/agents/classification/engine.py` | `_build_llm_classification_prompt`, `_llm_propose_for_attributes`, `_apply_proposal`, `_cache_as_unknown`, `_unknown_result`; `classify()` unknown branch; `refresh_from_llm` reuses shared helpers/prompt |
| `tests/test_supervisor_routing.py` | Mock LLM for existing tests; +3 smoke tests (known no LLM, garbage cached, sensible unknown cached) |
| `docs/architecture.md` | One paragraph updated for on-demand unknown LLM + caching |

No changes to supervisor, core_data, state, graphs, MCP.

## Verification

### Smoke

```
$ uv run pytest -m smoke -q
....................                                                     [100%]
20 passed, 9 deselected in 0.24s
```

### Ruff

```
$ uv run ruff check src/agents/classification tests/test_supervisor_routing.py
All checks passed!
```

### Manual classify (isolated tmp cache)

```
email: contact 0.95
foo_bar_baz: unknown
```

### CLI

`query --person-key "Nichanan Kesonpat" --attributes foo_bar_baz` → `category': 'unknown'` in debug (no taxonomy pollution).

### Hot-path callers

`grep` on supervisor, core_data, graphs, mcp, main: **no** `ChatOpenAI` / `_llm_propose` (LLM stays in `classification/engine.py` only).

## Success criteria

| Requirement | Met |
|-------------|-----|
| Known attrs: no LLM, same 0.95 behavior | Yes |
| Garbage → unknown, not mapped to real category | Yes (prompt + `_apply_proposal` rejects `unknown` cat) |
| Sensible unknown → classified + cached | Yes (`test_classify_sensible_unknown_llm_then_cached`) |
| Second call for same attr: no LLM | Yes (`llm_calls == 1` tests) |
| LLM lazy import | Yes (inside `_llm_propose_for_attributes`) |
| Tests mocked, no API key required | Yes |
| Public API unchanged | Yes |

## Notes

- If LLM invoke fails (no API key, network), `classify()` returns unknown **without** caching (exception path).
- `refresh_from_llm` early-return and mock-merge tests still pass (shared `_apply_proposal` / prompt).
