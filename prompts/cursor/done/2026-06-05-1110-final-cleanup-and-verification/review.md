# Review: Task 1110 — Final cleanup, verification, and TODO/architecture alignment after query-only + core data agent migration

**Reviewer:** Grok  
**Date:** 2026-06-05  
**Artifacts:** `prompt.md`, `output.md` (review.md added now)

---

## Objective Recap
Final pass to remove any remaining public ingest/add references after the 1000–1100 migration series. Global grep + targeted cleanup in src/tests/docs/tmp. Run full verification (ruff, pytest, CLI/MCP/graph smokes). Update TODO + docs (architecture, full-code-walkthrough) where they still described old behavior. Leave the project in a clean "queries only, core data owned by `core_data_agent`" state. Legacy enrich/validator/person_prep stay on disk but unwired.

**Required statement in output:** "Project is now query-only public interface with core data managed by the CoreDataAgent."

---

## Changes Delivered (from `git diff` + output.md)
- **TODO.md**:
  - Wiring item marked `[x] Wire core_data_agent into graph; supervisor routes to it (1070, 1100)`.
  - Updated follow-up: "Continue reducing inline routing lookups in `routing.py` now that core data node owns lookups."
  - Last updated: 2026-06-05 (query-only migration complete; task 1110).
- **src/agents/enrich.py, validator.py, person_prep.py**:
  - Module docstrings updated to "** (unwired legacy)**", "Reserved for future internal data-addition coordination. Not imported by `agents.__init__` or `graphs.core`. Do not use from public CLI/MCP paths."
  - One helper docstring clarified as "legacy addition path".
  - (Note: `__init__.py` cleanup also appears in this diff — it was the primary 1100 delta but carried here.)
- **tmp/**:
  - Removed: `ingest-example.json`, `studio-correct-input.json`, `studio-add-person-guide.md` (misleading ingest teaching files).
  - Added/updated: `tmp/README.md` (documents the removal and future internal addition), rewrote `studio-inputs.md` / `studio-input-guide.md` for current query + non-core use.
- **prompts/resets/2026-06-02b_mvp_reset.md**: Updated "Current Task" / success criteria to reflect 1110 complete; next objective now "Pick the next item from `prompts/cursor/next/`".
- **Other**: No functional code changes. Global clean claimed in src (only legacy), tests (only negative regression guards), README, docs (per 1090 prior work).

Cursor's `output.md` contains the required clear statement and a migration summary table.

---

## Verification Performed (independent re-check)
1. **Grep for stragglers** (public ingest / provided_data / submit / enrich_agent / validator_agent):
   - `src/`: Only inside the three legacy unwired files (function names + one internal `provided_data` reference in old enrich logic) + generated `egg-info/PKG-INFO`. No active code paths.
   - `tests/`: Only the two intentional negative asserts in `test_supervisor_routing.py` (`"ingest" not in ...`, `"provided_data" not in ...`) as regression guards for not-found messages. Good.
   - `docs/`: Historical/negative references only (e.g. "no public ingest guidance", "Public ingest ... was removed June 2026. Planned return: internal..."). Vision-level "ingestion" mentions in architecture overview are high-level capabilities, acceptable.
   - `tmp/`: Explanatory only (README notes removal; one negative in studio-inputs.md). See findings below.
   - `prompts/cursor/done/`: Historical task records — expected and useful for audit. No problem.
   - Root `README.md`: Clean.

2. **Linter + tests**:
   - `uv run ruff check src tests` → **All checks passed!**
   - `uv run pytest -q` → **22 passed in ~0.3s**
   - Specific path test: `tests/test_core_graph.py::test_graph_invokes_supervisor_then_core_data` → **passed** (confirms supervisor audit "routing to core_data" + core_data_agent execution + response).
   - Other relevant: `test_supervisor_agent_routes_to_core_data` (thin supervisor), core_data_agent unit tests all green.

3. **Smokes** (attempted; env/DB/LangSmith timing can be slow in this session — relied on fast pytest path + prior successful runs):
   - Direct `run_query(PersonQuery(person_key="Nichanan Kesonpat"))` exercises the full supervisor → core_data path (covered by the passing test above).
   - Historical manual CLI/MCP smokes in this session (and Cursor's reported output) succeeded with correct core record, "Found core record..." message, `trace_id`/`thread_id`, etc.
   - MCP import + `query_person` surface remains query-only (`query_person`, `list_specialist_routing`).

4. **Graph wiring final verification**:
   - `graphs/core.py`: `START → supervisor` (sets `route="core_data"`) → conditional → `core_data` → `END`.
   - `supervisor.py`: pure coordinator, no data access.
   - `core_data.py`: owns `CoreIdentity.find_by_key` + response builders.
   - `agents/__init__.py`: exports only the two active agents.
   - Matches architecture intent and 1100/1070 work.

5. **File hygiene**:
   - `in-progress/` empty (Cursor correctly cleaned its claim).
   - Legacy files present but not imported/wired (confirmed via grep + package imports).
   - No re-introduction of public add paths (CLI only `query`/`seed`; MCP only `query_person` + stub).

---

## Findings & Assessment

**Strengths / What went well:**
- Clear "Project is now query-only..." statement delivered.
- Good tmp hygiene on the obvious ingest teaching files + helpful README.
- Legacy modules correctly annotated without being deleted (per constraints).
- TODO updated, including a forward-looking note on `routing.py`.
- Tests provide solid regression guards.
- Scope respected: no deletion of legacy files, no re-adding public ingest, small focused edits.
- Migration summary table in output.md is useful historical record.

**Issues / Misses (non-blocking but should be addressed soon):**
1. **Stale language in key docs (architecture.md + full-code-walkthrough.md)**:
   - `docs/architecture.md:64`: "Wiring supervisor → `core_data_agent` in the graph is in progress (tasks 1070/1100); today routing still performs lookups inline inside the supervisor path."
   - `docs/architecture.md:67`: "Legacy **enrich** / **validator** nodes may still appear in the compiled graph until task 1070 removes them..."
   - `docs/architecture.md:65`: "...used by `core_data_agent` (and routing until fully wired)".
   - `docs/full-code-walkthrough.md`: Multiple "graph wiring ... is pending (1070/1100)", "Not yet the default path", "Target (1070/1100):", "Routing still performs lookups inline today", and transitional graph descriptions.
   - 1110 prompt explicitly called for checking and cleaning these (even after 1090 docs task). Cursor marked "docs aligned" in the b_reset success criteria but did not update the "in progress / pending / today" phrasing to past tense or "completed via 1070/1100/1110".
   - `routing.py` description in arch is now inaccurate for the *active* public query path (it is test-only / duplicated logic).

2. **`tmp/restart-server-for-schema.md` left in misleading state**:
   - Still refers to "provided_data", "new ingests", "the enrich step will generate the id", "send the ingest test input again (use the one in tmp/studio-inputs.md)".
   - This was one of the files the 1110 prompt specifically flagged for update/delete if teaching old ingest usage. It was not touched (only the other three ingest examples + two studio guides + new README).
   - Recommendation: delete, rename to something like `restart-server-for-schema-query-only.md`, or heavily rewrite for current `PersonQuery` (no provided_data).

3. **Original reset file**:
   - `prompts/resets/2026-06-02_mvp_reset_final.md` (the one loaded at the start of this conversation for context) is no longer present in the tree. Cursor updated the `b` variant. If this was intentional "final" refresh, the deletion should be noted; otherwise it may have been an accidental straggler removal.

4. **Minor / pre-existing**:
   - Generated `src/mycelium.egg-info/PKG-INFO` and `SOURCES.txt` still describe old ingest/MCP surface and graph. (Rebuild with `uv pip install -e .` or equivalent after final commit.)
   - Occasional "Deserializing unregistered type ..." warnings from checkpoints (seen in long-running smokes); unrelated to 1110.
   - `bin/run-studio` has an unrelated prior edit (Studio restart note).
   - `routing.py` + its test still exist and duplicate lookup logic (TODO now calls this out for future reduction — correct observation).

**Overall:** The task largely succeeded in the spirit and in the mechanical verifications + tmp/legacy marking / TODO update. The "queries only + CoreDataAgent owns core" state is real and verified. However, the prompt's explicit instruction to clean stragglers in architecture.md and full-code-walkthrough.md (and tmp misleading files) was only partially executed. The success criteria in the updated reset claim "docs aligned," but they are not fully current.

**Recommendation:** 
- Accept the core of the work (the statement is fair; project *is* in the desired state functionally).
- Create a small follow-up prompt (or have Cursor do a quick pass) to:
  1. Update the stale "in progress"/"pending"/"until 1070" sentences in `docs/architecture.md` and `docs/full-code-walkthrough.md` to reflect completion.
  2. Clean or archive `tmp/restart-server-for-schema.md`.
  3. Optionally regenerate egg-info or note it in a build step.
- Refresh the main context reset (the _final one that was read earlier) if its absence was unintended.
- The next work after 1110 should focus on the items now listed in TODO under "Continue reducing inline..." and the "Re-adding data addition (internal / future)" section.

**Project is now query-only public interface with core data managed by the CoreDataAgent.** (Functional truth holds even if a couple of docs strings lag.)

---

(Review written after independent greps, test/lint runs, path verification, and diff inspection. If adjustments needed or you want me to produce the follow-up prompt for the doc/tmp nits, say the word.)
