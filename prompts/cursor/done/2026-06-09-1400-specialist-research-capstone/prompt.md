# Task: Specialist Research Phase 1 — Slice 1400: Remaining niggles (capstone polish)

**Read these first (mandatory):**
- `docs/plans/specialist-research-phase1.md` (approved)
- `prompts/cursor/WORKFLOW.md` and `.cursor/rules/04-cursor-workflow.mdc`
- Grok reviews (full minor-notes sections):
  - `prompts/cursor/done/2026-06-09-1100-specialist-research-runner/review.md`
  - `prompts/cursor/done/2026-06-09-1200-specialist-template-sync-research/review.md`
  - `prompts/cursor/done/2026-06-09-1300-specialist-research-integration/review.md`
- Done outputs: `1100`, `1200`, `1300`

**Depends on:** Slices **1100**, **1200**, and **1300** present in the working tree (implementation + integration tests). If research runner or sync template is missing, **stop** and report in `output.md`.

**Objective**

Close **all remaining non-blocking niggles** from Phase 1 specialist research reviews in one slice. Keep **sync** Phase 1; do **not** implement async dispatch, Tavily Extract/Crawl, or MCP/graph contract changes.

This is the **last queued slice** for specialist-research Phase 1 before Paul/Grok commit the full stack.

---

## Fixes (implement all)

### 1. Omitted LLM fields → `pending` (`src/tools/research.py`)

When `_persist_proposal` has no `FieldProposal` for a `target_fields` entry, persist **`pending`** + `last_error` (do not leave the field absent).

After partial persist, any `target_fields` still without a storage record → **`pending`** + `last_error`.

**Test (smoke):** mock proposal with only one of two `target_fields` → missing field is `pending` in storage.

### 2. Pre-mark `pending` before sync research (`specialist_agent.py.j2`)

Before `run_field_research`, call `_mark_fields_pending(pid, need, storage)` for fields in `need` only (do not clobber `found`/`na`).

**Test (smoke):** storage has `pending` + `started_at` for `need` fields when research is mocked to inspect mid-flight or when research no-ops after pre-mark.

### 3. Retry failed `pending` (`specialist_agent.py.j2`)

`_fields_needing_research` must include fields with `status: "pending"` **and** non-empty `last_error` (failed prior research) so the next query re-runs sync research.

Do **not** re-queue fields that are `pending` without `last_error` during the same in-process sync call (blocking research already running).

Env (document in `.env.example`):

- `MYCELIUM_RESEARCH_RETRY_PENDING` — default `1` (retry pending-with-error)
- Optional: `MYCELIUM_RESEARCH_RETRY_PENDING_MIN_AGE_SEC` — only retry if `started_at` older than N seconds (default `0` = no age gate)

**Test (smoke):** seed `pending` + `last_error`; invoke specialist; assert `run_field_research` called (mock).

### 4. `mixed` status messaging (`specialist_agent.py.j2`)

When some owned fields are `found` and others `na` (no `pending`), use a **dedicated response branch**:

- Keep contrib `overall_status` as `"mixed"` unless you have a strong reason to add `"partial"`.
- `message` must list outcomes accurately (e.g. “email: …; phone: N/A”) — **not** blanket “not currently available” for found fields.

**Test (smoke):** storage with one `found` + one `na`; invoke contact specialist for both fields; message mentions both states.

### 5. `_run_field_research` returns result (`specialist_agent.py.j2`)

Change hook to return `ResearchRunResult | None` from `run_field_research` when research runs.

Use it for **audit_log** (fix 7) and avoid re-loading storage only for error counts.

### 6. Specialist `audit_log` after research (template)

After research, append one line, e.g.:

`contact_specialist: research id=<uuid> fields=[email] updated=[email] tool_calls=1 errors=0`

Concise; do not paste full `meta.research_audit` into graph audit.

### 7. `financial` in `data/categories.json`

Add `financial` category aligned with `data/agent_registry.json` (`financial_specialist`, description, examples). Extend `attribute_map` only for attributes you can justify from existing usage.

**Test (smoke):** `load_category_metadata("financial")` has non-empty `description`.

### 8. Runner failure smoke tests (`tests/test_research.py`)

Mocked smoke tests:

- Overall timeout → all `target_fields` `pending`, `last_error` mentions timeout
- `_run_llm_loop` returns `proposal is None` → all `target_fields` `pending`

### 9. Integration: `na` in same response (`tests/test_specialist_research_integration.py`)

Add smoke test: mock `run_field_research` persisting `na` + `reason` for `email` → single `run_query` returns honest messaging (attribute not presented as found; message or merge behavior per `responses.py` — assert what the product **should** do and document in `output.md`).

### 10. Integration: stable assertions (`tests/test_specialist_research_integration.py`)

Reduce brittle `response.debug` substring checks where possible:

- Prefer asserting on `results`, `message`, and stable outcome semantics.
- If debug format must stay, centralize expected fragments in one helper or comment why strings are stable.

Do not weaken coverage of `outcome='assembled'` / contributions without replacement assertions.

### 11. Plan doc status line (`docs/plans/specialist-research-phase1.md`)

Add one line under **Status** or **Approval checklist**: “Phase 1 implemented via Cursor slices 1100–1300; polish in 1400.” Keep edits minimal (this file only).

### 12. Regenerate specialists (mandatory)

After all template changes:

```bash
uv run python -c "from agents.factory.agent_factory import get_agent_factory; print(get_agent_factory().regenerate_specialists_from_registry())"
```

Confirm all six `src/agents/specialists/*_specialist.py` updated; grep: no `threading`, no `_stub_background_research`, no `langchain_tavily` / `TavilySearch`.

---

## Out of scope

- Async / background research / job queue
- Graph topology, MCP, `PersonQuery` / public API shape changes
- Tavily Extract / Crawl
- Renaming `prompts/cursor/done/2026-06-09-*` folder dates
- Refactoring `tools.research` ↔ `agents` import layering (note in `output.md` only if relevant)
- Live API / manual Tavily runs in CI
- `MYCELIUM_RESEARCH_VERBOSE_DEBUG` implementation (unless trivial one-liner; defer)
- Git commit (Paul/Grok handles after review)

---

## Exact steps (in order)

1. **Claim:** `prompts/cursor/in-progress/2026-06-04-1400-specialist-research-polish-minor-fixes/prompt.md`

2. **Discovery:** Read three `review.md` files; `uv run pytest -m smoke -q` baseline; note count.

3. Implement fixes **1–12**.

4. **Verification:**
   ```bash
   uv run pytest -m smoke -q tests/test_research.py tests/test_specialist_sync_research.py tests/test_specialist_research_integration.py
   uv run pytest -m smoke -q
   uv run ruff check src/tools/research.py src/agents/factory src/agents/specialists tests/
   ```

5. **Deliverables** in `prompts/cursor/done/2026-06-04-1400-specialist-research-polish-minor-fixes/`:
   - `prompt.md`, `output.md` with a table mapping fix **1–12** → files/tests
   - Remove only your claim from `in-progress/`

---

## Scope boundaries (strict)

**May modify:**
- `src/tools/research.py`
- `src/agents/factory/templates/specialist_agent.py.j2`
- `src/agents/specialists/*_specialist.py` (regenerated)
- `src/agents/factory/agent_factory.py` (if needed for regen only)
- `data/categories.json`
- `tests/test_research.py`, `tests/test_specialist_sync_research.py`, `tests/test_specialist_research_integration.py`
- `.env.example` (retry / research env comments)
- `docs/plans/specialist-research-phase1.md` (fix 11 only)

**May touch minimally:**
- `src/agents/responses.py` — only if required for correct `na` / `mixed` messaging in integration test; document why

**Out of scope:**
- `docs/architecture.md`, `README.md` (unless one-line retry note is essential — prefer `.env.example`)

**Test policy:** Smoke by default; any new `@pytest.mark.full` must be run immediately.

---

## Acceptance checklist

- [ ] 1–12 implemented; `output.md` maps each to code/tests
- [ ] Six specialists regenned; no threading/Tavily in specialist modules
- [ ] Full smoke suite green
- [ ] Phase 1 research niggles from 1100/1200/1300 reviews addressed or explicitly deferred with reason in `output.md` (should be **none** deferred if possible)