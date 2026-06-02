# Mycelium — Full Top-Down Code Walkthrough (Refreshed June 2026)

**Date of this version:** Based on current codebase state after deep dives into graph, ingest path, CoreIdentity, queries, etc.
**Purpose:** Comprehensive orientation so you can see how *all* pieces fit together. This is a refreshed re-print of the original top-down walkthrough, updated with clarifications from our conversation (especially around the graph, enrich/validator being *only* for ingestion, and the Phase 1 nature of CoreIdentity).

We originally went deep into the graph section because assumptions about "agents" for queries vs. ingest were different from reality. Enrich and validator are **not** involved in normal lookups/queries — they are exclusively for the new data ingestion handshake.

---

## 1. High-level Vision & Philosophy (The "Why")

From [docs/architecture.md](/Users/paul/Library/CloudStorage/Dropbox/PRM/projects/mycelium/docs/architecture.md) (the living source of truth), the compact reset prompt, and [prompts/system/CORE_PROMPT.md](/Users/paul/Library/CloudStorage/Dropbox/PRM/projects/mycelium/prompts/system/CORE_PROMPT.md):

- **Goal**: Data infrastructure that is **100% managed by AI agents**, not humans. External agents talk to it primarily via MCP (JSON).
- **Core rule**: *Everything is ultimately agent-owned* — including what we currently call the "core" CRM data.
- **Supervisor is deliberately narrow**: Pure coordinator/router. It never owns data or accesses storage directly in the long term. No "god agents."
- **Specialists own their domain + their storage strategy**. Even core identity resolution can move off shared storage later.
- **No pre-defined derivatives**: No central schema for "extra" attributes, no shared `extra_json` or derivative tables. These emerge from specialists.
- **Phase 1 practical constraint**: Shared storage (`CoreStorage`) must stay dead simple. Supervisor direct-ish access (via the `CoreIdentity` facade) is an explicit temporary concession.

This is a deliberate evolution from earlier thinking (lots of cleanup work in the `prompts/cursor/done/` history around derivative removal, orchestrator→supervisor rename, response model simplification, etc.).

**Key from our deep dive**: The architecture vision is aspirational. Current code (especially CoreIdentity and how queries work) is in a "Phase 1 concession" state. We discussed this at length — CoreIdentity is documented as the "Core Identity agent (Phase 1)" but is currently a thin facade, not a separate LangGraph node/agent with its own graph handoff.

---

## 2. Project Structure & Development Workflow (How We Build It)

This is part of the "system":

- **Roles**: Paul (vision/priorities), Grok (planning/architecture/reviews/prompts), Cursor (senior dev executing in IDE).
- **Handoff mechanism**: Structured self-contained prompts in `prompts/cursor/next/`. See [prompts/cursor/WORKFLOW.md](/Users/paul/Library/CloudStorage/Dropbox/PRM/projects/mycelium/prompts/cursor/WORKFLOW.md) and the embedded rule [`.cursor/rules/04-cursor-workflow.mdc`](/Users/paul/Library/CloudStorage/Dropbox/PRM/projects/mycelium/.cursor/rules/04-cursor-workflow.mdc).
  - "Work on the next task" → Cursor scans `next/`, sorts alphabetically (YYYY-MM-DD-HHMM), **moves first file to `in-progress/` (the claim/lock)**, executes, delivers to `done/<slug>/` (prompt.md + output.md + optional review.md), and **only removes its own claimed file from in-progress**.
  - Strong emphasis on **scope discipline**, small/reviewable changes, and parallel safety.
- **Cursor rules** (alwaysApply): Python standards (strict typing, Pydantic, tests), LangGraph rules (explicit graphs, no god agents).
- **Hooks** ([.cursor/hooks.json](/Users/paul/Library/CloudStorage/Dropbox/PRM/projects/mycelium/.cursor/hooks.json) + scripts): Auto-allow single-file deletes; gate dangerous `rm -r` / dir deletions.
- **Must-reads every session**: `docs/architecture.md`, `prompts/cursor/WORKFLOW.md`, `TODO.md`, `prompts/system/CORE_PROMPT.md`, `.cursor/rules/`.
- Historical work is fully auditable in `prompts/cursor/done/` (many recent folders cover the model alignment, supervisor refactor, response redesign, trace/thread_id work, MCP rename, etc.).
- `next/` and `in-progress/` are currently empty — the queue is clear.

This process itself is sophisticated agent orchestration, mirroring the project's philosophy.

Current directory snapshot (as of latest exploration):
- `src/`: agents/ (supervisor, routing, responses, core_identity, enrich, validator, person_prep), graphs/, models/, storage/, mycelium_mcp/, main.py, utils/, etc.
- Lots of legacy pycache from old names (orchestrator, etc.), but source is cleaned.
- `data/`: seed_crm.json (457 people), mycelium.db, checkpoints.sqlite, raw_data.json + .bak.
- `prompts/cursor/done/`: Full history of Cursor-executed tasks.

---

## 3. Core Data Model & Contracts (What the World Sees)

Defined in [src/models/state.py](/Users/paul/Library/CloudStorage/Dropbox/PRM/projects/mycelium/src/models/state.py):

- **`Person`**: *Strictly* `id: str`, `name: str`, `employer: str | None`. `CORE_PERSON_FIELDS`, `MINIMUM_VIABLE_FIELDS`. No `extra`. `core_dict()` helper.
- **`PersonQuery`**: `person_key` (id or name for Phase 1 lookup), `requested_attributes: list[str]` (non-core → specialists), `provided_data: Person | None` (triggers ingest).
- **`PersonResponse`** (the *only* thing CLI/MCP return):
  ```json
  {
    "results": [{ "id": "...", "name": "...", "employer": "..." }],  // always list of core dicts
    "message": "Found... | No core record... | still researching age, x_handle | Added... | Could not add...",
    "debug": "internal only; person_key=...; outcome=found|non_core_requested|ingest_required|...",
    "trace_id": "..." | null,
    "thread_id": "session-abc" | generated-uuid
  }
  ```
- `non_core_attributes()` helper.

**Design notes**: Minimalist on purpose (easy for external agents to consume). Narrative lives in `message`. `results` is *only* core data. `thread_id` for session continuity + LangGraph checkpoints. `trace_id` for observability linking.

From architecture: Lookups and ingests share the same `PersonQuery` shape. Ingestion is single-step via `provided_data`.

---

## 4. Entry Points (How You Talk to It)

- **CLI** ([src/main.py](/Users/paul/Library/CloudStorage/Dropbox/PRM/projects/mycelium/src/main.py)): `uv run mycelium query --person-key "..." [--attributes ...] [--thread-id ...]`, `ingest --data '{...}'`, `seed`.
  - Loads dotenv, forces singleton resets (storage/graph) + re-gets storage (triggers seed), calls `run_query`.
  - Uses `rich` for pretty JSON.

- **MCP server** ([src/mycelium_mcp/server.py](/Users/paul/Library/CloudStorage/Dropbox/PRM/projects/mycelium/src/mycelium_mcp/server.py)) — the primary external interface.
  - FastMCP tools: `query_person(query_json: str) → str`, `submit_person_data(...)`, `list_specialist_routing()` (Phase 1 stub).
  - Resources: schemas for Person / PersonResponse.
  - Same `_bootstrap()` + `run_query` path as CLI.
  - **Important rename** (recent task): `src/mcp/` → `src/mycelium_mcp/` + pyproject entry `mycelium-mcp = "mycelium_mcp.server:run_server"` to avoid collision with the `mcp` SDK package.

Both paths converge on `graphs.core.run_query`.

([pyproject.toml](/Users/paul/Library/CloudStorage/Dropbox/PRM/projects/mycelium/pyproject.toml) declares the scripts and `package-dir = {"": "src"}`.)

---

## 5. The Graph & Runtime Core ([src/graphs/core.py](/Users/paul/Library/CloudStorage/Dropbox/PRM/projects/mycelium/src/graphs/core.py)) + Supporting Pieces

This was the section we dug deep into. You now understand why enrich/validator felt out of place for queries — they are **only** for the ingest path.

**State Graphs 101 (no LangGraph yet)**: Shared "notebook" (state) travels between "desks" (nodes) via arrows (edges). Nodes read current notebook, write updates (deltas), follow arrows. Cycles for loops. Explicit control flow.

**LangGraph**: Library for building these as stateful graphs for LLM/agent workflows. Nodes are callables returning partial state updates. Reducers (e.g., `Annotated[list, operator.add]`) control merging. Persistence via checkpointers (keyed by `thread_id` in config). Compilation turns declaration into runnable. Invocation with initial state + config.

**Mycelium's Graph — The Declaration**:

```python
graph: StateGraph = StateGraph(MyceliumGraphState)

graph.add_node("supervisor", supervisor_agent)
graph.add_node("enrich", enrich_agent)
graph.add_node("validator", validator_agent)

graph.add_edge(START, "supervisor")
graph.add_conditional_edges(
    "supervisor",
    _route_after_supervisor,  # looks at state.route
    {"enrich": "enrich", "__end__": END},
)
graph.add_edge("enrich", "validator")
graph.add_edge("validator", "supervisor")

return graph.compile(checkpointer=checkpointer)
```

Live inspection (from earlier runs):
- Nodes: `__start__`, `supervisor`, `enrich`, `validator`, `__end__`
- Edges show the conditional from supervisor, and the ingest loop.

**The State** (`MyceliumGraphState` in models/state.py):
- `query`, `route`, `response`, `person`, `validation_passed`, `validation_errors` (reducer add), `audit_log` (reducer add), invocation ids.
- Reducers allow accumulating logs/errors across nodes without full overwrites.

**Node Implementations**: Thin callables that coerce state (dict or model), do work, return partial dict updates. LangGraph merges them.

**Invocation & Wrappers** (`run_query`):
- Pre-populates invocation ids.
- `config` with thread_id for checkpointer.
- `_invoke_core_graph`: Wraps with LangSmith `@traceable` only if `LANGCHAIN_TRACING_V2` enabled; captures trace_id.
- `_finalize_response` ensures ids on the final `PersonResponse`.
- Singletons + resets for CLI/MCP/tests.

**The Conditional Router** (`_route_after_supervisor`): Only "enrich" if `state.route == "enrich"`, else END. Set by supervisor during decision.

**Key Insight from Our Conversation**: For *queries*, the graph is essentially `START → supervisor → END`. The entire lookup, CoreIdentity delegation, response building happens *inside one execution of the supervisor node*. Enrich/validator are never visited. This is why they seemed mysterious in query context — they aren't part of query paths at all.

**Concrete Query Trace** (live):
- Nodes visited: only `['supervisor']`
- audit_log: just "evaluating query." + "responding — finishing."
- route ends as None.

**Ingest Trace** (for contrast, only when `provided_data` present):
- supervisor (sets route=enrich) → enrich (assigns id) → validator (checks) → supervisor (persist + respond)

The graph machinery (checkpointer, tracing, state) is always there, but for simple queries it's minimal overhead.

---

## 6. Supervisor & Routing Layer ([src/agents/supervisor.py](/Users/paul/Library/CloudStorage/Dropbox/PRM/projects/mycelium/src/agents/supervisor.py) + [src/agents/routing.py](/Users/paul/Library/CloudStorage/Dropbox/PRM/projects/mycelium/src/agents/routing.py))

**Supervisor is intentionally thin** (post-2026-06-02-1100 refactor):

- `supervisor_agent(state)` → calls `evaluate_supervisor_turn(...)` → returns state updates (person, route, response, audit_log).
- All classification + data decisions in `routing.py: evaluate_supervisor_turn`:
  - Uses injected (or singleton) `CoreIdentity`.
  - Logic (priority order, checked on every supervisor visit):
    1. `validation_passed is False` → `response_ingest_failure`.
    2. `validation_passed is True and person` → `core_identity.persist(...)` + `response_ingest_success`.
    3. `query.provided_data is not None` → `route_enrich` (with the person).
    4. Else: `core_identity.find_by_key(person_key)`.
       - None → `response_not_found` (with ingest guidance in message).
       - Found + `non_core_attributes(requested)` → `response_non_core` (returns core record + "still researching X, Y" message).
       - Found + only core → `response_found`.
  - Propagates thread/trace ids.
- `SupervisorDecision` dataclass for the outcome.

This is the "router" that will later talk to real autonomous specialists. Note that even the CoreIdentity calls happen here, inside the supervisor node (for queries).

---

## 7. Specialist Facade: CoreIdentity ([src/agents/core_identity.py](/Users/paul/Library/CloudStorage/Dropbox/PRM/projects/mycelium/src/agents/core_identity.py))

This was a major point of our later discussion.

```python
class CoreIdentity:
    """Agent responsible for the system's core person identity data (id, name, employer)."""

    def find_by_key(self, person_key: str) -> Person | None:
        return self._resolve_storage().find_person(person_key)

    def persist(self, person: Person) -> None:
        self._resolve_storage().upsert_person(person)
```

- Singleton `get_core_identity()`.
- Currently just wraps `storage.core.get_storage()`.
- **Purpose (per docs and our deep dive)**: Gives the supervisor a "delegate" for core identity responsibility. Future: replace this with a full specialist agent that may own its own storage, do LLM resolution, etc. Supervisor never calls `get_storage()` directly anymore (post-refactor).

**Important clarification (from conversation)**: It is *called* "Core Identity agent (Phase 1)" in docstrings and architecture.md, and the rename task made the name more agent-like. However, it is **not** a separate LangGraph node or dynamically created agent. It is a thin Python facade/singleton. Calls to it are synchronous method calls from *within* `evaluate_supervisor_turn` (which runs as part of the supervisor node). No graph edge routes to it. This is the "Phase 1 concession."

Live demo (from earlier): Same singleton object used for all queries; delegates straight to the shared SQLite storage.

TODO explicitly calls out evolving it into a full specialist agent.

---

## 8. Storage Layer ([src/storage/core.py](/Users/paul/Library/CloudStorage/Dropbox/PRM/projects/mycelium/src/storage/core.py))

Dead simple (by design):

- `people(id TEXT PK, name TEXT NOT NULL, employer TEXT)`.
- `CoreStorage` class (direct sqlite3, row_factory=Row).
- Methods: `find_person` (id or case-insensitive name), `get_person_by_id`, `upsert_person` (replace or ignore), `seed_from_file`.
- Singleton `get_storage()`: on first access, creates DB, runs schema, **auto-seeds from `data/seed_crm.json`** (if present; env overrides `MYCELIUM_*_PATH`).
- `reset_storage()` for tests (closes conn).

**Seed**: 457 people (processed from `raw_data.json` in earlier Cursor task; dedup rules applied for a couple name collisions). See `data/seed_crm.json.bak`. Delete `mycelium.db` to force re-seed.

Legacy note: Old DBs with extra columns/derivative tables will break — see [docs/database-notes.md](/Users/paul/Library/CloudStorage/Dropbox/PRM/projects/mycelium/docs/database-notes.md). No migrations in Phase 1.

For queries, this is where the actual data comes from (via CoreIdentity.find_by_key → storage.find_person → SELECT).

---

## 9. Ingest Path (Enrich + Validator)

**Only triggered by `provided_data` in the query (single-step handshake, per recent redesign). Never for pure queries.**

- `enrich_agent` ([src/agents/enrich.py](/Users/paul/Library/CloudStorage/Dropbox/PRM/projects/mycelium/src/agents/enrich.py)): Takes `provided_data` (or state.person), calls `agents.person_prep.ensure_person_id` (generates `person-{slug}-{short-uuid}` if no id), sets `person` + audit. Then unconditional edge to validator.
- `validator_agent` ([src/agents/validator.py](/Users/paul/Library/CloudStorage/Dropbox/PRM/projects/mycelium/src/agents/validator.py)): Checks `MINIMUM_VIABLE_FIELDS` present/non-empty + basic name regex. Sets `validation_passed` + errors. Then edge back to supervisor.
- Back in supervisor (next turn, via routing logic): if passed, persist via CoreIdentity and respond success; else failure response.
- `person_prep.py` is a small helper for generating id on ingest.

**From our deep dive**: This explains why you don't see them in query context. The graph loop (supervisor → enrich → validator → supervisor) exists *solely* to prepare, validate, and then let the supervisor do the persist for new core records. Enrich/validator are "ingest preparation and validation" nodes.

Live trace example (ingest):
- Supervisor (provided_data → route enrich)
- Enrich (id assigned)
- Validator (passed or errors)
- Supervisor (persist or failure response)

---

## 10. Response Builders ([src/agents/responses.py](/Users/paul/Library/CloudStorage/Dropbox/PRM/projects/mycelium/src/agents/responses.py))

Pure functions: `response_found`, `response_not_found`, `response_non_core`, `response_ingest_success`, `response_ingest_failure`.

All go through `_make_response` + `debug_for_query`. Messages are human- + agent-friendly and include guidance (e.g., how to ingest).

Used by the routing decisions (which are called from inside supervisor).

---

## 11. Observability & Sessions ([src/utils/langsmith.py](/Users/paul/Library/CloudStorage/Dropbox/PRM/projects/mycelium/src/utils/langsmith.py) + graph wiring)

- `trace_id`: Captured only when tracing enabled (via the traceable wrapper + `get_current_run_tree`). Wired into every `PersonResponse` by `run_query`/`_finalize_response`. Recent series of Cursor tasks (09xx) added this end-to-end (CLI, MCP, tests, docs).
- `thread_id`: Passed by caller (CLI `--thread-id`, MCP top-level in JSON) or generated. Used for (a) LangGraph checkpoint config, (b) echoed in response, (c) external agent session continuity.
- Helper: `get_langsmith_trace_url(trace_id)` (supports org/project scoping via env). Added in 0980 but not yet heavily exercised (TODO item remains to configure/test full LangSmith end-to-end with `.env`).

Tests cover this (mocking the run tree).

---

## 12. How a Query Flows End-to-End (The Common Path for Seeded Data)

External (Agent/CLI) → `PersonQuery(person_key=..., requested_attributes=...)` (no provided_data) → `run_query` → graph (thread config) → **supervisor node only** → `CoreIdentity.find_by_key` (via routing) → storage SQLite lookup → build response (found / not found / non-core) → `PersonResponse` (with ids) → return.

All within one supervisor node execution. No graph routing to other nodes. CoreIdentity is the inline delegation point.

Live example (we ran many):
- `uv run mycelium query --person-key "Nichanan Kesonpat"` → core record in results, "Found..." message, short audit_log from supervisor only.

Non-core attributes: Still handled entirely in supervisor (returns core results + "still researching..." message in `message` field). No specialist work yet.

---

## 13. How Ingest Flows (The Path That Uses Enrich/Validator)

External → `PersonQuery(..., provided_data={name, employer, id?})` → supervisor (first visit) sees provided_data → route_enrich (sets person + route) → **enrich** (ensure id) → **validator** (checks) → supervisor (second visit): if passed → `CoreIdentity.persist` + success response; else failure.

The graph loop exists to separate preparation/validation from the final decision/persist (which supervisor owns).

Live traces (we ran several, including success and failure cases with bad data like empty employer or short name) showed the exact state updates after each node.

---

## 14. Current State / Gaps (from TODO.md + recent done/)

Major alignment work is done (per the catch-up section in TODO):
- Core is tiny.
- Supervisor is coordinator (via routing/responses/CoreIdentity).
- Derivative language/tables gone.
- Response model is minimal + ids wired.
- Ingestion handshake is single-step `provided_data`.
- MCP package collision fixed.
- Trace/thread_id everywhere.

Open/high-priority from [TODO.md](/Users/paul/Library/CloudStorage/Dropbox/PRM/projects/mycelium/TODO.md):
- Evolve `CoreIdentity` toward real specialist (less direct storage). "Continue reducing direct data access as specialist agents are introduced (evolve `CoreIdentity` into a full specialist agent)."
- Stronger validation, post-ingest enrichment?
- Full LangSmith config + test + docs (env vars, trace URL usage).
- Decide MCP strategy long-term.
- Real specialist spawning, vector search, LLM bits (future phases).
- CI, license, etc.

From our conversation: The CoreIdentity "agent" vs. facade distinction is a known gap. Enrich/validator are the *only* current examples of separate graph-routed "agents" (and they are limited to core ingest prep).

Recent done/ includes the supervisor refactor, trace work, MCP rename, etc.

---

## 15. What Enables Future Evolution (and How the Pieces Fit)

- **Explicit small graph** instead of one big ReAct loop: Matches the "no god-agents", "narrow responsibilities" philosophy. Easy to reason about, audit, test, and extend one piece at a time.
- **CoreIdentity as a facade, not direct storage in supervisor**: Already a seam for turning "core identity" into a real specialist agent later (as we discussed — could promote it to its own node/subgraph with graph routing from supervisor).
- **Enrich/validator as explicit nodes**: Shows the pattern for future specialists (supervisor detects → routes via conditional edge → specialist node(s) → back to supervisor for final decision/response).
- **Audit log via reducer + trace/thread_id**: Free observability inside the state and across sessions.
- **Minimal contracts (PersonQuery/Response)**: Stable external API while internals evolve.
- **Singletons + resets**: Pragmatic for now; TODO notes considering DI later when multiple agents access storage.
- **MCP + CLI thin adapters**: Both feed the same `run_query` + graph.

**Mental model of how pieces fit** (updated with our deep dives):

```
External (Agent/CLI/MCP)
   │ (JSON PersonQuery ± thread_id / provided_data)
   ▼
Entry points (main.py or mycelium_mcp/server.py)  (bootstrap storage, call run_query)
   ▼
graphs/core.py:run_query  (state + config + traceable invoke + finalize ids)
   ▼
LangGraph (checkpointer per thread_id)
   │
   ├─ supervisor (thin coordinator, one node for queries)
   │   └── (inside: routing.py) 
   │       ├── classify (provided_data? validation results? lookup?)
   │       ├── delegate to CoreIdentity (find_by_key or persist)   <--- current "core agent" is here (inline, facade)
   │       └── select/build response via responses.py
   │
   └─ (only for ingest) supervisor → enrich (prep id) → validator (gate) → supervisor (persist via CoreIdentity)
       (graph edges + state updates for the loop)
```

Storage is the only thing that talks to SQLite today (via CoreIdentity for the facade). The graph + run_query wrapper are the execution + observability harness. The supervisor + routing are the decision nexus.

**Everything is explicit, typed, auditable, and small** — which is why digging into the graph revealed the ingest-only nature of enrich/validator and the Phase 1 nature of CoreIdentity.

**Enables**:
- Adding real specialist nodes for non-core (supervisor detects non-core → route to new node instead of just "researching" message).
- Evolving CoreIdentity: make lookups/persists graph-routed steps, give it more smarts, own storage, etc.
- LLM-backed enrich/validator/specialists later.
- Keeping supervisor narrow.

See `docs/architecture.md` for the target, and TODO for the prioritized gaps.

## Local Debugging Tool: LangSmith Studio (LangGraph Studio)

As mentioned when discussing LangSmith setup, for visual debugging of the exact graph:

**Key distinction (this addresses the "why does it need the internet?" question):**

- `langgraph dev` (the in-memory/local CLI) runs the **backend** — your actual Mycelium graph code (the supervisor, the enrich/validator steps, CoreIdentity, storage, the LangGraph state machine, etc.) — **100% locally** on your computer.
- "Studio" is the name of the **visual debugging frontend/IDE**. The graph visualization, state inspector, interact mode, etc. are provided by a web application hosted at `smith.langchain.com/studio`.
- `--tunnel` is the bridge that makes *your local server* reachable from that external web UI (via a temporary Cloudflare tunnel). This is the part that touches the internet.
- The design gives a rich, always-up-to-date visual tool without shipping a full desktop app. The tradeoff is that the UI layer lives outside your machine.

Your code and data never leave the computer when tracing is off. If you want **zero internet at all**, simply do not use `--tunnel` and do not open the hosted Studio. Use the pure-local options below.

**For truly zero-internet / fully offline debugging (no tunnel, no external domains, no browser to smith.langchain.com):**

Use these options (all run entirely on your machine). The `./bin/run-studio` script (which does `langgraph dev --tunnel`) prints a convenient 🎨 Studio UI link with the `?baseUrl=...` already set — open that for the hosted visual when you want it.

1. **Direct Python (recommended for pure local, no server needed at all)**:
   ```python
   from graphs.core import get_core_graph, reset_core_graph
   from models.state import PersonQuery, MyceliumGraphState
   from storage.core import reset_storage
   import asyncio
   import os

   os.environ["LANGCHAIN_TRACING_V2"] = "false"
   reset_storage()
   reset_core_graph()

   graph = get_core_graph()
   q = PersonQuery(person_key="Nichanan Kesonpat")
   initial = MyceliumGraphState(query=q, invocation_thread_id="offline-test")
   # Use ainvoke + asyncio.run because the graph is compiled with AsyncSqliteSaver
   # (required for langgraph dev / Studio ASGI compatibility). run_query() does
   # equivalent wrapping for normal use.
   result = asyncio.run(
       graph.ainvoke(initial, config={"configurable": {"thread_id": "offline-test"}})
   )
   print("Response:", result.get("response") if isinstance(result, dict) else getattr(result, "response", None))
   # Add pdb.set_trace(), prints, etc. for debugging supervisor logic, state, etc.
   # (run the script under pdb or use breakpoint() inside nodes).
   ```
   This is completely offline. You can step through the exact same code paths the Studio would show.

2. **Local-only server (no tunnel, no external UI)**:
   ```bash
   LANGCHAIN_TRACING_V2=false uv run --with 'langgraph-cli[inmem]' langgraph dev --no-browser --host 127.0.0.1
   ```
   Starts the server at http://127.0.0.1:2024 on your machine only.
   - Call it from curl, Python requests, or any local tool on the same computer (e.g. POST to /runs/stream).
   - No Cloudflare, no smith.langchain.com involved.
   - You get the Agent Server API locally for testing inputs/inspecting runs.

See `.env.example` (Local development section) and the official LangGraph docs for more.

The hosted Studio + tunnel is convenient for the visual layer, but the project is fully usable and debuggable offline using the approaches above.

Note: "Failed to initialize Studio" / "TypeError: Failed to fetch" / "ConnectionError: Unable to connect..." is common with tunnels. Key gotcha: each `./bin/run-studio` run creates a *new temporary* Cloudflare subdomain. Old URLs (like ones from earlier banners) return 530 "Tunnel error" once the process stops. Always copy the live URLs from the *current running terminal's banner*, warm them up by visiting the plain API URL first in a browser tab, then use the manual "Connect to a local server" flow (not just the pre-filled link). See the detailed steps in the main README.md "Local Debugging" section (it now matches the official LangSmith Studio troubleshooting).

---

**This is the full original walkthrough structure, re-printed and refreshed with the context from our deep dives (especially the graph explanation, query vs. ingest distinction, and CoreIdentity reality vs. naming).**

The pieces fit as a deliberately minimal Phase 1 system that has been aggressively aligned (via many Cursor tasks) to the vision, but with acknowledged concessions (like CoreIdentity still being a facade + inline calls, enrich/validator only for core ingest).

If you'd like this saved as a permanent doc, more live demos (e.g. ingest now that you understand queries), a plan for evolving CoreIdentity, or to go back to the initial list of priorities/TODO to decide what to attack, just say.

(Original exploration used list_dir, multiple read_file on these exact paths, run_terminal_command for live queries/traces/graph inspection, etc. The above is synthesized directly from the current files.)