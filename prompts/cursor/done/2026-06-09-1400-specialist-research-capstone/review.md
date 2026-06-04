# Review — 2026-06-09-1400-specialist-research-capstone (slice 1400, final)

**Reviewer:** Grok (on behalf of Paul) — **re-review after Cursor finished capstone pass**  
**Artifacts:** `prompts/cursor/done/2026-06-09-1400-specialist-research-capstone/` (+ earlier `…-polish-minor-fixes/` for first 1–7 pass)  
**Implementation:** uncommitted 1100–1400 stack on `main`

**Overall:** **Approved** — expanded checklist **1–12** is satisfied. Phase 1 specialist research is complete pending commit.

---

## Two deliverable folders (expected)

| Folder | What landed |
|--------|-------------|
| `2026-06-09-1400-specialist-research-polish-minor-fixes/` | First pass: fixes 1–7 (runner, template, regen, core tests) |
| `2026-06-09-1400-specialist-research-capstone/` | Second pass: fixes **9–11**, audit format tweak, env alias |

Treat **capstone `output.md`** as the authoritative fix map for the full 1–12 list.

---

## Fix checklist (1–12)

| # | Item | Verdict |
|---|------|---------|
| 1 | Omitted LLM fields → `pending` | **Done** |
| 2 | Pre-mark `pending` before research | **Done** |
| 3 | Retry `pending` + `last_error` (+ stale age env) | **Done** |
| 4 | `mixed` messaging | **Done** |
| 5 | `_run_field_research` returns `ResearchRunResult` | **Done** |
| 6 | Audit line (`updated`, `tool_calls`, `errors`) | **Done** — capstone format |
| 7 | `financial` in `categories.json` | **Done** |
| 8 | Timeout + null-proposal tests | **Done** |
| 9 | Integration `na` same `run_query` | **Done** — `test_run_query_email_na_in_same_response_when_research_mocked` |
| 10 | Stable integration assertions | **Done** — `_assert_single_person_assembled` (less brittle than exact `outcome='assembled'`) |
| 11 | Plan status line | **Done** — “implemented via … 1100–1300; capstone polish in 1400” |
| 12 | Regen six specialists | **Done** |

---

## Strengths

- Capstone closed the gaps from the prior **Approved with minor gaps** review (items 9–11).
- Integration `na` test documents product behavior: `results["email"] == "N/A"`, message does not imply discovery.
- Retry env supports both `MYCELIUM_RESEARCH_RETRY_PENDING_SEC` and `MYCELIUM_RESEARCH_RETRY_PENDING_MIN_AGE_SEC` alias.
- **50** smoke tests green (was 49 before `na` test).

---

## Minor notes (non-blocking)

1. **`docs/plans/specialist-research-phase1.md` ~line 26:** Still says assembly implemented in “slice 1400” — that conflates this research polish with the **2026-06-04-1400-filter-query-results** slice. Fix wording on next doc touch (e.g. “slice 2026-06-04-1400-filter-query-results”).

2. **Duplicate done folders** for one queue prompt — fine for history; optional merge/archive later.

3. **`_assert_single_person_assembled`** still asserts `contributions={n}` in `debug` — acceptable compromise; not as brittle as the old `outcome='assembled'` exact match.

4. **Commit** the full 1100–1400 implementation stack when ready (still local-only).

---

## Verification (Grok re-run)

```
uv run pytest -m smoke -q tests/test_research.py tests/test_specialist_sync_research.py tests/test_specialist_research_integration.py  → 19 passed
uv run pytest -m smoke -q                                                                                                              → 50 passed, 11 deselected
uv run ruff check src/tools/research.py src/agents/factory src/agents/specialists tests/                                               → passed
grep threading|TavilySearch|_stub_background in src/agents/specialists/                                                                → no matches
```

---

## Status

**Approved.** Phase 1 research queue complete; `next/` empty. Proceed to commit + optional plan-doc typo fix.