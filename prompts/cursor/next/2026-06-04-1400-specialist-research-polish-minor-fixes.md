# Task: Specialist Research Phase 1 — Slice 1400: Polish minor review issues

**Read these first (mandatory):**
- `docs/plans/specialist-research-phase1.md` (approved)
- `prompts/cursor/WORKFLOW.md` and `.cursor/rules/04-cursor-workflow.mdc`
- Review notes (source of this slice):
  - `prompts/cursor/done/2026-06-09-1100-specialist-research-runner/review.md` (minor notes)
  - `prompts/cursor/done/2026-06-09-1200-specialist-template-sync-research/review.md` (minor notes)
- Prior slice outputs: `1100`, `1200`, and **`1300`** done folders (this slice runs **after 1300**)

**Depends on:** Slices **1100**, **1200**, and **1300** complete and merged or present in the working tree. If `1300` is not done, **stop** and report in `output.md`.

**Objective**

Address non-blocking issues from Grok reviews of 1100/1200 — storage/retry semantics, specialist messaging for mixed outcomes, runner completeness, `financial` category metadata, and targeted smoke tests. Keep sync Phase 1; do not introduce async dispatch.

---

## Fixes (implement all)

### 1. Omitted LLM fields → `pending` (`src/tools/research.py`)

When `_persist_proposal` receives no `FieldProposal` for a `target_fields` entry, **persist `pending`** with `last_error` explaining omission (do not leave the field absent).

After a successful partial persist, any `target_fields` still without a record should also be marked `pending` with a clear error.

**Test:** smoke test — mock proposal missing one of two `target_fields` → storage shows `pending` + `last_error` for the missing field.

### 2. Pre-mark `pending` before sync research (`specialist_agent.py.j2`)

Before calling `run_field_research`, call `_mark_fields_pending(pid, need, storage)` for fields in `need` (empty cache misses only — do not overwrite `found`/`na`).

Regenerate all six specialists via `regenerate_specialists_from_registry()`.

**Test:** extend `tests/test_specialist_sync_research.py` or add smoke test — after invoking specialist with mocked slow/no-op research, storage shows `pending` with `started_at` on the field before research completes (mock can assert pre-mark by checking storage mid-call if needed, or verify `started_at` exists when research raises).

### 3. Retry stale `pending` (`specialist_agent.py.j2`)

`_fields_needing_research` should include fields that are `pending` **and** have `last_error` set (failed research), so a subsequent query re-invokes sync research. Do **not** retry bare `pending` without `last_error` if research is actively in progress on same process (Phase 1 sync is blocking, so this is mainly for failed runs).

Optionally respect env `MYCELIUM_RESEARCH_RETRY_PENDING=1` (default **on**): when set, retry any `pending` older than N seconds (default 0 = retry all pending-with-error only). Document in `.env.example`.

Regenerate six specialists.

**Test:** smoke — seed storage with `pending` + `last_error`, invoke specialist, assert `run_field_research` called again (mock).

### 4. `mixed` overall status messaging (`specialist_agent.py.j2`)

When some owned fields are `found` and others `na` (and none `pending`), set a dedicated branch:

- `overall_status` remains `"mixed"` (or introduce `"partial"` if you prefer — if you change the status string, update tests and `assemble_response` merge paths only if they depend on it; prefer keeping `"mixed"` for contrib).
- User-facing `message` must **not** say all attributes are “not currently available”. Example: “Found email; phone marked N/A (via contact_specialist).”

Regenerate six specialists.

**Test:** smoke — contact specialist with one `found` and one `na` in storage after mock research → message mentions both; no “not currently available” for the found field.

### 5. `financial` in `data/categories.json`

Add a `financial` category block consistent with `data/agent_registry.json` / `financial_specialist` (description, examples, `assigned_agent`: `financial_specialist`). Update `attribute_map` only if there are known financial attributes already classified elsewhere; otherwise examples-only is fine.

**Test:** `load_category_metadata("financial")` returns non-empty description in existing or new smoke test.

### 6. Runner failure smoke tests (`tests/test_research.py`)

Add **smoke** tests (mocked, no live API):

- Timeout path → `pending` + `last_error` contains `timed out`
- `proposal is None` from `_run_llm_loop` → `pending` on all `target_fields`

Mark `@pytest.mark.smoke`.

### 7. Specialist `audit_log` for research (template)

After `_run_field_research`, append one audit line when research ran, e.g. `contact_specialist: research completed for id=… fields=[email] errors=0` (include `ResearchRunResult.errors` count or summary if returned — may require returning result from hook or reading storage meta `research_audit` tail).

Keep concise; do not duplicate full `meta.research_audit` into graph `audit_log`.

Regenerate six specialists.

---

## Out of scope

- Async / background research dispatch
- Graph topology, MCP, `PersonQuery` changes
- Tavily Extract/Crawl
- Renaming done-folder dates (`2026-06-09` vs `2026-06-04`)
- Refactoring `tools.research` → `agents` import layering (document only if needed)
- Live API integration tests (keys required)

---

## Exact steps (in order)

1. **Claim:** Move to `prompts/cursor/in-progress/2026-06-04-1400-specialist-research-polish-minor-fixes/prompt.md`.

2. **Discovery:** Read 1100/1200/1300 done outputs; run `uv run pytest -m smoke -q` baseline.

3. Implement fixes **1–7** above.

4. **Regenerate** all six `src/agents/specialists/*_specialist.py` from template (mandatory after template edits).

5. **Verification:**
   ```bash
   uv run pytest -m smoke -q tests/test_research.py tests/test_specialist_sync_research.py
   uv run pytest -m smoke -q
   uv run ruff check src/tools/research.py src/agents/factory src/agents/specialists tests/
   ```

6. **Deliverables** in `prompts/cursor/done/2026-06-04-1400-specialist-research-polish-minor-fixes/`:
   - `prompt.md`, `output.md` (map each fix 1–7 to what changed + test names)
   - Remove only your claim from `in-progress/`

---

## Scope boundaries (strict)

**May modify:**
- `src/tools/research.py`
- `src/agents/factory/templates/specialist_agent.py.j2`
- `src/agents/specialists/*_specialist.py` (regenerated)
- `src/agents/factory/agent_factory.py` (only if needed for regen)
- `data/categories.json` (`financial` block + attribute_map if applicable)
- `tests/test_research.py`, `tests/test_specialist_sync_research.py`
- `.env.example` (retry env var comments)

**Out of scope unless blocking bug:**
- `src/graphs/core.py`, `src/agents/dispatch.py`, `src/agents/responses.py` — **exception:** if `assemble_response` or merge logic must understand `"mixed"` contrib for messaging tests, make the **minimal** change and document in `output.md`
- `docs/architecture.md` / README (1300 owns unless one line on retry env is needed)

**Test policy:** Smoke only unless you add `@pytest.mark.full` (then run it immediately).

---

## Acceptance checklist

- [ ] Missing LLM field proposals → `pending` + `last_error` in storage
- [ ] `need` fields pre-marked `pending` before `run_field_research`
- [ ] `pending` + `last_error` re-enters research on next query
- [ ] `found` + `na` mixed contrib → honest message (not all “unavailable”)
- [ ] `financial` category in `categories.json`
- [ ] Timeout + null-proposal smoke tests pass
- [ ] Six specialists regenned; no threading/Tavily in specialist modules
- [ ] Full smoke suite green