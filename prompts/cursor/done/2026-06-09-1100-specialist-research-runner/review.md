# Review — 2026-06-09-1100-specialist-research-runner (slice 1100)

**Reviewer:** Grok (on behalf of Paul)  
**Artifacts:** `prompt.md`, `output.md`, uncommitted implementation on `main`

**Overall:** **Approved** — ready for slice **1200** (specialist template sync wiring). No blocking issues.

---

## Plan alignment

| Requirement | Verdict |
|-------------|---------|
| Shared `research.py` runner (category-agnostic) | Yes |
| Full `context` in user prompt (JSON payload) | Yes — `build_research_prompts` embeds entire `context` |
| `target_fields` write scope + validation reject outsiders | Yes |
| Low confidence → `na` + `reason` | Yes — `_validate_and_build_record` |
| `found` needs value, confidence ≥ threshold, ≥1 source URL | Yes |
| API/timeout/unavailable → `pending` + `last_error` | Yes — `_mark_pending`, `ThreadPoolExecutor` timeout |
| Tavily only via `tools/tavily.py` | Yes — `TavilySearch` only in `tavily.py` |
| Sync Phase 1 API; async dispatch later | Yes — module docstring + `run_field_research` contract |
| No specialist template / graph changes | Yes — scope respected |
| Jinja fragments (6 categories + `_system`) | Yes |
| Smoke tests, mocked, tmp storage | Yes — 7 tests in `test_research.py` |

---

## Strengths

- Clear split: tool loop (`_run_llm_loop`) vs validation/persist (`_validate_and_build_record`, `_persist_proposal`).
- Injectable `llm=` on `run_field_research` — tests avoid live APIs.
- `meta.research_audit` trail is useful for debugging before specialist `audit_log` wiring in 1200.
- Env knobs documented in `.env.example`.
- Reuses existing classification pattern (`with_structured_output` on final pass).

---

## Minor notes (non-blocking)

1. **Omitted target field in LLM proposal:** `_persist_proposal` appends `"no proposal for field …"` to `errors` but does not write `pending` or `na` for that field. Slice **1200** should either pre-mark all `target_fields` pending before calling the runner, or extend the runner to set `pending` when a requested field is missing from the proposal (aligns with plan failure semantics).

2. **`financial` not in `data/categories.json`:** `load_category_metadata("financial")` returns empty description/examples; `financial.md.j2` still exists. Acceptable for now; consider adding a `financial` block to `categories.json` in a later doc/data slice.

3. **Done-folder date:** Delivered as `2026-06-09-1100-…` while queue file was `2026-06-04-1100-…`. Cosmetic only.

4. **Layer coupling:** `tools.research` imports `agents.specialists.base.SpecialistStorage` — intentional per API, but creates `tools` → `agents` dependency. Watch for import cycles when 1200 wires specialists → `tools.research` (likely fine: `base.py` does not import `research`).

5. **Test gaps (optional polish):** No smoke test for timeout (`FuturesTimeoutError`) or for “LLM returns `None` proposal → pending”. Not required to approve 1100.

6. **`person_id` parameter name:** Matches 1100 prompt; 1200 must pass graph `current_id` (UUID) — output.md documents this correctly.

---

## Verification (Grok re-run)

```
uv run pytest -m smoke -q tests/test_research.py tests/test_web_search.py  → 11 passed
uv run ruff check src/tools tests/test_research.py                         → passed
TavilySearch in src/                                                       → only tavily.py
```

---

## Status

**Approved.** Proceed with `2026-06-04-1200-specialist-template-sync-research.md`.