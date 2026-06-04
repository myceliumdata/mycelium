# Review — 2026-06-09-1300-specialist-research-integration (slice 1300)

**Reviewer:** Grok (on behalf of Paul)  
**Depends on:** 1100 + 1200 (implementation in working tree; not yet committed as of this review)  
**Artifacts:** `prompt.md`, `output.md`, uncommitted `tests/test_specialist_research_integration.py`, `docs/architecture.md`, `README.md`

**Overall:** **Approved** — Phase 1 integration slice complete. Proceed to **1400** (polish minor fixes) when ready.

---

## Plan / prompt alignment

| Requirement | Verdict |
|-------------|---------|
| Integration test: single `run_query` → `found` in same response (mocked) | Yes — `test_run_query_email_returns_found_in_same_response_when_research_mocked` |
| Contact + `email` path through full graph | Yes — seed `Test User`, `requested_attributes=["email"]` |
| Honest `message` when value returned | Yes — asserts no “not currently available” / “may be in the future” |
| Attribute-scoped `results` with `id` + `email` | Yes |
| Keys missing → pending, no crash | Yes — `test_run_query_email_pending_when_research_unavailable_no_crash` |
| `architecture.md` updated (sync implemented, async deferred, plan link) | Yes |
| `README.md` latency note | Yes |
| Smoke only, mocked, no live API | Yes — both tests `@pytest.mark.smoke` |
| Scope: no graph/MCP/research feature changes | Yes — tests + docs only per output |

---

## Strengths

- Exercises **real** `run_query` / graph / `assemble_response`, not only isolated specialist node (1200 tests).
- `research_integration_env` mirrors `test_core_graph` isolation (tmp DB, seed, registry, specialist dirs, categories copy).
- Mocks at `tools.research` boundary — consistent with unit tests.
- Asserts `person_id` passed to research matches `results[0]["id"]` (UUID alignment).
- Doc updates match approved plan language (sync Phase 1, Tavily, async deferred).

---

## Minor notes (non-blocking)

1. **No `na` integration path:** Only `found` (mocked) and `pending` (unavailable keys) are covered. Optional smoke: mock research writing `na` + `reason` → `results` omit attribute or show N/A messaging per merge rules.

2. **`output.md` typo:** “slice **1400** filter public results” should be **1400 polish minor fixes** (`prompts/cursor/next/2026-06-04-1400-specialist-research-polish-minor-fixes.md`).

3. **Brittle debug assertions:** Tests require substrings `outcome='assembled'` and `contributions=1` in `response.debug` — fine if stable; consider asserting on parsed debug or outcome tags if debug format changes.

4. **Commit stack:** Prompt artifacts are on `origin/main` (`e702aa9`); **implementation** (1100–1300 code + tests + docs) remains uncommitted locally — commit as one feature commit before or after 1400 per Paul’s preference.

5. **No `review.md` in repo until this file** — closes WORKFLOW “pending review” gap for 1300.

---

## Verification (Grok re-run)

```
uv run pytest -m smoke -q tests/test_specialist_research_integration.py  → 2 passed
uv run pytest -m smoke -q                                                 → 42 passed, 11 deselected
uv run ruff check tests/test_specialist_research_integration.py           → passed
```

---

## Status

**Approved.** Next: `2026-06-04-1400-specialist-research-polish-minor-fixes.md` after Paul/Cursor choose to run it.