# Task: Classification Engine Phase 1 - Slice 03: Wire classifications into Supervisor + State (minimal injection)

**Read these first (mandatory):**
- `docs/plans/classification-engine-phase1.md` (the approved plan - immutable spec. Focus on "How the Supervisor Will Call This (Minimal Changes)", the exact supervisor diff, the state field addition, Step 3 verification commands, lightweight note, and risks)
- `prompts/cursor/WORKFLOW.md`
- `.cursor/rules/04-cursor-workflow.mdc`
- `docs/architecture.md` (supervisor is thin coordinator, "classifies the query and route to specialists" but currently does nothing real, audit_log is the channel, small/reviewable changes)

**Objective**
Implement the core "supervisor intelligence" slice: add the `classifications` field to MyceliumGraphState, update supervisor_agent to call get_category_tree().classify() for each requested_attribute, append nice audit log lines for known ones, and return the classifications list in the result dict (so it flows into state).

This is the minimal change that gives the supervisor the ability to look up categories. No change to routing (still always core_data in Phase 1). No changes to response yet (that is slice 04).

Follow lightweight: simple, explicit, no over-abstraction.

**Lightweight priority (from approved plan - obey strictly)**
"Keep implementation as lightweight as possible in early steps. Prioritize getting `classify()` + supervisor injection working cleanly before polishing `refresh_from_llm` and atomic saves. Err on the side of simplicity for Phase 1."

**Constraints & Principles**
- Strictly limited scope (see box below). Previous slices (01 scaffold, 02 engine) have already delivered the engine.
- Use the *exact* small diff and code from the approved plan's "How the Supervisor Will Call This" section.
- Preserve all existing behavior for queries without requested_attributes, and for the route/audit when no attrs.
- Small, reviewable increment only.
- Smoke -q default. Update/add smoke tests only for the supervisor_agent path (no full graph yet).
- This is the third small slice in the sequence. The monolithic big prompt is superseded and moved to _superseded/.

**Context**
- Slice 01 created data + package skeleton.
- Slice 02 implemented the full CategoryTree (classify works, returns category/assigned_agent/description/confidence, unknown for missing, reset/get work, uses the seed from data/categories.json or embedded).
- Now we wire it into the supervisor (the primary injection point per approved plan and architecture.md).
- The approved plan has the exact state addition, the supervisor code diff (using current = _coerce, query = current.query, build classifications list, append to audit_log only for non-unknown, return "classifications": ... ), and test updates.
- After this slice, a manual `uv run mycelium query --person-key "Nichanan Kesonpat" --attributes email` will show the classification in audit_log (e.g. "Supervisor: classified 'email' -> category=contact, agent=contact_specialist, confidence=0.95"), but response.debug and core_data will not yet have it.
- This matches "minimal changes to supervisor" and "inject classification metadata into the result".

See approved plan for the full "How the Supervisor Will Call This", the ClassificationResult shape, and Step 3 verification (smoke + the specific manual query).

**Exact Steps (perform in order)**
1. **Claim the task first (mandatory per WORKFLOW.md)**: Scan next/, this should be the oldest (after previous slices claimed/done), **immediately move** this file to `prompts/cursor/in-progress/2026-06-03-classify-03-supervisor-injection/prompt.md`. Document the move. Do not touch other in-progress files.

2. **Discovery**:
   - Read the approved plan sections listed (especially the supervisor diff and state field).
   - Read the current `src/agents/supervisor.py` (very thin, _ = _coerce, always returns route + basic audit).
   - Read `src/models/state.py` (MyceliumGraphState, PersonQuery with requested_attributes, non_core_attributes helper).
   - Read `tests/test_supervisor_routing.py` (the existing test_supervisor_agent_routes_to_core_data).
   - Read `tests/conftest.py` (the _final_cleanup resets).
   - Run `uv run pytest -m smoke -q` (baseline).
   - Run the before repro: `uv run mycelium query --person-key "Nichanan Kesonpat" --attributes email` (note current audit has no "classified" lines).

3. **Update state.py**:
   - Add the classifications field to MyceliumGraphState, exactly as in approved plan:
     classifications: list[dict[str, Any]] = Field( default_factory=list, description="Classification metadata injected by supervisor for requested_attributes (Phase 1: lookup only).", )
   - Ensure `Any` is imported from typing if not present.
   - Keep the change minimal.

4. **Update supervisor.py** (the key minimal change):
   - Add the import: from .classification import get_category_tree
   - Change the supervisor_agent body to the exact diff in the approved plan:
     current = _coerce(state)
     query = current.query
     audit_log = ["Supervisor: evaluating query."]
     classifications: list[dict[str, Any]] = []
     if query.requested_attributes:
         tree = get_category_tree()
         for attr in query.requested_attributes:
             cl = tree.classify(attr)
             classifications.append(cl.model_dump())
             if cl.category != "unknown":
                 audit_log.append( f"Supervisor: classified '{attr}' -> category={cl.category}, agent={cl.assigned_agent}, confidence={cl.confidence:.2f}" )
     route = "core_data"
     audit_log.append(f"Supervisor: routing to {route} specialist.")
     result: dict[str, Any] = { "route": route, "audit_log": audit_log, }
     if classifications:
         result["classifications"] = classifications
     return result
   - Keep the _coerce helper.
   - Update the docstring if needed to reflect it now does classification lookup for attrs (still thin router).

5. **Update tests and conftest (minimal for this slice)**:
   - In `tests/conftest.py`: import reset_category_tree from agents.classification.engine (or via the package) and add it to the cleanup tuple.
   - In `tests/test_supervisor_routing.py`:
     - Ensure the existing test_supervisor_agent_routes_to_core_data still passes (for no-attrs case, classifications will be absent or empty).
     - Add/extend a smoke test that provides requested_attributes with known non-core (e.g. "email") and asserts "classifications" in result, and that the category/assigned_agent are correct for the known attr. Also test an unknown attr gets "unknown".
     - Keep it smoke-safe (no real storage/graph).

6. **Verification for this slice (smoke + manual)**:
   - `uv run pytest -m smoke -q`
   - Re-run the manual: `uv run mycelium query --person-key "Nichanan Kesonpat" --attributes email`
     - Expect: still works, "we're still researching", but audit_log now contains the "Supervisor: classified 'email' ..." line.
     - Core attrs only query should have no classification lines.
   - `uv run python -c '...' ` direct call to supervisor_agent with attrs to inspect the returned dict has "classifications".
   - Confirm no other files changed (git status / diff limited to the 4 files in scope).
   - Confirm the engine from slice 02 is used (classifications appear).

7. **Output artifacts**:
   - Create `prompts/cursor/done/2026-06-03-classify-03-supervisor-injection/output.md`:
     - Summary, decisions (e.g. "used exact diff from approved plan; kept route unchanged; lightweight simple injection").
     - Full command outputs.
     - Diffs for the files touched in *this* slice.
     - Confirmation of scope and that previous slices' behavior is preserved.
   - Move/copy this prompt to done/ as prompt.md.
   - Remove *only* your claimed file from in-progress/.

**Scope Boundaries (Strict)**
You may only modify files under:
- `src/models/state.py`
- `src/agents/supervisor.py`
- `tests/conftest.py`
- `tests/test_supervisor_routing.py`

**Out of Scope (Do Not Touch)**
- `data/categories.json`, `src/agents/classification/` (previous slices; do not re-edit engine/models unless a bug in previous slice).
- `src/agents/core_data.py`, `src/agents/responses.py`, `tests/test_core_graph.py` (slice 04).
- `src/graphs/core.py`, mcp, main, storage, other tests, docs/architecture.md, the superseded big prompt, the approved plan itself, TODO.md, etc.
- Do not change routing logic or response builders.
- Do not implement refresh or polish.

If you believe something outside is required: **stop immediately**, document in output.md + create follow-up prompt. Do not make the change.

**Test Execution Policy**
- Default `uv run pytest -m smoke -q`
- The tests updated here are smoke (direct agent node calls + stubs).
- If adding a test that would require full marker, note it for Grok.

**Required Output Location & Artifacts**
- `prompts/cursor/done/2026-06-03-classify-03-supervisor-injection/output.md` and prompt.md per WORKFLOW exactly.
- Remove only the specific claimed file from in-progress/.

Follow the claiming process in WORKFLOW.md before any implementation.

After you deliver and say ready for review, we (Grok + Paul) will review *just this slice*, re-run the smoke + the specific manual query, verify the injection appears in audit as specified in approved plan, confirm scope, add review.md, then prepare the next small prompt (04-propagate).

Claim the file now and execute. Keep changes small and explicit. Copy the diff and details from the approved plan. Good luck.