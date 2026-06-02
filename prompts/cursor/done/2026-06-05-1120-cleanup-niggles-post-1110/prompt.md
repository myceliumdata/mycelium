# Task: Cleanup niggles (docs alignment, tmp/, reset refresh, checkpoint warnings) after 1110

## Objective
The 1110 final cleanup + review identified several small but visible inconsistencies ("niggles") that prevent docs and helper files from accurately reflecting the completed query-only + core_data_agent reality. Fix them so a new reader (or a fresh session starting by reading the context reset) sees a consistent, up-to-date picture with no "wiring still in progress", "pending 1070/1100", "transitional", or old ingest-era instructions. Also eliminate the noisy "Deserializing unregistered type models.state.* from checkpoint" warnings that appear during verification smokes and CLI runs. Polish the supporting files (docs, tmp, resets, TODO, run script, minimal graph code) without changing behavior or scope.

**Primary references for the list of niggles:**
- `prompts/cursor/done/2026-06-05-1110-final-cleanup-and-verification/review.md` (especially "Issues / Misses" and the architecture/full-walkthrough excerpts).
- This task's own prompt (for self-reference during execution).

See `docs/architecture.md` (the active source of truth), `TODO.md`, `docs/full-code-walkthrough.md`, and the 1110 output.md for context.

## Constraints
- **Strictly post-1110 cleanup only.** Do not re-introduce public ingest, `provided_data`, CLI `ingest`, MCP `submit_person_data`, or re-wire legacy agents.
- Do **not** delete the legacy `enrich.py`/`validator.py`/`person_prep.py` files (their docstrings were updated in 1110; they stay for future internal addition work).
- Do **not** edit historical artifacts under `prompts/cursor/done/` (they are the audit record; the 1110 review.md already documents the state of the niggles at review time).
- Keep all edits small, reviewable, and narrowly scoped to docs, tmp/, context reset(s), TODO.md, `bin/run-studio`, and a minimal supporting change in `src/graphs/core.py` (for the warning).
- Do not touch tests beyond running them for verification, and do not alter agent/graph logic.
- After fixes, the primary context reset must be accurate for "fast context load for fresh sessions" (as the original 2026-06-02_mvp_reset_final.md was used at the start of this conversation).
- Claim the task first (move this file from `next/` to `in-progress/`) before any edits.

## Exact Steps
1. **Claim the task (per WORKFLOW.md).** Immediately move this file from `prompts/cursor/next/2026-06-05-1120-cleanup-niggles-post-1110.md` to `prompts/cursor/in-progress/2026-06-05-1120-cleanup-niggles-post-1110.md`. This is the lock for parallel safety. Do not touch any other files in in-progress/.

2. **Discovery / global search.** Run greps (and `rg` if available) for the outdated phrases across the live tree (exclude `prompts/cursor/done/**`, `**/.git/**`, and `src/mycelium.egg-info/**`):
   - "in progress (tasks 1070/1100)"
   - "pending (1070/1100)"
   - "Target (1070/1100)"
   - "until task 1070"
   - "Routing still performs lookups inline today"
   - "not yet the default path"
   - "until fully wired"
   - "Compiled today (transitional)"
   - "graph wiring from supervisor → core_data is pending"
   - "Legacy **enrich** / **validator** nodes may still appear"
   - "provided_data" + "ingest" + "enrich step" (in tmp/ and resets/ only; ignore historical done/)
   - Also search for "Deserializing unregistered type" to locate recent occurrences.
   Document the hits in your output.md. Only the locations in `docs/`, `tmp/`, `prompts/resets/`, `bin/`, and `src/graphs/core.py` (plus TODO) are in scope.

3. **Fix `docs/architecture.md`.** 
   - Replace the entire "### Supervisor as coordinator (Phase 1 progress)" subsection (approximately lines 58-69) with accurate post-1110 text. Suggested replacement (adapt minimally for flow):
     ```
     ### Supervisor as coordinator (Phase 1 complete)
     
     The **supervisor node** (`src/agents/supervisor.py`) is a thin coordinator and router:
     
     - It evaluates the inbound `PersonQuery` (person_key + optional requested_attributes) and emits a `route` decision plus audit log. For the current public query-only surface it always routes to the core specialist (`route="core_data"`).
     - Classification, core lookup via `CoreIdentity`, and construction of the minimal `PersonResponse` (`results`, `message`, `debug`, `trace_id`, `thread_id`) are performed by the specialist.
     - **Core data specialist** — `src/agents/core_data.py` defines `core_data_agent`, the LangGraph node that owns core CRM lookups (`find_by_key` via `CoreIdentity`). Wiring supervisor → `core_data_agent` (with the conditional edge in `graphs/core.py`) was completed in tasks 1070/1100 and the final alignment pass was 1110.
     - **CoreIdentity** — `src/agents/core_identity.py` is the storage facade used by `core_data_agent` (and available for future specialists).
     
     Legacy **enrich**, **validator**, and **person_prep** modules remain on disk as *unwired legacy* (see the module docstrings in those files). They are not imported by `src/agents/__init__.py` and are not present in the compiled public graph. They are reserved exclusively for future internal agent-coordinated data addition (see TODO.md "Re-adding data addition").
     
     Full specialist-agent routing for non-core attributes is still future work. When a query requests non-core attributes, the core record (if present) is returned and the `message` field contains a narrative (e.g. "we're still researching X").
     ```
   - Update the "Last major update" footer at the end of the file to mention the 1120 niggle cleanup (e.g. "June 2026 (query-only migration 1000–1110 + niggle cleanup 1120)").
   - Run a targeted grep afterward to confirm the old "in progress" / "until task 1070" sentences are gone from this file.

4. **Fix `docs/full-code-walkthrough.md`.** Perform targeted, minimal replacements in the following sections (read the current text first so your diff is reviewable). Provide before/after excerpts in output.md.
   - "Current reality (June 2026):" bullets (top of file) — remove "pending (1070/1100)", "Routing still performs lookups inline today", "removal is task 1070".
   - Section 5 "Graph runtime" — remove the "Compiled today (transitional)" line or mark it historical. Change "Public query path today" description to the real current path. Change the "**Target (1070/1100):**" header to "**Achieved (1070/1100, finalized 1110):**" and update the parenthetical.
   - Section 6 "Supervisor & routing" — update the description of `supervisor_agent` (it is now a very thin coordinator that only returns the route + audit; it does not call `evaluate_supervisor_turn` directly). Note that `routing.py` supplies shared helpers used inside `core_data_agent` and by tests.
   - Section 7 — remove "Not yet the default path in the compiled graph (supervisor/routing still inline)".
   - Section 8 "CoreIdentity facade" — remove "Used by `core_data_agent` and routing until wiring is complete."
   - Section 12 "Query flow" — update the ASCII diagram so the "current" path is supervisor → core_data_agent (remove the [today] / [target] distinction or mark the old one as pre-1110).
   - Section 14 "Gaps / next tasks" — replace the wiring items with the current open items from TODO.md (the "Continue reducing inline routing lookups in `routing.py`..." and "Further narrow response construction..." bullets, plus the re-adding section and other near-term items). Keep the reference to TODO.md.
   - Section 15 "Mental model" — update the diagram (remove [today]/[target] or make the target the current achieved state).
   - Footer "Last major refresh" — update to include 1120.
   - Any other incidental stale references you find while editing.
   - After edits, grep the file to confirm the phrases from step 2 are gone.

5. **Fix `tmp/restart-server-for-schema.md`.**
   - Rewrite the outdated final paragraphs (starting around "Now the Input editor (when adding Person under provided_data)...") so they are accurate for the query-only interface.
   - Use current terminology and reference the examples in `tmp/studio-inputs.md` (the "query" object containing "person_key" + optional "requested_attributes").
   - Remove all mentions of "provided_data", "new ingests", "enrich step will generate the id", and "ingest test input".
   - Keep (and lightly polish if helpful) the core advice that the running server process must be restarted after model edits because Studio schemas come from the live process.
   - Add a small header note or comment at the top: "Updated during 1120 niggle cleanup for the query-only public interface (no more ingest paths)."
   - Verify that `tmp/studio-inputs.md` and `tmp/studio-input-guide.md` are already clean (they should be after 1110) and reference them correctly.
   - Confirm after edit that greps for ingest/ provided_data in this file are either gone or only in a historical "previously" note if you add one.

6. **Address the checkpoint deserialization warnings (the "Deserializing unregistered type models.state.Person* from checkpoint" messages).**
   - Reproduce the warning: run a smoke that exercises checkpointing (e.g. `uv run mycelium query --person-key "Nichanan Kesonpat" --thread-id "niggle-test-1120"` or a direct `run_query` with a stable thread_id, or the python -c from previous reviews). Capture the output.
   - Implement a minimal, non-breaking fix. Recommended starting point (test and adjust):
     - In `src/graphs/core.py`, early (after the imports, before any `_setup_async_checkpointer` or `get_core_graph` eager call), add:
       ```python
       # Allow our Pydantic models to be deserialized from LangGraph's SQLite
       # checkpoints (AsyncSqliteSaver). Without this, runs that load prior
       # thread state emit noisy warnings:
       #   "Deserializing unregistered type models.state.PersonQuery from checkpoint..."
       # See warnings observed during 1110/1120 verification runs.
       import os
       os.environ.setdefault("LANGGRAPH_ALLOWED_MSGPACK_MODULES", "models.state")
       ```
     - Also export/set the same env in `bin/run-studio` (near the top, before the LANGCHAIN_TRACING_V2 line) and any other entry points that start the graph (e.g. tests already do resets but a top-level set is fine).
     - If the env var alone is insufficient in this LangGraph version, investigate the saver constructor or a small serde config and implement the smallest working change. Add a clear comment.
   - Re-run the smoke(s) and confirm the "Deserializing unregistered type" lines no longer appear in the captured output (other warnings such as LangSmith sandbox notes are acceptable if pre-existing).
   - Document the exact change and verification output.

7. **Refresh the context reset file(s).**
   - Edit the active compact reset `prompts/resets/2026-06-02b_mvp_reset.md`:
     - Bump **Last Updated** and any internal Date.
     - Update the "## Current Task" section:
       - Next Objective: now points to the remaining supervisor/specialist follow-ups from TODO (e.g. "Continue reducing inline routing lookups in `routing.py`...", "Further narrow response construction...", plus items from "Re-adding data addition" and "Observability").
       - Update the success criteria list so the niggle-cleanup items from this task are checked (docs now aligned, tmp/ cleaned, reset refreshed, warnings addressed).
       - Update "Relevant Files / References" and "Suggested Approach" to mention this 1120 task + the 1110 review.
     - Keep the overall compact structure and "Must-Read Files" section (it should still list architecture.md first, etc.).
   - Because the session-start reset read at the very beginning of work was `prompts/resets/2026-06-02_mvp_reset_final.md` (which is no longer present on disk), also create a fresh canonical version at `prompts/resets/2026-06-05_mvp_current.md` (or similar dated name) using the compact style and full section structure from that earlier file (Vision & Core Philosophy, Phase 1 MVP, Collaboration & Cursor Workflow, Must-Read Files, Working Principles, Current Task). Populate "Current Task" with the post-1120 state. This gives future sessions (or Paul) a single up-to-date file to `cat` for context.
   - If the resets/ dir now has clearly obsolete pre-migration files that add confusion, you may move them into a new `prompts/resets/archive/` subdirectory (or simply leave them — prefer the least destructive option and document the choice).

8. **TODO.md and any incidental updates.**
   - If the fixes surface tiny new items, add them under the appropriate section (keep the spirit of the existing "Continue reducing..." note).
   - Otherwise just ensure the last-updated style comment is reasonable.
   - Do not expand scope into new features.

9. **Final verification (must all pass cleanly).**
   - `uv run ruff check src tests`
   - `uv run pytest -q`
   - CLI smoke: `uv run mycelium query --person-key "Nichanan Kesonpat"`
   - MCP smoke (import + one `query_person` call)
   - A direct python smoke that exercises a thread_id (to hit checkpoint) with tracing off, capturing stdout and confirming no "Deserializing unregistered type" lines.
   - The specific graph path test: `uv run pytest tests/test_core_graph.py::test_graph_invokes_supervisor_then_core_data -q --tb=no`
   - Post-edit greps (live files only) for all the outdated phrases from step 2 — they must be absent from `docs/`, `tmp/`, and the active reset(s).
   - `git status --porcelain` or equivalent to show only the expected files changed.
   - Re-read the key sections of architecture.md and full-code-walkthrough.md to confirm they now read as "complete / achieved / current state".

10. **Deliver the artifacts.** Create the directory `prompts/cursor/done/2026-06-05-1120-cleanup-niggles-post-1110/` (use the exact slug of this prompt file). Place:
    - A copy of this prompt as `prompt.md`.
    - `output.md` containing:
      - Bullet list of every file touched + one-line summary of the change.
      - Key before/after excerpts (especially the rewritten supervisor section and the tmp paragraphs).
      - Full stdout/stderr from all verification commands in step 9.
      - The final declarative statement: "Niggles cleaned. `docs/architecture.md`, `full-code-walkthrough.md`, `tmp/`, and the primary reset(s) now accurately describe the query-only public interface with core data owned by the `core_data_agent` (post 1110 + 1120). Checkpoint warnings addressed in normal operation."
      - Any follow-up prompts you created for larger remaining items.
    - Optionally a `review.md` placeholder.
    - **Remove only this claimed file** from `in-progress/`. Never touch other in-progress entries.

## Required Output Artifacts
- `prompts/cursor/done/2026-06-05-1120-cleanup-niggles-post-1110/output.md` (as detailed above).
- All live files (docs, tmp, resets, etc.) left in a state where a new person or session reading the reset + architecture.md gets zero surprises about "still pending" wiring or old ingest flows.
- The primary reset file(s) updated so that "Current Task" accurately drives the next real work (routing reduction, response narrowing, internal addition design, LangSmith E2E, etc.).

**Scope boundaries (strict):** Only the files and changes described. If you discover something truly out of scope that blocks correctness, stop, document it in `output.md`, and create a follow-up prompt in `next/` rather than hacking around it.

Claim the file, execute the steps, deliver cleanly, then remove only your in-progress claim. Produce small, reviewable diffs.

Good luck — this is the polish pass that makes the post-migration docs trustworthy.