# specialist-research-capstone (slice 1400 niggles) — Output

## Claim

Moved `prompts/cursor/next/2026-06-04-1400-specialist-research-polish-minor-fixes.md` → `prompts/cursor/in-progress/2026-06-09-1400-specialist-research-capstone/prompt.md`.

**Note:** An earlier polish pass landed in `prompts/cursor/done/2026-06-09-1400-specialist-research-polish-minor-fixes/`. This capstone slice closes the expanded 1–12 checklist from the re-queued prompt.

**Depends on:** 1100, 1200, 1300 (present).

## Fix map (1–12)

| # | Item | Status | Tests / notes |
|---|------|--------|----------------|
| 1 | Omitted LLM fields → `pending` | Already in `research.py` (`_persist_proposal`) | `test_persist_proposal_missing_field_marks_pending` |
| 2 | Pre-mark `pending` before research | Template | `test_contact_pre_marks_pending_before_research_runs` |
| 3 | Retry `pending` + `last_error` | Template + env | `test_contact_retries_pending_with_last_error` |
| 4 | `mixed` messaging | Template | `test_contact_mixed_found_and_na_message` |
| 5 | `_run_field_research` returns `ResearchRunResult` | Template | Used for audit (fix 6) |
| 6 | Audit line format | **Updated** `research id=… fields=… updated=… tool_calls=… errors=…` | `test_contact_retries_pending_with_last_error` |
| 7 | `financial` in `categories.json` | Already present | `test_load_category_metadata_financial` |
| 8 | Timeout + null-proposal smoke | Already in `test_research.py` | `test_run_field_research_timeout_marks_pending`, `test_run_field_research_null_proposal_marks_all_pending` |
| 9 | Integration `na` same response | **Added** | `test_run_query_email_na_in_same_response_when_research_mocked` |
| 10 | Stable integration assertions | **Added** `_assert_single_person_assembled` helper; dropped brittle `outcome='assembled'` substring | All three integration tests |
| 11 | Plan status line | **Added** under `docs/plans/specialist-research-phase1.md` Status | — |
| 12 | Regenerate six specialists | Ran `regenerate_specialists_from_registry()` | No threading/Tavily in specialists |

### Delta this session

- Template audit format + `ResearchRunResult.fields_updated` / `tool_calls_count` in audit line
- Env alias `MYCELIUM_RESEARCH_RETRY_PENDING_MIN_AGE_SEC` (falls back to `MYCELIUM_RESEARCH_RETRY_PENDING_SEC`)
- Integration: N/A test + `_assert_single_person_assembled` helper
- Plan doc one-line status

### Deferred (documented only)

- `tools.research` → `agents.specialists.base` import coupling (intentional; no cycle)
- `MYCELIUM_RESEARCH_VERBOSE_DEBUG` (out of scope)
- Renaming done-folder dates (`2026-06-09` vs `2026-06-04`)

## Verification

```
$ uv run pytest -m smoke -q tests/test_research.py tests/test_specialist_sync_research.py tests/test_specialist_research_integration.py
19 passed

$ uv run pytest -m smoke -q
50 passed, 11 deselected

$ uv run ruff check src/tools/research.py src/agents/factory src/agents/specialists tests/
All checks passed!
```

## Phase 1 queue

**Complete.** `prompts/cursor/next/` is empty.
