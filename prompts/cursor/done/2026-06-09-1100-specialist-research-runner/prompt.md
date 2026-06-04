# Task: Specialist Research Phase 1 — Slice 1100: Research runner (`research.py`)

**Read these first (mandatory):**
- `docs/plans/specialist-research-phase1.md` (approved — **sync** Phase 1, full context in prompts, low confidence → `na` + `reason`)
- `prompts/cursor/WORKFLOW.md` and `.cursor/rules/04-cursor-workflow.mdc`
- `docs/architecture.md` (graph, merge rules, specialists-only tools)
- `prompts/system/CORE_PROMPT.md`
- `src/tools/tavily.py` (already implemented — **reuse**, do not reimplement Tavily)
- `src/agents/classification/engine.py` (pattern: `ChatOpenAI`, `with_structured_output`)
- `src/agents/context.py` (`build_full_context` shape: `seed` + `specialists`)
- `src/agents/specialists/base.py` (`SpecialistStorage`)

**Prerequisite (done):** Slice 1000 Tavily tool is merged (`src/tools/tavily.py`, `tests/test_web_search.py`, `langchain-tavily` in `pyproject.toml`). Do not duplicate unless you find a bug.

**Objective**

Implement the **category-agnostic** research runner in `src/tools/research.py`: bounded LLM + Tavily `web_search` tool loop, structured proposals, validation, persist to `SpecialistStorage`. Phase 1 calls this **synchronously** from specialists (slice 1200); design the API so dispatch can move to async later without rewriting validation/persist logic.

**Agreed behavior (do not deviate)**

| Rule | Implementation |
|------|----------------|
| Context in prompt | Serialize **full** `context` dict from `build_context` (`seed` + `specialists` union). |
| Writes | Only fields in `target_fields` for this specialist/category. |
| Low confidence | Persist `status: "na"` with required `reason` (explain weak evidence). |
| `found` | Non-empty `value`, `confidence >= RESEARCH_MIN_CONFIDENCE` (default `0.6`, env `MYCELIUM_RESEARCH_MIN_CONFIDENCE`), at least one `sources` URL. |
| Failure (API/LLM/timeout) | `pending` + optional `last_error`; no fake `found`. |
| Tools | `web_search` / `create_tavily_search_tool` only — no direct `TavilySearch` outside `tools/tavily.py`. |
| God agent | One `research.py` runner; category hints via Jinja fragments only. |

**Constraints**

- Small, reviewable slice: **no** specialist template changes, **no** regen of `*_specialist.py`, **no** graph/supervisor/MCP changes in this slice.
- Smoke tests only (`uv run pytest -m smoke -q`) unless you add a `@pytest.mark.full` test (then run it immediately per WORKFLOW).
- Mock all LLM and Tavily calls in tests — no live API keys required in CI.

---

## Exact steps (in order)

1. **Claim (mandatory):** Move this file to `prompts/cursor/in-progress/2026-06-04-1100-specialist-research-runner/prompt.md` before any edits. Document the move in `output.md`.

2. **Discovery (read-only):** `git status`, read files listed above, run `uv run pytest -m smoke -q tests/test_web_search.py` as baseline.

3. **Implement `src/tools/research.py`** (module docstring: sync Phase 1; async dispatch deferred).

   **Models** (Pydantic, can live in same module):
   - `FieldProposal`: `field`, `value`, `status` (`found` | `na`), `confidence`, `sources: list[str]`, optional `reason` for `na`
   - `ResearchProposal`: `fields: list[FieldProposal]`, `notes: str = ""`

   **Config** (env with sensible defaults):
   - `MYCELIUM_RESEARCH_MIN_CONFIDENCE` (default `0.6`)
   - `MYCELIUM_RESEARCH_MAX_TOOL_ROUNDS` (default `3`)
   - `MYCELIUM_RESEARCH_TIMEOUT_SEC` (default `120`) — enforce on the overall run if practical
   - `OPENAI_API_KEY` + `TAVILY_API_KEY` via `is_research_available()` (both required)

   **Prompt building:**
   - `src/agents/factory/templates/research/_system.j2` — shared system skeleton (role, tool rules, output schema summary)
   - `src/agents/factory/templates/research/{category}.md.j2` for: `contact`, `social`, `relationships`, `demographic`, `professional`, `financial` (short category-specific guidance; contact should mention verifying legal name vs seed)
   - Load category metadata from `data/categories.json` (description, examples) when building user message
   - User message includes JSON (or compact structured text) of **full** `context`, `person_id`, `target_fields`, category name

   **LLM loop:**
   - `ChatOpenAI` (default `gpt-4o-mini`, env `MYCELIUM_RESEARCH_MODEL` optional)
   - Bind `create_tavily_search_tool()`; loop: invoke → execute tool calls → append tool messages until no tool calls or max rounds
   - Final structured output via `with_structured_output(ResearchProposal)` (separate final invoke or last message without tools — your choice, document in `output.md`)

   **Public API:**
   ```python
   def is_research_available() -> bool: ...
   def run_field_research(
       *,
       category: str,
       specialist_name: str,
       person_id: str,
       target_fields: list[str],
       context: dict[str, Any],
       storage: SpecialistStorage,
   ) -> ResearchRunResult: ...
   ```
   - `ResearchRunResult`: `fields_updated: list[str]`, `errors: list[str]`, `tool_calls_count: int`
   - Persist per field under `records[person_id][field]` per plan (`found` / `na` / `pending` shapes with `researched_at` ISO timestamps)
   - Append to storage `audit_log` in meta or a simple list field if the storage schema already supports it; otherwise log via return value only (slice 1200 will surface in specialist `audit_log`)

   **Helpers:** `load_category_metadata(category: str) -> dict` (read `data/categories.json`)

4. **Update `src/tools/__init__.py`** — export `run_field_research`, `is_research_available`, `ResearchRunResult`, models as appropriate.

5. **`.env.example`** — add optional `MYCELIUM_RESEARCH_*` and `MYCELIUM_RESEARCH_MODEL` comments (keep existing `TAVILY_API_KEY`).

6. **Tests: `tests/test_research.py`** (all `@pytest.mark.smoke`, mocked):
   - Validation: low confidence → `na` + `reason`
   - Validation: good proposal → `found` with sources
   - Rejects proposals for fields not in `target_fields`
   - `is_research_available()` false when keys missing → no persist / error path
   - Tool loop: mock LLM returning one tool call then structured proposal; mock Tavily invoke
   - Use `tmp_path` + `SpecialistStorage(..., base_dir=tmp_path)` — never write real `data/agents/` in tests

7. **Verification:**
   ```bash
   uv run pytest -m smoke -q tests/test_research.py tests/test_web_search.py
   uv run ruff check src/tools tests/test_research.py
   ```
   Grep: no `TavilySearch` import outside `src/tools/tavily.py`.

8. **Deliverables** (`prompts/cursor/done/2026-06-04-1100-specialist-research-runner/`):
   - `prompt.md`, `output.md` (summary, decisions, verification output, `git diff --stat`)
   - Remove **only** your claim from `in-progress/`

---

## Scope boundaries (strict)

**You may modify/create:**
- `src/tools/research.py`
- `src/tools/__init__.py`
- `src/agents/factory/templates/research/**` (new)
- `tests/test_research.py`
- `.env.example` (research env vars only)

**Out of scope (do not touch):**
- `src/agents/factory/templates/specialist_agent.py.j2`
- `src/agents/specialists/*_specialist.py`
- `src/graphs/`, `src/agents/supervisor.py`, `src/agents/dispatch.py`, `src/agents/responses.py`, MCP, `PersonQuery`, `docs/plans/specialist-research-phase1.md`
- `src/tools/tavily.py` (unless critical bugfix — document and keep minimal)

If you need template/specialist wiring to test end-to-end, **stop** and note in `output.md`; slice **1200** handles that.

**Test execution policy:** Smoke only for this slice.

---

**Next queue item after this slice:** `2026-06-04-1200-specialist-template-sync-research.md`