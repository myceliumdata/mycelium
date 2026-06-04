# specialist-research-polish-minor-fixes (slice 1400) — Output

## Claim

Moved `prompts/cursor/next/2026-06-04-1400-specialist-research-polish-minor-fixes.md` → `prompts/cursor/in-progress/2026-06-09-1400-specialist-research-polish-minor-fixes/prompt.md`.

**Depends on:** slices **1100**, **1200**, **1300** (complete).

## Fix map (1–7)

| # | Change | Tests |
|---|--------|-------|
| 1 | `_persist_proposal`: omitted LLM fields → `pending` + `last_error`; post-pass for any still-unset allowed fields | `test_persist_proposal_missing_field_marks_pending` |
| 2 | Pre-mark `_mark_fields_pending` before `run_field_research` | `test_contact_pre_marks_pending_before_research_runs` |
| 3 | `_fields_needing_research` retries `pending` + `last_error`; env `MYCELIUM_RESEARCH_RETRY_PENDING` (default on) and `MYCELIUM_RESEARCH_RETRY_PENDING_SEC` | `test_contact_retries_pending_with_last_error` |
| 4 | `mixed` overall status → dedicated message (found + N/A, not all unavailable) | `test_contact_mixed_found_and_na_message` |
| 5 | `financial` category + `attribute_map` entries in `data/categories.json` | `test_load_category_metadata_financial` |
| 6 | Timeout + null-proposal smoke tests in `test_research.py` | `test_run_field_research_timeout_marks_pending`, `test_run_field_research_null_proposal_marks_all_pending` |
| 7 | Research audit line on specialist `audit_log` after research runs | covered by `test_contact_retries_pending_with_last_error` (`research completed` in audit) |

### Files

- `src/tools/research.py` — `_pending_record`, `_persist_proposal` completeness
- `src/agents/factory/templates/specialist_agent.py.j2` — retry, pre-mark, mixed messaging, audit line
- `src/agents/specialists/*_specialist.py` — regenerated (6)
- `data/categories.json`, `.env.example`, `tests/test_research.py`, `tests/test_specialist_sync_research.py`

Regen: `get_agent_factory().regenerate_specialists_from_registry()`

## Verification

```
$ uv run pytest -m smoke -q tests/test_research.py tests/test_specialist_sync_research.py
16 passed

$ uv run pytest -m smoke -q
49 passed, 11 deselected

$ uv run ruff check src/tools/research.py src/agents/factory src/agents/specialists tests/
All checks passed!
```

No `threading` / `TavilySearch` in specialist modules.

## Phase 1

Polish slice complete. Queue `next/` empty unless new prompts are added.
