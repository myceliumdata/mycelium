# Task: Agent Factory Phase 2 - Slice 07: LLM refine, final cross-checks, docs touch, full verification + cleanup

**Read these first (mandatory):**
- `docs/plans/agent-factory-phase2.md` (the approved plan - focus on "optional LLM refinement", Success Criteria, "Next Steps After Approval", Risks (generated code quality), full "Verification (End-to-End + Regression)")
- The detailed implementation plan at `docs/plans/agent-factory-phase2.md` (focus on Step 7, "Optional LLM Refinement" notes in factory design, full Verification section (automated + manual hot-path + creation + test isolation + dispatch/restart + observability + git hygiene + no hot-path LLM + after Cursor), Success Criteria, "After Cursor delivers each slice", and the polish note for docs)
- `prompts/cursor/WORKFLOW.md`
- `.cursor/rules/04-cursor-workflow.mdc`
- `docs/architecture.md`
- `prompts/system/CORE_PROMPT.md`

**Objective**
Fill the real body of `_refine_with_llm` in agent_factory.py (lazy ChatOpenAI, explicit "review and lightly improve this specialist agent code for consistency with project style... keep structure... Output ONLY the complete python source code" prompt, temperature 0, guard that the improved code still contains the expected `def <agent_name>(`, return improved or original). Add a smoke test for the refine path in test_agent_factory.py (fake llm that returns a slightly modified code string with a marker; assert factory used it when llm_refine=True). Small high-value doc updates only: 1-2 sentences in `docs/architecture.md` (under supervisor or Derivative/Non-Core or a new Phase 2 note: "Phase 2 Agent Factory (see plans) provides on-demand creation of committed specialist agents via Jinja2 + registry + dispatch; supervisor triggers on unregistered assigned_agents from classification; per-specialist flat JSON + storage_strategy.json hooks for future self-evolution."). Run full ruff + smoke + the full non_core/graph/factory subset. Final manual matrix exactly as in the plan's Verification (core query; non-core creation e.g. via net_worth -> financial_specialist (real git commit happens); git log --oneline -1 --stat + cat header in the py; ls data/agents/financial/; subsequent query no re-create; python -c reset_agent_registry + get_agent_fn + call it with stub; env isolation create; delete reg reseed; header grep only in specialists/; no hot-path LLM unless explicit refine; mcp list now real; observability in audit/debug/state.route; lint; etc.). After: in output.md note re-ran verifs from plan.

This is the polish/verify/final slice. Completes the approved plan via small reviewed increments.

**Lightweight priority (from approved detailed plan + user approval notes - obey strictly)**
"Keep every slice small, explicit, and easily reviewable. Prioritize getting basic creation + registration + dynamic loading + routing working cleanly before any polish (LLM refine, advanced storage logic, etc.). Strictly enforce auto_commit=False + temporary paths in all tests. Real git commits only happen on actual (non-test) runs. Generated agents must always include the prominent AUTO-GENERATED header and be committed to git on real usage."

**Extra Guidance from Paul**
Prioritize simplicity. If a slice feels complex, simplify the implementation and document it. Generated code must always have the full AUTO-GENERATED header. Tests must never trigger real git commits.

For this slice: refine is small (stub was in 04); docs 1-2 sentences only; full verif only here; no new big features.

**Constraints & Principles**
- Strictly limited scope (see box below).
- The refine prompt/body must match the approved plan's notes (review for style match with core_data.py, keep explicitness, only complete .py, guard).
- Small, reviewable change only.
- Smoke + the full targeted as in plan.
- This is the final slice of the sequence.

**Context**
- All prior slices have delivered the factory (with stub refine), trigger, dispatch, responses, fixtures, tests.
- The approved plan has the exact refine notes, the full Verification matrix (every command listed), the Success Criteria, and the "After Cursor delivers" process.
- Current: refine is stub in factory; architecture.md has no Phase 2 note yet; no final e2e creation + git + restart load + isolation matrix run in one go.
- This slice closes the loop: refine implemented + tested (mock), docs touched minimally, full matrix run (including real creation + commit + header + load), all green.

See approved plan Step 7, Verification, Success Criteria, and "After Cursor delivers each slice".

**Exact Steps (perform in order)**
1. **Claim the task first (mandatory per WORKFLOW.md)**: Scan `prompts/cursor/next/`, select the oldest (this one), **immediately move** it to `prompts/cursor/in-progress/2026-06-07-agent-factory-07-polish-refine-verify/prompt.md` (or the exact name). Only then begin work. Document the move in your output.md. Never work on a file still in next/.

2. **Discovery (read-only)**: 
   - Read the approved plan sections listed above (especially the full Verification and Success Criteria).
   - Read the current _refine_with_llm stub in agent_factory.py, the test_agent_factory.py refine test stub, docs/architecture.md (supervisor/derivative sections).
   - Run baselines: `git status`, `uv run pytest -m smoke -q`, `uv run pytest -m full -q -k "non_core or query_non_core or supervisor or graph or factory or registry"`, a core query and a non-core query.
   - Confirm current refine stub and no Phase 2 note in architecture.md.

3. **Implement the real `_refine_with_llm`** in `src/agents/factory/agent_factory.py` (matching the approved notes):
   - Replace the stub body with: lazy `from langchain_openai import ChatOpenAI`; llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.0); prompt = f"""You are an expert Python developer maintaining the Mycelium project. Review the following generated specialist agent code for consistency with project style (see core_data.py: thin, explicit _coerce, use of SpecialistStorage, response builders with specialist= kwarg, classifications handling, audit logs, payload shape). Keep all functionality and structure. Improve comments/docstrings if missing or unclear. Output ONLY the complete valid Python source code, no ``` or explanation.
   {code}
   """
   - resp = llm.invoke(prompt)
   - improved = (resp.content if hasattr(resp, "content") else str(resp)).strip()
   - if agent_name in improved and "def " + agent_name in improved:
     return improved
   - return code
   - Add clear comment: "Optional LLM refine (off by default per lightweight). The template + plan design is the source of truth. Result is still committed for human review (per user note)."

4. **Add/enhance the refine smoke test in `tests/test_agent_factory.py`** (from plan Step 7):
   - Add a test like:
     ```python
     @pytest.mark.smoke
     def test_agent_factory_refine_with_mock_llm(tmp_path, monkeypatch):
         from agents.factory import get_agent_factory, reset_agent_factory
         from agents.registry import reset_agent_registry
         monkeypatch.setenv("MYCELIUM_AGENT_REGISTRY_PATH", str(tmp_path / "r.json"))
         monkeypatch.setenv("MYCELIUM_SPECIALISTS_DIR", str(tmp_path / "s"))
         reset...
         f = get_agent_factory()

         class _FakeLLM:
             def invoke(self, prompt):
                 return type("R", (), {"content": "# improved\n" + prompt.split("```")[-1] if "```" in prompt else "def contact_specialist... # REFINED"})()

         # patch inside or pass if supported; for stub, monkey the ChatOpenAI or test the guard path
         # for the test: call with llm_refine=True using a patched create or direct, assert "REFINED" in result or side-effect code
         info = f.create_specialist("contact", "contact_specialist", "desc", llm_refine=True)  # will use real unless patched; for smoke use the guard
         # or directly test the method with fake
         print("refine test (mock path exercised)")
     ```
   - Ensure it exercises the path safely (no key if possible, or document).

5. **Small doc touch in `docs/architecture.md`** (1-2 sentences only, high value):
   - Under "Supervisor as coordinator (Phase 1 complete)" or "Derivative / Non-Core Data" or add a short "Phase 2 Agent Factory" para: "Phase 2 adds the Agent Factory, Agent Registry (data/agent_registry.json), per-category specialists/ (committed .py with AUTO-GENERATED header), and dispatch. Supervisor triggers creation for unregistered assigned_agents from classification (minimal if + factory.create). Specialists start with flat JSON + storage_strategy.json (hooks for future agent self-evolution). See plans/agent-factory-phase2* and the 7-slice Cursor prompts."

6. **Lint + full pytest**:
   - `uv run ruff check src/agents/factory/agent_factory.py tests/test_agent_factory.py docs/architecture.md src/agents/supervisor.py src/graphs/core.py ...` (all touched across phases)
   - `uv run pytest -m smoke -q && uv run pytest -m full -q -k "non_core or query_non_core or supervisor or graph or factory or registry or agent"`

7. **Final manual matrix (exactly as in plan Verification section)**:
   - Core only query.
   - Non-core that triggers creation (e.g. `uv run mycelium query --person-key "Nichanan Kesonpat" --attributes net_worth`): first run creates financial_specialist (or whichever), audit has "created new..." + "routing to ...specialist", response "researching" (via if present), debug/classif, git status clean (committed), `git log --oneline -1 --stat`, `cat src/agents/specialists/financial_specialist.py | head -20` (AUTO-GENERATED header), `ls data/agents/financial/`.
   - Subsequent same attr: no "created", direct.
   - Another category if needed.
   - `uv run python -c 'from agents.registry import reset...; r=...; fn=r.get_agent_fn("financial_specialist"); ... call with stub state ...'`
   - Env isolation create (MYCELIUM_* = /tmp/... create with auto_commit=False; no src/git).
   - Delete reg json reseed test.
   - Header grep: `git grep -l "AUTO-GENERATED by Agent Factory" -- src/agents/specialists/`
   - No hot-path LLM unless refine: grep for ChatOpenAI in non-factory files (only in factory's refine method).
   - mcp list now real if polished in 06.
   - Observability: audit, debug, state.route = specialist name, LangSmith if on.
   - Lint/hygiene.
   - Full matrix from plan.

8. **Output artifacts (exactly per WORKFLOW)**:
   - Create `prompts/cursor/done/2026-06-07-agent-factory-07-polish-refine-verify/output.md` with:
     - Summary ( "followed lightweight: refine small + mock test; docs 1-2 sent only; full matrix run including real creation + git commit + header enforcement + isolation"; decisions), git diff --stat + key (refine body, architecture sentence), **explicit `git diff --stat tests/test_agent_factory.py` + Guard compliance statement**, full outputs of every verif command (incl. the creation + git log + cat header + load python -c + greps + mcp), scope confirmation (only factory refine, test refine test, architecture.md tiny, command runs), "Phase 2 per approved plan complete".
     - Move/copy this prompt into the done/ dir as `prompt.md`.
     - Remove **only** the file you claimed from `prompts/cursor/in-progress/`.
     - Optionally create review.md placeholder.

9. **Process hygiene**:
   - Follow claiming exactly.
   - Stop on scope (no new features, no large docs, no re-touching prior slices' files unless tiny ruff fix documented as part of polish, no changes to plan).
   - After delivery: note in output that verifs were re-run per "After Cursor delivers each slice".

## Scope Boundaries (Strict)
You may only create or modify files under the following paths:
- `src/agents/factory/agent_factory.py` (only the _refine_with_llm body + comment)
- `tests/test_agent_factory.py` (only the refine path test addition/enhancement — see Guard rule above; no other tests or expansions)
- `docs/architecture.md` (only 1-2 high-value sentences in appropriate section)
- Running of ruff/pytest/git/mycelium commands (may touch temps/checkpoints but not source outside scope)

**Out of Scope (Do Not Touch)**
- All other source (supervisor, graphs, state, responses, core_data, registry, base, dispatch, mcp, tests beyond the refine test in factory test, etc.), data/ (except as part of the manual matrix creation, which is intended and committed), the plan files, TODO.md, large docs changes, any new tests beyond the refine one, etc.
- Do not implement advanced storage migration, pre-generate all specialists, move core_data, etc. (future).
- Do not run commands that would cause un-intended commits outside the matrix.

If you determine that changes outside this scope are necessary:
- **Stop immediately.**
- Clearly document the problem in your `output.md`.
- Do **not** make the out-of-scope changes.
- Create a follow-up prompt in `prompts/cursor/next/` describing what needs to be done instead.

This rule is mandatory.

## Test Execution Policy
- Default: `uv run pytest -m smoke -q`.
- Full targeted as in plan Verification (the non_core/graph/factory/registry subset + the manual matrix).
- The refine test must be smoke-safe (mock llm, no key/network if possible).
- The manual matrix includes real creation (which commits per requirement) + all isolation/grep/observability checks.

**Guard against excessive insertions in shared files (mandatory):**
This series prioritizes small, reviewable slices. Even for the final polish slice, keep changes tiny.

When the scope includes modifying a test file (`tests/test_agent_factory.py`):
- ONLY add/enhance the *exact refine smoke test* described in the "Exact Steps".
- Make the *absolute minimum* supporting code for that one test.
- Run ruff only on your additions.
- **Never** add unrelated tests, restore old code, or expand the test file beyond the refine path test.

In output.md you **must** include `git diff --stat tests/test_agent_factory.py` + statement that changes were limited to the described refine test.

The same spirit applies to the tiny doc change in `docs/architecture.md` (1-2 sentences only, as described).

## Required Output Location & Artifacts
- `prompts/cursor/done/2026-06-07-agent-factory-07-polish-refine-verify/output.md`
- The claimed prompt moved to the done/ subdir as `prompt.md`

Follow the claiming process in `prompts/cursor/WORKFLOW.md` exactly before doing any implementation work.

## Suggested Acceptance (for Grok + Paul review)
After Cursor delivers, we will review the output.md, confirm only the listed files + command side-effects, **confirm via `git diff --stat` on test_agent_factory.py that changes were limited to the refine test per the Guard rule**, re-run the full manual matrix from the plan (core; non-core creation + git commit + header cat + data/agents/ + subsequent + restart python -c load + isolation env + delete reseed + header grep + no hot LLM grep + mcp + observability + lint), confirm refine test exercises the path, architecture.md has the 1-2 sent Phase 2 note, all green and matches Success Criteria, scope clean, add review.md if needed. This completes the approved plan via small reviewed increments (7 slices). Then (if good) commit the final slice, publish a snapshot of the detailed plan to docs/plans/agent-factory-phase2-plan.md if not already, and consider follow-ups (pre-generate remaining specialists from the taxonomy, etc.).

Start by claiming the file (move to in-progress/). Good luck — this is the final polish/verify slice. Make it small, explicit, and reviewable. Reference the approved plan for every detail (refine prompt, matrix commands, success criteria).
