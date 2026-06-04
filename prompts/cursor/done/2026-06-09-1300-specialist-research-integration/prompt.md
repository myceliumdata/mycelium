# Task: Specialist Research Phase 1 — Slice 1300: Integration tests + docs

**Read these first (mandatory):**
- `docs/plans/specialist-research-phase1.md` (approved)
- `prompts/cursor/WORKFLOW.md`
- `docs/architecture.md`
- Prior done folders: `2026-06-04-1100-specialist-research-runner`, `2026-06-04-1200-specialist-template-sync-research`

**Depends on:** Slices **1100** and **1200** complete (sync research wired, six specialists regenned).

**Objective**

Add an integration-level test that a **single** `run_query` with a non-core attribute returns **`found` or `na` in the same response** when research is mocked (not `pending` forever). Update architecture docs to reflect implemented Phase 1 (sync research, Tavily, pointer to plan). Optional README sentence on demo latency vs future async.

**Agreed verification (from plan)**

- Mock `run_field_research` or LLM/Tavily at boundary so CI needs no keys.
- Query e.g. `person_key` from seed + `--attributes email` (or `x_handle` on social) → `results` include attribute with value or N/A messaging; not “not currently available” while mock returns `found`.
- Unset keys test: `is_research_available()` false → `pending`, no crash (smoke).

---

## Exact steps (in order)

1. **Claim:** `prompts/cursor/in-progress/2026-06-04-1300-specialist-research-integration/prompt.md`.

2. **Discovery:** Read 1100/1200 outputs; run `uv run pytest -m smoke -q` baseline.

3. **Integration test** in `tests/test_core_graph.py` or new `tests/test_specialist_research_integration.py`:
   - Mark `@pytest.mark.smoke` if fully mocked (preferred for default policy).
   - If the test uses real `run_query` + real storage under tmp, still mock research/LLM/Tavily.
   - Assert attribute-scoped `results` keys and `id` present.
   - Assert `message` is honest (not claiming unavailable when value returned).
   - Document test category in `output.md` (smoke vs full).

4. **Docs:**
   - `docs/architecture.md` — under “Next phases”, replace Tavily “scaffold/planned” wording with **implemented sync research** (brief), link `docs/plans/specialist-research-phase1.md`, note **async deferred**.
   - `README.md` — one short bullet under development or architecture: sync research on cache miss may slow queries; future async.

5. **Verification:**
   ```bash
   uv run pytest -m smoke -q
   uv run ruff check src tests
   ```

6. **Deliverables** in `prompts/cursor/done/2026-06-04-1300-specialist-research-integration/`.

---

## Scope boundaries (strict)

**May modify:**
- `tests/test_core_graph.py` and/or `tests/test_specialist_research_integration.py`
- `docs/architecture.md` (research paragraph only)
- `README.md` (minimal note)

**Out of scope:**
- New features in `research.py` or specialist template (fix bugs only with note)
- MCP / `PersonQuery` / graph topology changes
- `docs/plans/specialist-research-phase1.md` (except you may add “Implemented via slices 1100–1300” one line if Paul wants — optional)
- Slice 1400 polish (timeouts, extra env) unless trivial

**Test policy:** Smoke default; run full suite only if you add `@pytest.mark.full` tests.

---

**End of Phase 1 queue.** Optional follow-up (not in `next/` unless Paul asks): polish slice for timeout tuning and README async note expansion.