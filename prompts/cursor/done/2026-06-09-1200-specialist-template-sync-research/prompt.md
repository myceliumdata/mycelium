# Task: Specialist Research Phase 1 — Slice 1200: Sync research in specialist template + regen

**Read these first (mandatory):**
- `docs/plans/specialist-research-phase1.md` (approved — sync Phase 1)
- `prompts/cursor/WORKFLOW.md` and `.cursor/rules/04-cursor-workflow.mdc`
- `src/tools/research.py` and `src/agents/factory/templates/specialist_agent.py.j2` (current stub thread)
- `src/agents/factory/agent_factory.py` (render/regen pattern)
- `data/categories.json` + `data/agent_registry.json` (six generated specialists)
- Prior slice output (if present): `prompts/cursor/done/2026-06-04-1100-specialist-research-runner/output.md`

**Depends on:** Slice **1100** complete (`run_field_research`, `is_research_available`, research Jinja fragments). If 1100 is not merged, **stop** and report in `output.md`.

**Objective**

Wire **synchronous** research into `specialist_agent.py.j2`, remove daemon-thread stub, **regenerate all six** committed `*_specialist.py` files. Prove behavior for **`contact`** + **`email`** with mocked research in tests (no live API in CI).

**Agreed behavior**

- On cache miss for an owned field: if `is_research_available()`, call `run_field_research(...)` **inline** with full `ctx`, `pid`, `owned`/`target_fields`, and `SpecialistStorage`; then **re-read** storage and build `values` from `found` / `na` / `pending`.
- If keys missing: keep current **pending** path (no crash).
- **Remove** `threading` / `Thread` / `_stub_background_research` daemon pattern.
- Keep hook name like `_run_field_research(...)` that delegates to `tools.research.run_field_research` so async dispatch can replace the call site later.
- **Do not** build `PersonResponse` inside the research runner.
- **No** direct Tavily imports in generated specialists — only `tools.research` / `tools` package.

**Regen (mandatory)**

`AgentFactory.create_specialist` no-ops when the agent is already registered. **Overwrite** each existing specialist `.py` by rendering `specialist_agent.py.j2` with the same metadata as `data/agent_registry.json` / `data/categories.json` (plus `financial_specialist` if registered).

Acceptable approach:
- Add `AgentFactory.render_specialist_py(...)` (or `regenerate_specialist_py`) that renders and `write_text`s **without** requiring `create_specialist` to return `created: True`, **or**
- A one-off script under `tests/` / documented `uv run python -c` block in `output.md` that renders all six — prefer a small reusable method on `AgentFactory` for future regens.

Categories/agents (expected six):
- `contact` / `contact_specialist`
- `social` / `social_specialist`
- `relationships` / `relationships_specialist`
- `demographic` / `demographic_specialist`
- `professional` / `professional_specialist`
- `financial` / `financial_specialist`

Preserve AUTO-GENERATED headers and `created_at` may update to regen time (document in output).

---

## Exact steps (in order)

1. **Claim:** Move to `prompts/cursor/in-progress/2026-06-04-1200-specialist-template-sync-research/prompt.md`.

2. **Discovery:** Read 1100 done output; `grep -r threading src/agents/specialists/`; run smoke baseline.

3. **Update `specialist_agent.py.j2`:**
   - Remove `import threading` and thread start in `_start_research_if_needed`.
   - Replace stub with sync path:
     - Optionally write `pending` before call (for observability) or only on failure — align with plan; on **success** contrib must show `found`/`na`, not `pending`.
     - Call `run_field_research(category="{{ category }}", specialist_name="{{ agent_name }}", person_id=pid, target_fields=..., context=ctx, storage=storage)`.
     - Re-load record and re-evaluate fields for `specialist_contrib`.
   - Update module docstring: Phase 1 sync research; async deferred.

4. **Regenerate** all six `src/agents/specialists/*_specialist.py` from template (do not hand-edit logic except via template).

5. **Tests** — extend `tests/test_research.py` or add `tests/test_specialist_sync_research.py` (`@pytest.mark.smoke`):
   - Monkeypatch `run_field_research` on contact path: after invoke with `--attributes email`, storage contains `found` or `na` and contrib is not stuck on `pending` when mock returns `found`.
   - Use `MYCELIUM_AGENT_DATA_DIR=tmp_path` and existing graph/specialist test patterns from `tests/test_core_graph.py` / `test_supervisor_routing.py` as reference.
   - **Prove contact + email** explicitly in test name/docstring.

6. **Verification:**
   ```bash
   uv run pytest -m smoke -q tests/test_research.py tests/test_agent_factory.py
   uv run ruff check src/agents/factory src/agents/specialists src/tools/research.py tests/
   ```
   Grep: no `threading.Thread` in `src/agents/specialists/*_specialist.py`; no `langchain_tavily` / `TavilySearch` in specialists.

7. **Deliverables** in `prompts/cursor/done/2026-06-04-1200-specialist-template-sync-research/`.

---

## Scope boundaries (strict)

**May modify:**
- `src/agents/factory/templates/specialist_agent.py.j2`
- `src/agents/factory/agent_factory.py` (regen helper only — small)
- `src/agents/specialists/*_specialist.py` (regenerated output)
- `tests/test_research.py` and/or `tests/test_specialist_sync_research.py`

**Out of scope:**
- `src/tools/research.py` — only if a tiny fix required for wiring; prefer follow-up 1100 fix prompt
- Graph topology, supervisor, MCP, `PersonQuery`, `docs/architecture.md` (slice 1300)
- Live manual Tavily/OpenAI runs in CI

**Test policy:** Smoke only unless you add a full integration test (then run it).

---

**Next queue item:** `2026-06-04-1300-specialist-research-integration.md`