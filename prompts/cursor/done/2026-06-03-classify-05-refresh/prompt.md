# Task: Classification Engine Phase 1 - Slice 05: Implement LLM refresh path (off hot path, lightweight, safe)

**Read these first (mandatory):**
- `docs/plans/classification-engine-phase1.md` (approved plan - focus on Step 5 "Add the LLM refresh path", the full `refresh_from_llm` sketch in the CategoryTree design (prompt, with_structured_output, conservative merge 0.7, additive only, metadata update, atomic save), the "Safe Mechanism for Occasional LLM-Based Tree Updates", the grep enforcement, the smoke test for refresh (mocked), lightweight note)
- `prompts/cursor/WORKFLOW.md`
- `.cursor/rules/04-cursor-workflow.mdc`

**Objective**
Implement the `refresh_from_llm` method in the CategoryTree (the only place LLM is ever used for classification). It must be completely separate from hot path (supervisor, core_data, run_query, MCP never call it). Use the exact logic from the approved plan: lazy ChatOpenAI, the careful prompt (current cats + attrs to consider), structured output with CategoryProposal, conf >=0.7 only, never delete existing, add new cats conservatively, update last_updated/model_used, _save + _load, return changes dict.

Add a safe smoke test that exercises the merge logic without real LLM (mock or early-return/known case).

This slice is deliberately last for the "evolution" piece, per the lightweight priority (core classify + injection first).

**Lightweight priority (obey)**
Get the core working cleanly first (already done in prior slices). For refresh: implement the body, but keep any polish (e.g. if atomic save was left simple) minimal.

**Constraints & Principles**
- Scope narrow (see box).
- The implementation must match the approved design exactly (the prompt text, the merge rules, the structured_llm = llm.with_structured_output(list[CategoryProposal]), etc.).
- **Never** make refresh callable from hot path code.
- Smoke test must not make real LLM calls (use monkeypatch or test only non-LLM paths like "all known").
- Grep enforcement will be part of verification.
- Part of small sequence.

**Context**
- Prior slices: engine basic (02), supervisor injection (03), propagate (04).
- refresh is the "occasional / admin-only path" for evolving the tree when unknowns appear in logs.
- Invocation is manual: python -c 'from agents.classification... ; t.refresh_from_llm(["kids", "net_worth"])' (requires key for real call).
- The approved plan has the full prompt string example and the changes dict logic.
- Hot path must have zero LLM imports/calls (enforced by grep in final verification).

See the exact code sketch in the approved plan's engine.py CategoryTree section for refresh_from_llm, and the "No hot-path LLM guarantee" verification.

**Exact Steps (perform in order)**
1. **Claim**: Move to in-progress/ immediately. Document.

2. **Discovery**:
   - Read the approved plan Step 5 and the refresh sketch in the design.
   - Read current engine.py (from slice 02).
   - Confirm prior slices' state (e.g. a manual classify still works).
   - Note the current big prompt is superseded.

3. **Implement refresh_from_llm in engine.py**:
   - Fill the method body exactly per approved sketch:
     - if llm is None: from langchain_openai import ChatOpenAI; llm=...
     - Build current_cat_names, current_map, attrs_to_consider (skip already known).
     - If none, return early with reason.
     - The prompt = f"""...""" (use the exact conservative prompt from the approved design section).
     - structured_llm = llm.with_structured_output(list[CategoryProposal])
     - proposals = structured_llm.invoke(prompt)
     - Then the loop: for p in proposals, normalize, if conf < 0.7 skip, if new cat create Category(description=..., assigned_agent=..., examples=...), always set attribute_map, track changes.
     - Update last_updated = datetime.now(timezone.utc), model_used = model
     - self._save(); self._load()
     - return changes
   - Add the clear comment at top of method or module: "refresh_from_llm is the ONLY place that may import or call an LLM for classification. It must never be called from supervisor, core_data, graphs, mcp, main, or any query path."
   - Make sure no top-level import of langchain in the file (lazy inside the method).

4. **Add safe smoke test for refresh (non-LLM)**:
   - In a suitable smoke test file (e.g. extend in test_supervisor_routing.py or the engine test area), add a test that calls refresh with attrs that are already known (expects the early "all already known" return, no LLM).
   - Or use monkeypatch to replace the llm creation/invoke for a case that would propose something.
   - Explicitly: the test must not require OPENAI_API_KEY and must not make network/LLM call.

5. **Verification for this slice**:
   - `uv run pytest -m smoke -q`
   - The grep from approved: `git grep -n "ChatOpenAI\|refresh_from_llm\|langchain.*chat\|invoke.*llm" -- src/agents/supervisor.py src/agents/core_data.py src/graphs/ src/mycelium_mcp/ src/main.py src/models/ | cat`
     - Must show hits *only* inside classification/engine.py (the method).
   - Manual off-path (if you have key): the python -c refresh example from approved plan, then classify the new attr sees the update. (If no key, just test the early return path.)
   - Confirm the test for refresh is smoke and doesn't call LLM.
   - Re-confirm a normal query with attrs still works fast (no LLM on hot path).
   - git changes only in scope for this slice (mainly engine.py + test addition).

6. **Output**:
   - done/2026-06-03-classify-05-refresh/output.md : summary ( "implemented exactly per approved sketch; refresh is off-path only; smoke test uses no-LLM path" ), full outputs of grep, smoke, manual (early return + any real if done), diffs for this slice, confirmation of the "ONLY place" comment and grep.
   - prompt.md .
   - Remove only your claim.

**Scope Boundaries (Strict)**
You may only modify:
- `src/agents/classification/engine.py` (the refresh method + comment)
- `tests/test_supervisor_routing.py` (or whichever smoke file you choose for the refresh smoke test addition)

**Out of Scope (Do Not Touch)**
- All previous slice files unless a tiny bugfix from prior (but document).
- No changes that would make refresh reachable from hot path.
- No docs updates (that can be in polish if needed).
- No real LLM calls in any test run here.

Stop and follow-up if needed outside.

**Test Execution Policy**
- smoke -q
- The refresh smoke must be safe (no key, no network).

**Output per WORKFLOW**
done/2026-06-03-classify-05-refresh/...

Claim first. This is the "evolution" piece, kept separate and last per the plan's lightweight priority. Implement the body cleanly from the approved sketch. Deliver and we will review (including the critical grep), then do the final polish slice if needed.

Good luck - keep it explicit and safe.