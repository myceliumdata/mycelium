# RESTART PROMPT - Mycelium Seed-Data-Context Architecture Redesign (as of 2026-06-07)

**Purpose:** Full context preservation for compaction / new session restart. Cat or paste this entire file at the start of a fresh conversation with Grok/Cursor to resume exactly. Do not summarize or lose any details from this document.

**Date:** 2026-06-07
**Last major activity:** Creation of slice prompt 2026-06-07-1720-eliminate-id-from-seed-transform.md (in next/); review of 1700-expose-uuid-in-results completed (review.md added); 1710-eliminate-core-person-fields.md also in next/.

---

## Original Two Converging Threads (preserve exactly - from initial RESTART_PROMPT_FOR_PLAN.md)

The conversation has two main threads that are now converging:

1. Earlier work on a dev tool called `bin/reset-mycelium` (Python script for cleaning generated specialists, registry, data dirs, etc., to support frequent "nuking" during agent development). This was initially implemented directly (user was unhappy about writing code without being asked), then properly driven via Cursor prompts in `prompts/cursor/done/reset-mycelium/` and a cleanup slice. The physical script was temporarily removed during "cleanup the mistaken code" but has been restored as the "Cursor-produced" version. The user has now asked to commit/push recent changes (including all the prompt records and the script).

2. The current long discussion (the main focus now): Completely redesigning how the supervisor and specialists interact, moving away from the current "core_data is special" model.

### Current Architecture (pre-changes, for reference)
- Seed/CRM data is loaded into a SQLite DB.
- Core fields: id, name, employer (always provided by core_data specialist).
- Non-core attributes are classified by the CategoryTree (LLM + cache) into categories (contact, demographic, financial, professional, social, relationships, etc.).
- Supervisor classifies requested attributes, creates specialists on-demand via Agent Factory if needed, and routes to the appropriate specialist (or core_data).
- Specialists (generated from Jinja template) receive the state, resolve the person via core_identity, and return a response (often "still researching via X_specialist" narrative + core record). They have per-category storage via SpecialistStorage (data/agents/<category>/storage.json + strategy.json).
- Graph: START -> supervisor -> specialist (dispatcher) -> END.
- Thread/checkpointer exists but queries are mostly independent today.
- Generated specialists are committed to git in src/agents/specialists/.
- Registry in data/agent_registry.json tracks all (core + generated).
- No direct specialist-to-specialist communication yet.
- reset-mycelium tool exists for dev to clean generated state without env var gymnastics.

### User's Proposed New Model (user's exact words and clarifications)
The user is reversing previous ideas (e.g., no more short-circuiting name/employer in classification). Core data is no longer special.

1. Treat any data that is loaded for the supervisor as "seed" data. That seed data may or may not be accurate. The supervisor assigns an ID to the person represented by this data.

2. The supervisor must pass the seed data to all specialists (including the contact specialist) it invokes. In addition, the supervisor will pass data related to that person that has been collected by other specialists. All of that data is the context. (This is not the most efficient way but avoids building specialist-to-specialist communication now. Add explicit TODO to eventually change from supervisor providing all context to agents retrieving context from fellow specialists.)

3. Specialists will be responsible for validating seed data passed to them. Specialist data always overrides seed data. Example: if person A is at firm X in seed, but later moves to firm Y, the seed won't change, but the specialist responsible for the employer field will have the right value. (This can even apply to name: seed might have "Paul Murphy", contact specialist can store full "Paul Rober Murphy".)

Additional clarifications from user:

- The specialist (supervisor logic) will still decide what specialists to invoke. It will invoke all of the specialists required to retrieve the requested fields. The fact that it first has to invoke *all* the specialists in order to build context is an implementation detail. Building context will require pulling all available data associated with the person ID from every specialist.

- Person ID (current phase): Continue to restrict queries to full names and match against names in the Seed data. Supervisor assigns the ID. (User has more thoughts but defer.)

- Context passing details (3 scenarios for a specialist):
  1. The specialist already has the requested data and returns it. It doesn't even need to look at the context.
  2. The specialist doesn't have the data and hasn't looked for it yet. It will return the fact that the data is not currently available but may be in the future. In parallel it starts a thread to retrieve it by using LLM+tools and the context. (Mark as "pending" to avoid multiple threads. Add note: we will have to revisit this later to make sure it's robust — e.g., research thread dying and leaving "pending" forever.)
  3. The specialist researched the data in the past and couldn't find it. It will mark that field N/A and will return that value if the datum is requested again. (Future: supervisor may request a new search, or specialist may retry on its own with new tools.)

- Fields passed to specialist: only the fields the specialist owns.

- Seed data: Whatever is provided when the system is started. It will be a JSON file (switch from DB for more expressive data). Seed data cannot be updated without resetting the system to its origin state. Core data specialist will no longer exist.

- Implications user listed:
  - Switch seed data storage from database to JSON file.
  - Change how output is built (seed data no longer special).
  - No core data specialist.

- Thread continuity: To date every invocation has been its own thread (simple queries). Getting rid of threads today would change nothing. In the future, LLM-to-LLM conversations could be quite long; keeping state will be critical. But we aren't there yet. We can keep managing state as we are today with no negative impact (we just aren't making use of it yet). Clarification: user is thinking about state that survives across multiple user queries (per-thread state via checkpointer).

- Supervisor role: Still decides specialists based on requested fields. Invokes the required ones, passing context + person ID + list of fields the specialist owns.

- No direct specialist-to-specialist yet (deferred, with TODO).

- Output building must change because there is no longer a privileged "core" layer.

- Context is created by the supervisor (seed + union of specialist data for the person). Specialist data wins on conflicts with seed.

- Idempotency is not a goal. Data continuously changes as natural outcome of specialist research.

- Performance/efficiency: Do not worry about now. This is a whole new way of managing a data store.

### Project Style and Constraints
- Follow the style of existing plans (e.g., docs/plans/agent-factory-phase2.md, classification-engine-phase1.md): lightweight but explicit, clear hooks for future evolution, keep supervisor thin where possible.
- The reset-mycelium tool (already "delivered" via Cursor prompts) supports frequent nuking of generated specialists during dev.
- All changes must support the vision of specialists owning their data/storage, using LLM+tools for research/validation, overriding seed, etc.
- Future phases will include: specialist peer context retrieval, robust pending handling, attached validation/provenance data, possibly direct specialist communication, richer person ID strategies, long-running threads, etc.
- Keep the plan actionable for "implementation in the next few hours" — break into small, reviewable slices (like the previous agent-factory Cursor slices with strict scope, verification, Guards against scope creep).

### Your Task When Resuming (from initial)
You have been restarted. The full conversation history above (this document) is the complete context. Do NOT assume or hallucinate any details not in this document.

1. Confirm you have internalized the entire model as described.
2. Acknowledge any compaction/summarization that occurred.
3. Propose or iterate on a structured plan document (in the style of previous plans) to implement this architecture.
4. The plan should cover: Current state snapshot. Target model (with all user's points). Key shifts and implications... etc.

(End of original two-thread summary from initial RESTART_PROMPT_FOR_PLAN.md)

---

## Progress on the Redesign (as of 2026-06-07)

### Completed & Reviewed Slices (Cursor prompts executed, reviewed, approved)
All slices followed strict scope, WORKFLOW.md (claim to in-progress/, deliver to done/<slug>/ with prompt.md + output.md + review.md, remove only own claim), smoke-first + targeted full + manual verification matrices, ruff, git-stat enforcement, no scope creep.

- **1500-seed-json-loader** (reviewed): Standardized to data/seed.json (exact copy of people array from seed_crm.json, 457 records). Introduced src/agents/seed.py (SeedData, get/reset, uuid5 person_id assignment using seed id or name|employer, find_by_key by name or seed id, env MYCELIUM_SEED_PATH). Updated storage/core.py (auto_seed=False default), conftest, test_core_graph fixture. Old DB seeding severed. Verification: loader idempotency, name match, env isolation, "delete seed" fallback, smoke + 3 full tests green. data/seed.json now canonical static origin (user replaces manually; reset-mycelium ignores it).

- **1510-state-model-context** (reviewed): Added to MyceliumGraphState: matched_persons, context, current_person_id, target_fields. Docstrings + TODO for peer retrieval. Backward compat via defaults. Tests green.

- **1520-unify-responses** (reviewed): responses.py: _build_identity_results (supports base_records), updated messages (no "core record", "Found record for...", "No record found for...", "We're still researching... (via ...)"). response_found/non_core accept base_records. Updated core_data.py call sites minimally, test asserts for new strings (including extra smoke touch to test_supervisor_routing.py noted transparently). 

- **1530-eliminate-core** (reviewed): core_data.py deleted. dispatch.py: no core fallback, raises on unknown route. registry.py + data/agent_registry.json: no core_data entry (seed now empty agents). supervisor.py: seed resolution via find_by_key, direct responses from seed when no specialists needed, still plans/creates real specialists. __init__.py, bin/reset-mycelium, tests updated (test_core_data_agent.py now just skip). Graph clean. Queries now use seed path. reset-mycelium dry-run works. No core_data in runtime.

- **1540-specialist-template-base** (reviewed): Updated specialist_agent.py.j2 (header, removed core_identity, added person_id/context/target_fields resolution, full 3 scenarios with _start_research_if_needed + daemon thread stub + pending/na/found logic + specialist_contrib, robustness TODO exact quote, uses unified builders with base_records). base.py: comment on person_id keys in records. agent_factory.py: refine prompt updated. test_agent_factory.py minimal marker updates. Smoke green. Manual tmp factory create + dynamic load/invoke test exercises scenarios correctly (pending path writes status, returns correct contrib/message).

- **1550-supervisor-context-graph** (reviewed): New src/agents/context.py (ContextBuilder.build_full_context using registry + SpecialistStorage pulls, TODO for peer retrieval). supervisor.py: planning only (collects *all* specialists_to_invoke via _collect_..., puts in context._meta, enriches matched_persons/context/current_person_id; always route=None). dispatch.py: build_context_node, invoke_specialists_node (sequential, enriches with context/person_id/target_fields, collects contributions), assemble_response_node (merges using contributions + pending logic in messages; legacy alias). graphs/core.py: new nodes + conditional routing per choice C (if specialists_planned -> build_context else direct assemble; edges for fan-in). Tests/fixtures updated. Manual CLI queries (name-only + multi-attr) exercise full flow (plans, builds context, invokes multiple, assembles with "via ..." + contributions in debug). Smoke + full green. No core_data left.

- **1600-integration-tests-reset-docs-regen** (reviewed, capstone): reset-mycelium cleaned (no core, no seed.json handling). Re-genned all 6 specialists via factory (after --specialists reset) — they now have new headers, 3-scenario logic, TODO, no core_identity. Updated MCP/main/CLI/tests/docs (architecture.md, plan doc with "Implemented via ... 1500-1600", TODO.md). Full matrix: smoke/full, classic 3 in clean env, manual CLI (name, +1cat, +multicat, ambiguous, missing, post-reset re-create), ruff, grep no core in runtime, confirm seed.json source, traces. System end-to-end on new model.

- **1700-expose-uuid-in-results** (reviewed + approved in this session): Added person_id (UUID) to results dicts and Person model (alongside original seed "id"). Updated identity builders, tests (asserts + plain-dicts allowance), docs. Manual single + ambiguous queries now expose distinct person_ids in results. Smoke/full green. This addresses user's need for stable UUID in results for client disambiguation/followups (esp. multi-result sets).

**Note:** The 1720 prompt (eliminate-id-from-seed-transform) was created at user's request (see below) but has not yet been executed by Cursor (still in next/).

### Currently in `prompts/cursor/next/` (ready for Cursor)
- 2026-06-07-1710-eliminate-core-person-fields.md (sibling to 1700; removes CORE_PERSON_FIELDS / non_core_attributes / the privileged core notion entirely so name/employer queries properly surface specialist status).
- 2026-06-07-1720-eliminate-id-from-seed-transform.md (the one just created; see below).
- Historical reset-mycelium/ subdir.

Cursor "work on the next task" will pick oldest by filename.

### The 1720 Prompt (just written, for the user's latest request)
**File:** prompts/cursor/next/2026-06-07-1720-eliminate-id-from-seed-transform.md

**Objective (verbatim from user):** "write a promt to modify the file that transforms seed_crm.json to seed.json. Eliminate the creating of the id field."

**Key elements in the prompt (self-contained for Cursor):**
- Creates `data/prepare_seed.py` (the reusable transform file): reads seed_crm.json, strips "id" from each person (output only name + employer), writes clean seed.json.
- Regenerates data/seed.json via the script (will have no "id" keys).
- Updates src/agents/seed.py (enrichment: no longer sets seed_id from static "id"; person_id always assigned).
- Updates src/agents/supervisor.py ( _identity_records_from_seed and _persons_from_seed now set "id" to the person_id UUID; comments reference slice).
- Updates test fixture in test_core_graph.py (inline seed creation omits "id"; light UUID assert).
- Updates docs/architecture.md (seed.json now only name+employer; results "id" is the UUID).
- Verification: run prepare, inspect seed.json has no "id", manual queries (single + name attr) show results "id" is UUID (matches internal), multi-result has distinct UUIDs, smoke/full green, ruff, git-stat only scoped, grep no more "id" creation in transform path.
- Full context references the user's recent query with --attributes name (got old "person-0001" + full record incl. unrequested employer), the need for UUID in results, the 1700/1710 siblings, RESTART_PROMPT_FOR_PLAN.md, how seed generation works (see below), reset policy (user replaces seed.json manually).

This will make the exposed "id" in results the UUID, and stop creating the legacy id in the static seed transform.

### How seed.json Is Generated (user asked; include verbatim in all future restarts)
- **Source of truth:** data/raw_data.json (460 rich contacts; owner Paul Murphy, firms, roles, emails, LinkedIn, etc.).
- **Step 1 (one-time, Cursor 2026-06-01-1730-process-raw-data-to-seed-crm):** Python snippet (in the prompt) loaded raw_data["contacts"], applied explicit dedup (Andrea Kalmans → only Lontra Ventures; Pete Townsend → only Techstars; Kevin Zhang both kept), preserved order, assigned person-0001..person-0457, extracted only {"id", "name", "employer"}, wrote to data/seed_crm.json (backed up old placeholder). 457 records.
- **Step 2 (redesign, Cursor 1500):** data/seed.json created as **exact copy** of the "people" array from seed_crm.json (so identical content, still had "id"). This standardized to direct JSON model (no more DB seeding for people; queries use agents.seed).
- **Current policy (redesign + user instruction):** seed.json is the committed static read-only origin. **User replaces the entire file manually to change origin data.** reset-mycelium **never touches** it (confirmed in 1600 and reviews). No automated generator script exists (was out-of-scope in 1730; only documented as optional follow-up). 
- **Runtime:** agents/seed.py loads it, enriches every record with "person_id" (uuid5, idempotent, never written back), optionally "seed_id" (legacy). find_by_key supports name or (legacy) seed id.
- **Legacy artifacts:** seed_crm.json + .bak remain (historical). Old storage/core.py still references seed_crm but auto_seed=False by default.
- **Future updates:** Re-apply similar dedup+id logic (or the new prepare_seed.py from 1720) to a fresh raw export. The 1720 prompt will make the transform omit "id" entirely (UUID becomes the id).

See also: data/seed.json (current), the 1730 prompt/output for exact dedup rules + snippet, 1500 prompt/output for the copy step, architecture.md (Seed origin section), and the 1720 prompt (will introduce data/prepare_seed.py that omits id).

### User's Recent Issues & Planned Fixes (from direct queries)
- Ran: `uv run mycelium query --person-key "Nichanan Kesonpat" --attributes name`
  - Got full seed record (id + name + employer) + plain "Found record..." message (no specialist status for "name").
  - Debug showed classification name→contact, but outcome='found', no "via", no contributions.
- **Why?** (pre-1720/1710 state):
  - "id" in results was still the legacy seed id (not UUID).
  - name/employer still in CORE_PERSON_FIELDS → non_core_attributes filtered "name" out → assemble took "else: response_found" path (plain found + full identity incl. unrequested employer). Even though classification routed to contact and invoke likely happened, the core filter + if deferred guarded the status message path.
- **Fixes in flight:**
  - 1700 (reviewed/approved): now exposes "person_id" UUID in results (alongside original id). Tests/docs updated. Multi-result disambiguation works.
  - 1710 (in next/): eliminates CORE_PERSON_FIELDS / non_core_attributes entirely. Updates assemble + template so *any* requested attr (incl. name) goes through specialist status/contribution path. Requesting "name" will now show proper "not currently available... (via contact_specialist)" (or value) while still returning identity record.
  - 1720 (in next/, just created at user's request): modifies the transform (creates data/prepare_seed.py) to **eliminate creating the "id" field** in seed.json. New seed will have only name+employer. Code updated so results "id" = the person_id UUID. Regenerates seed.json. This directly addresses "why is the ID not a UUID" and "eliminate the creating of the id field".

After 1710+1720: name/employer queries will behave like any specialist-owned field; results "id" will be the UUID; no more legacy id creation in the seed transform.

### Current Project State Snapshot (post-1700 review, pre-1710/1720 execution)
- **Seed:** data/seed.json (static, 457 people with id/name/employer from prior processing; person_id UUID runtime only; seed_crm.json legacy).
- **Loader:** agents/seed.py — direct JSON, idempotent UUID, find_by_key (name or seed id), env override. No DB people seeding for queries.
- **State:** matched_persons (enriched with person_id), context (seed + specialists), current_person_id, target_fields. Classifications still present.
- **Responses:** Unified (no "core record" language; supports base_records; "Found record for...", researching/pending via specialist).
- **No core_data specialist:** Deleted. Registry/dispatch/supervisor clean. Queries resolve via seed + classification-driven specialists (or direct seed response if no attrs/specialists needed).
- **Graph (post-1550):** supervisor (plans all required specialists into _meta) → build_context (pulls full union from all specialist stores + seed) → invoke_specialists (sequential calls with full context + person_id + target_fields; collects contribs) → assemble_response (merges identity + status from contribs). Conditional routing.
- **Specialists (post-1540/1600 re-gen):** 6 fresh ones with new template (3 scenarios + pending daemon stub + TODO + specialist_contrib + context/person_id/owned_fields; no core_identity). Re-gen via factory after reset --specialists.
- **Context builder:** src/agents/context.py (thin, pulls via registry + SpecialistStorage; TODO for peer retrieval).
- **Person/Results:** Now include person_id UUID (from 1700). Full identity from seed (with future overrides possible for name/employer).
- **reset-mycelium:** Cleaned (no core, no seed.json handling; targets generated + DB/categories).
- **Docs:** architecture.md updated for new model (seed origin, graph nodes, no core, results include person_id). Plan doc notes implementation through 1600 + later slices. TODO.md has redesign landed note.
- **Tests:** Smoke + full green for redesign slices. Fixtures use seed.json + new resets (incl. context_builder). Classic 3 + manual matrix pass (with pending/researching messages, contributions, via labels, UUIDs in results).
- **Other:** Thread/checkpointer unchanged. No direct specialist-to-specialist yet (TODO). Idempotency not a goal. Performance deprioritized.

**Open in next/ (not yet executed):**
- 1710-eliminate-core-person-fields.md
- 1720-eliminate-id-from-seed-transform.md (the transform one; will create prepare_seed.py that omits id, regenerate seed.json without ids, make results "id" = UUID, update loader/builders/tests/docs).

**Must-Read Files (every restart):**
- RESTART_PROMPT_FOR_PLAN.md (original detailed model — this reset is an update/extension)
- prompts/resets/2026-06-07_redesign_reset.md (this file)
- docs/architecture.md (live truth; updated for redesign)
- docs/plans/seed-data-context-architecture.md (the plan; update status as slices complete)
- prompts/cursor/WORKFLOW.md + PARALLEL_EXECUTION_GUIDE.md
- prompts/system/CORE_PROMPT.md
- TODO.md
- All prompts/cursor/done/2026-06-07-*/ (prompt.md + output.md + review.md) for the redesign slices — they contain exact verifications, decisions, and current behavior.
- src/agents/seed.py, supervisor.py, dispatch.py, models/state.py (core of new model)

**Test Policy (strict, from WORKFLOW + all slices):**
- Default: only `uv run pytest -m smoke -q`
- For integration changes (graph, storage, run_query, results shape): run targeted full (`-m full -k "query or graph or ..."` ) + the classic 3 in clean env + manual CLI matrix.
- If adding/changing a test, Grok decides smoke vs full category; run the appropriate immediately.
- Always paste outputs in Cursor output.md / reviews.
- ruff on touched files.
- Manual matrix always includes post-reset re-create, ambiguous names, name-only vs attrs, etc.

**Collaboration:**
- Paul: vision, priorities, direct questions/feedback (e.g. the name query example, UUID exposure request, "eliminate the id field", "how is seed.json generated").
- Grok: planning, writing detailed Cursor prompts (small slices), reviews (read prompt+output, inspect code with tools, re-run verifs, write review.md), creating reset prompts.
- Cursor: executes claimed prompt in next/ per WORKFLOW (claim first, scope discipline, paste full verif output, deliver to done/).

**Key Principles (unchanged):**
- Supervisor stays thin (coordinator/planner).
- Specialists own their data + use LLM+tools for research/validation/overrides.
- Seed is immutable origin (JSON, replace to reset).
- Context = seed + union from all specialists (supervisor provides for now; TODO peer retrieval).
- 3 scenarios per specialist for owned fields.
- Explicit TODOs for future (pending robustness, peer context, richer person ID, long threads, validation/provenance, direct specialist comms).
- Small reviewable slices, strict scope boxes in prompts, "stop and escalate".
- reset-mycelium for dev velocity (nuke generated specialists).
- Idempotency not a goal; data evolves.
- Perf/efficiency deprioritized now.

---

## Next Steps When Resuming
1. Confirm you have internalized the *entire* model (original user words + all clarifications + all slice progress + current code state + the two new prompts in next/).
2. Acknowledge this reset (compaction occurred; full history preserved here).
3. The 1720 prompt (in next/) is the direct response to "write a prompt to modify the file that transforms seed_crm.json to seed.json. Eliminate the creating of the id field." Cursor should execute it next (or after 1710).
4. After Cursor delivers 1710/1720: review them (read their done/ output, inspect code, re-run matrix including the --attributes name query, confirm UUID is now the "id", no more core filter for name/employer, seed.json has no "id", etc.), add review.md.
5. Update the plan doc (seed-data-context-architecture.md) and architecture.md with final status ("Implemented: ... through 1720").
6. Update TODO.md.
7. Consider commit/push of the full set (all new done/ prompts + reviews + code changes + this reset).
8. Resume any open discussion (e.g. further refinements, next phases like real research in specialists, peer context retrieval, supporting UUID in person_key, etc.).

**If Cursor is handed "work on the next task":** It will claim the oldest (1710 then 1720). Remind it of the full context in this reset + the individual prompt files.

This document + the referenced done/ slice artifacts + RESTART_PROMPT_FOR_PLAN.md + architecture.md + the plan should allow perfect resumption without loss.

(End of reset prompt. All details from original threads, all slice history, user's recent feedback, seed generation process, and current state are preserved here.)
</user_query>