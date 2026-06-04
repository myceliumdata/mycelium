# specialist-research-runner (slice 1100) — Output

## Claim

Moved `prompts/cursor/next/2026-06-04-1100-specialist-research-runner.md` → `prompts/cursor/in-progress/2026-06-09-1100-specialist-research-runner/prompt.md` before implementation.

## Summary

Implemented the category-agnostic **sync Phase 1** research runner in `src/tools/research.py`:

- **Models:** `FieldProposal`, `ResearchProposal`, `ResearchRunResult`
- **Config:** `MYCELIUM_RESEARCH_MIN_CONFIDENCE` (0.6), `MYCELIUM_RESEARCH_MAX_TOOL_ROUNDS` (3), `MYCELIUM_RESEARCH_TIMEOUT_SEC` (120), optional `MYCELIUM_RESEARCH_MODEL`
- **Availability:** `is_research_available()` requires `OPENAI_API_KEY` and `TAVILY_API_KEY`
- **Prompts:** Jinja `research/_system.j2` + per-category fragments (`contact`, `social`, `relationships`, `demographic`, `professional`, `financial`); category text from `data/categories.json` via `load_category_metadata()`
- **Public API:** `run_field_research(category, specialist_name, person_id, target_fields, context, storage)` — full `context` in user prompt; writes only `target_fields`
- **Validation:** low confidence / weak evidence → `status: "na"` + `reason`; strong evidence → `found` (non-empty value, confidence ≥ threshold, ≥1 source URL); out-of-scope fields rejected
- **Failure:** API/LLM/timeout → `pending` + `last_error` on target fields (no fake `found`)
- **Persist:** `records[person_id][field]`; research audit entries appended under storage `meta["research_audit"]`
- **Tools:** `create_tavily_search_tool()` only (no direct `TavilySearch` outside `tavily.py`)

**Out of scope (unchanged):** specialist templates, generated `*_specialist.py`, graph/supervisor/MCP. Slice **1200** wires `run_field_research` into specialists.

## LLM loop decision

1. `ChatOpenAI` bound with Tavily tool; loop up to `MAX_TOOL_ROUNDS` — invoke → execute tool calls → append `ToolMessage`s until no tool calls or cap.
2. Final pass: append a `HumanMessage` asking for the structured proposal, then **`llm.with_structured_output(ResearchProposal).invoke(messages)`** (no tools on this invoke).

Overall run bounded with `ThreadPoolExecutor` + `MYCELIUM_RESEARCH_TIMEOUT_SEC`.

## Parameter naming

API uses `person_id` (UUID string) as the storage key into `records[person_id]`, matching the 1100 prompt contract. Public graph/results use canonical `id` from slice 1300; 1200 will pass the same UUID when calling the runner.

## Verification

### Smoke

```
$ uv run pytest -m smoke -q tests/test_research.py tests/test_web_search.py
...........                                                              [100%]
11 passed in 0.55s
```

### Ruff

```
$ uv run ruff check src/tools tests/test_research.py
All checks passed!
```

### TavilySearch isolation

```
$ rg TavilySearch src/
src/tools/tavily.py  (only)
```

## Tests (`tests/test_research.py`, all smoke, mocked)

- `load_category_metadata` for `contact`
- Low confidence → `na` + `reason`
- Good proposal → `found` with sources
- Rejects fields outside `target_fields`
- `is_research_available()` false without keys
- Unavailable run → `pending` + error, no `found`
- Mocked `_run_llm_loop` → persist `found` on `tmp_path` storage

## Files touched (slice scope)

| Path | Action |
|------|--------|
| `src/tools/research.py` | New |
| `src/tools/__init__.py` | Exports |
| `src/agents/factory/templates/research/**` | New Jinja |
| `tests/test_research.py` | New |
| `.env.example` | `MYCELIUM_RESEARCH_*` comments |

**Note:** Working tree may also contain unrelated doc edits (`docs/plans/specialist-research-phase1.md`, `prompts/resets/...`) from planning — not required for this slice.

## Next queue item

`2026-06-04-1200-specialist-template-sync-research.md` — wire `run_field_research` into specialist agent template (replace stub background research).
