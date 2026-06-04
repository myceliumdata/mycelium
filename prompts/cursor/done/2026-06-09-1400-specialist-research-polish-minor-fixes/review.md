# Review — 2026-06-09-1400-specialist-research-polish-minor-fixes (slice 1400)

**Reviewer:** Grok (on behalf of Paul)  
**Artifacts:** `prompt.md`, `output.md`, uncommitted implementation (1100–1400 stack)

**Overall:** **Superseded** — see **`2026-06-09-1400-specialist-research-capstone/review.md`** for the final approval after the capstone pass completed items 9–11.

*(Original note: Approved with minor gaps on first pass only.)*

---

## Fix checklist (prompt items 1–12)

| # | Item | Verdict |
|---|------|---------|
| 1 | Omitted LLM fields → `pending` + `last_error` | **Done** — `_persist_proposal` + post-pass |
| 2 | Pre-mark `pending` before research | **Done** — `_evaluate_owned_fields` + `test_contact_pre_marks_pending_before_research_runs` |
| 3 | Retry `pending` + `last_error` | **Done** — `_fields_needing_research` + env vars + `test_contact_retries_pending_with_last_error` |
| 4 | `mixed` messaging branch | **Done** — `test_contact_mixed_found_and_na_message` |
| 5 | `_run_field_research` returns `ResearchRunResult` | **Done** |
| 6 | Specialist `audit_log` after research | **Done** — `research completed … error_count=` |
| 7 | `financial` in `categories.json` | **Done** — category + `attribute_map` + `test_load_category_metadata_financial` |
| 8 | Timeout + null-proposal smoke tests | **Done** |
| 9 | Integration test: `na` in same `run_query` response | **Not done** |
| 10 | Less brittle integration `debug` assertions | **Not done** — still `outcome='assembled'` / `contributions=1` substrings |
| 11 | Plan doc “implemented 1100–1300, polish 1400” line | **Not done** — status still “Approved” only |
| 12 | Regen six specialists | **Done** — no threading / Tavily in specialists |

`output.md` documents fixes **1–7** only; implementation largely matches the expanded **1–8** and **12** set.

---

## Strengths

- `_pending_record` helper unifies pending shape (`started_at`, `last_error`).
- Retry logic goes beyond review ask: optional stale `pending` via `MYCELIUM_RESEARCH_RETRY_PENDING_SEC` when `last_error` absent.
- Validation failures in `_persist_proposal` now write `pending` instead of leaving holes.
- Mixed-status UX is clear and tested at specialist level.
- Test count grew appropriately (16 research/sync + 2 integration = **49** smoke passes).
- `.env.example` documents retry knobs (note env name is `MYCELIUM_RESEARCH_RETRY_PENDING_SEC`, not `…_MIN_AGE_SEC` from prompt draft — fine).

---

## Minor gaps (non-blocking)

1. **Items 9–10 (1300 review):** No end-to-end `na` integration test; debug assertions unchanged. Recommend a 5-line follow-up or accept for Phase 1.

2. **Item 11:** Plan header not updated to record implementation complete — optional doc hygiene before commit.

3. **`docs/plans/specialist-research-phase1.md` line ~26:** References “slice 1400” for `assemble_response` — that was the **query-results** slice, not this research polish. Fix wording when touching the plan (e.g. “slice 2026-06-04-1400-filter-query-results”).

4. **Full stack still uncommitted** — 1100–1400 code + tests + docs should land as one (or two) commits after this approval.

---

## Verification (Grok re-run)

```
uv run pytest -m smoke -q  → 49 passed, 11 deselected
uv run ruff check (research, factory, specialists, tests)  → passed
grep threading|TavilySearch|_stub_background in specialists/  → no matches
```

---

## Status

**Approved with minor gaps** (9–11 optional). Phase 1 specialist research queue is **functionally complete** for Paul to commit the implementation stack.