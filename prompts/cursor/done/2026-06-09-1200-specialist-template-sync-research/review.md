# Review — 2026-06-09-1200-specialist-template-sync-research (slice 1200)

**Reviewer:** Grok (on behalf of Paul)  
**Depends on:** 1100 approved (`src/tools/research.py`)  
**Artifacts:** `prompt.md`, `output.md`, uncommitted implementation

**Overall:** **Approved** — ready for slice **1300** (integration tests + docs).

---

## Plan / prompt alignment

| Requirement | Verdict |
|-------------|---------|
| Remove threading / `_stub_background_research` | Yes — grep clean on all six `*_specialist.py` |
| Sync `_run_field_research` → `tools.research.run_field_research` | Yes — lazy import in hook |
| Full `ctx` + `person_id` passed to runner | Yes |
| Re-read storage after research; contrib reflects `found`/`na`/`pending` | Yes |
| Keys missing → pending, no crash | Yes — `_mark_fields_pending` when unavailable |
| No Tavily in specialists | Yes |
| Regen all six from template | Yes — `regenerate_specialists_from_registry()` + committed files updated |
| `render_specialist_py` / regen helper on factory | Yes — `create_specialist` delegates to render |
| Contact + email smoke test (mocked) | Yes — `test_contact_email_sync_research_persists_found_not_pending` |
| Scope: no graph/MCP/`research.py` feature work | Yes — `research.py` untouched in this slice |

---

## Strengths

- Batched cache misses: one `run_field_research` call per invocation with `need` list — efficient vs per-field calls.
- `_fields_needing_research` skips `found`/`na`/`pending` — avoids duplicate work on completed fields.
- `regenerate_specialists_from_registry()` is reusable for future template edits (better than hand-editing six files).
- Tests use isolated `MYCELIUM_*` paths; mock at `tools.research` boundary matches 1100 tests.

---

## Minor notes (non-blocking)

1. **Stale `pending` not retried:** Fields already `pending` are excluded from `need`, so a failed prior run will not re-invoke sync research on the next query (same as old thread-guard behavior). Acceptable for Phase 1; consider retry policy in polish/async slice.

2. **`overall_status == "mixed"` messaging (pre-existing):** When some fields are `found` and others `na`, template sets `overall = "mixed"` but the response branch treats non-`found`/non-`na` as **pending** messaging (`"not currently available"`). Unlikely in single-field queries; worth fixing in **1300** or polish if multi-field requests become common.

3. **No pre-mark `pending` before sync research:** Old flow wrote `pending` then background thread. New flow runs research immediately on empty fields — fine for sync; combined with 1100, omitted LLM fields may leave storage empty while contrib shows `pending` (1100 note). Optional: pre-mark `need` fields pending before `run_field_research`.

4. **Regen test scope:** `test_regenerated_contact_specialist_has_no_threading` checks factory output under `tmp_path`, not the six committed repo files — committed files were verified via grep (no threading).

5. **Commit hygiene:** 1100 + 1200 + tests still uncommitted together on `main`; commit as one feature stack before 1300 if desired.

---

## Verification (Grok re-run)

```
uv run pytest -m smoke -q tests/test_research.py tests/test_specialist_sync_research.py tests/test_agent_factory.py  → 13 passed
uv run pytest -m smoke -q                                                                                              → 40 passed
uv run ruff check src/agents/factory src/agents/specialists src/tools/research.py tests/...                            → passed
grep threading|_stub_background|langchain_tavily in src/agents/specialists/                                            → no matches
```

---

## Status

**Approved.** Proceed with `2026-06-04-1300-specialist-research-integration.md`.