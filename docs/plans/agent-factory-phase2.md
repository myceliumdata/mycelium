# Plan: Agent Factory - Phase 2 (Dynamic Specialist Agent Creation)

**Status:** Draft for review/approval. This is the comprehensive implementation plan produced in the Grok session (Plan Mode). It builds directly on the approved high-level at `docs/plans/agent-factory-phase2.md` and follows the exact style, structure, depth, and slice approach of the published `docs/plans/classification-engine-phase1.md`.

> **Historical note (June 2026):** The "Current state" section below reflects the codebase at plan time. The live public API uses `EntityQuery` / `entity_key` / `query_entity` / `QueryResponse`; `core_data` was removed in the seed-data-context redesign. See `docs/architecture.md`.

> **Lightweight priority (from high-level + Phase 1 precedent):** Keep every slice small, explicit, and reviewable. Prioritize end-to-end creation trigger + template render + file write + registry update + dynamic in-process load + git commit + dispatch routing before any polish (LLM refine, extra docs, mcp enhancements). Use `auto_commit=False`, env var overrides (`MYCELIUM_*_PATH`), and file-based loading for all tests — never pollute src/ or run real git commits inside pytest. Generated agents **must** be committed to git on real runs (this is a core requirement). Supervisor must stay thin. All artifacts (py + registry.json + data/agents/<cat>/*) are first-class committed source. Clear hooks for future storage self-evolution from day one. Reference `docs/plans/agent-factory-phase2.md`, `docs/plans/supervisor-intelligence-v1.md`, `docs/architecture.md`, and `prompts/system/CORE_PROMPT.md` in all work.

## Context
This plan is for **Phase 2 only** of the Supervisor Intelligence work, as defined in the authoritative high-level plan at `docs/plans/agent-factory-phase2.md` (read and internalized first) and the original roadmap in `docs/plans/supervisor-intelligence-v1.md`.

From the Phase 2 high-level:
- Phase 1 (Classification Engine) is complete. The supervisor now classifies requested_attributes (with on-demand LLM for first-seen unknowns + caching, plus batch `refresh_from_llm`).
- When the supervisor encounters a category whose `assigned_agent` (e.g. "contact_specialist") does not yet have a registered, loadable specialist implementation, it must dynamically create one.
- Core requirements: safe template-driven (Jinja2 + optional LLM refinement) code generation; automatic registration + loading (current process + on restart); each specialist starts with its own simple flat JSON storage; clear architectural hooks (`storage_strategy.json` + methods in base) so agents can later autonomously evolve their backing store (flat JSON → MiniSQL → Postgres → cloud, etc.).
- Guiding principles: Supervisor remains thin (coordinator/router only); generated agents are first-class committed source code (with prominent auto-generated header); start lightweight, explicit, and Pythonic; maximize reviewability and debuggability.

**Current state (from codebase exploration):**
- `src/agents/supervisor.py`: Thin coordinator (~52 lines). Runs classification for every non-core `requested_attributes` (which may trigger LLM inside `classify()` for first-time unknowns, then caches). Always forces `route="core_data"` with comment "Phase 1: classification is metadata only. Real specialist routing comes in Phase 2+." Injects `classifications` list and audit strings for known categories. No creation logic, no use of `assigned_agent` for routing.
- `src/graphs/core.py`: Static compiled graph. Hardcoded `add_node("core_data", core_data_agent)`, `Route = Literal["core_data", "__end__"]`, `_route_after_supervisor` only understands "core_data", conditional edges map only that. `run_query` + singleton + async/sync checkpointer paths. No dispatch mechanism. Eager init at import (skipped under pytest).
- `src/models/state.py`: `route: Literal["core_data"] | None`; `classifications: list[dict]` (from Phase 1); `audit_log` (Annotated add); core `Person`/`PersonQuery`/`PersonResponse` unchanged.
- `src/agents/core_data.py`: The sole implemented specialist today. `_coerce`, core lookup via `get_core_identity()`, `response_found`/`response_non_core`/`response_not_found` builders, includes `classifications` in payload. Sets `route: None` on return.
- `src/agents/responses.py`: `debug_for_query` (tolerant of non-str via repr), `response_non_core` emits the generic "we're still researching {attrs}" narrative + classifications in debug. No `specialist` param yet.
- `src/agents/classification/` (engine.py + models.py): Complete and evolved from the Phase 1 plan. `classify()` is hot-path (pure lookup for known; first-time unknowns may call LLM once via `_llm_propose_for_attributes` + conservative merge + cache-as-unknown for garbage). `data/categories.json` is committed + has 6 categories (contact/social/relationships/demographic/professional/financial) with forward-looking `assigned_agent` values ("*_specialist"); none of those specialists exist as code yet. `refresh_from_llm` is the explicit off-path batch path. Singleton + `reset_category_tree` + `MYCELIUM_CATEGORIES_PATH` env.
- `src/storage/core.py` + `src/agents/core_identity.py`: The exact singleton/reset/env/default-path/atomic patterns that new registry and per-specialist storage must emulate.
- No specialists or factory yet: `src/agents/` contains only the flat agents + `classification/` subpackage. No `specialists/`, no `factory/`, no `registry.py`, no `dispatch.py`.
- `data/`: `categories.json` present/committed (and updated by prior LLM use); `agent_registry.json` and `data/agents/<category>/` subtree do not exist.
- `pyproject.toml`: No `jinja2`. Python 3.12+, langchain-openai etc. already present (usable for optional refine). ruff/mypy/pytest configured.
- `tests/`: `conftest.py` cleans singletons (storage, core_graph, core_identity, category_tree). `test_supervisor_routing.py` has smoke tests for `supervisor_agent` (asserts route=="core_data" and classifications) + many classification tests (mocks for LLM parts). `test_core_graph.py` has `@pytest.mark.full` tests using `temp_storage` fixture (env overrides + resets + real `run_query`). Legacy `agents.routing` still imported in a few tests.
- `src/mycelium_mcp/server.py`: `list_specialist_routing()` is an explicit Phase 1 stub (returns empty datasets + message about no persisted registry).
- `src/agents/__init__.py`: Only re-exports `supervisor_agent` + `core_data_agent`.
- `docs/architecture.md`: Explicitly states supervisor is thin coordinator/router, specialists (future) own domains + their storage strategy, no god agents, classification provides the metadata, "If no suitable agent exists, the system should support creating one." Full specialist handoff still marked future.
- Git is active (branch main, prior commits including `data/categories.json`). No gitpython dep (will use `subprocess` + `git` CLI for commits — available in the dev environment).
- Cursor workflow (`prompts/cursor/WORKFLOW.md` + done/ slices for Phase 1): Work is delivered as timestamped prompt files in `prompts/cursor/next/`. This plan describes the slices in detail (like the 7-step Phase 1 plan) but **does not create any Cursor prompt files** (per explicit directive).
- No existing template, jinja, or agent generation code anywhere.

**Phase 2 Goal (Agent Factory + dynamic routing):** Give the supervisor the ability to *use* the `assigned_agent` from classifications. When a non-unknown category's assigned agent name is not yet present in the registry (or loadable), the supervisor triggers the Agent Factory (minimal code in supervisor). The factory renders a Jinja2 template (strong, explicit, matching core_data style) + optional LLM refinement, writes the `.py` under `src/agents/specialists/`, inits per-category flat JSON storage + `storage_strategy.json`, updates `data/agent_registry.json`, commits the artifacts to git with a clear message, and dynamically loads the agent fn (via `importlib.util.spec_from_file_location` for test isolation + normal import for committed) so the current process can route to it immediately. On restart the registry + committed files make the specialist available automatically. A tiny static dispatch node in the graph makes arbitrary route names work without recompiling or adding nodes per specialist. Core data remains the fallback; specialists are generated on demand for the taxonomy already present in categories.json. Everything stays lightweight, explicit, reviewable, and prepared for storage self-evolution.

All design must be lightweight/Pythonic/explicit/Pydantic-where-sensible/extensible (for embeddings, more dynamic behavior, SQLite-backed specialist stores later). Supervisor changes minimal. Generated code is committed source (never ephemeral).

## Proposed Final File/Folder Structure
Keep changes localized and aligned with existing layout (`src/agents/`, `data/`, `docs/`, `tests/`). All modifications are small and reviewable. Follow the folder convention in CORE_PROMPT.md.

**Files that will be created or modified (exact list for scope boxes in Cursor prompts):**

```
mycelium/  (project root)
├── data/
│   ├── agent_registry.json                 # NEW: committed seed (starts with core_data entry) + runtime updates when new specialists created. Atomic save like categories.json. Git-tracked.
│   └── agents/
│       └── <category>/                     # NEW per-specialist subtree (created on first use of a category)
│           ├── storage.json                # Flat JSON store (initially {"version":"1.0","records":{},"last_updated":...}). Committed (small start).
│           └── storage_strategy.json       # Evolution hooks (strategy, supported upgrades, last_migrated). Committed. Clear extension point.
├── src/
│   ├── agents/
│   │   ├── __init__.py                     # (no change or tiny re-export if convenient; keep minimal)
│   │   ├── supervisor.py                   # MINIMAL: ~12-15 line addition after classify loop — if non-unknown assigned_agent not in registry, call factory.create_specialist (side-effect), set route=agent_name instead of always "core_data"; audit for creation + routing.
│   │   ├── core_data.py                    # MINOR: pass specialist="core_data" to response_* builders (for consistent debug/message).
│   │   ├── responses.py                    # SMALL: extend response_non_core(..., specialist: str | None = None). Use it in message ("... researching X (via contact_specialist).") and debug when present. Keep backward compat for core_data calls.
│   │   ├── registry.py                     # NEW: AgentRegistry + RegisteredAgent (pydantic or simple), atomic load/save, _SEED with core_data, env MYCELIUM_AGENT_REGISTRY_PATH, has_agent/get_agent_fn (core special-case + file-spec load for generated using MYCELIUM_SPECIALISTS_DIR), register, list, singleton get_/reset_agent_registry().
│   │   ├── dispatch.py                     # NEW: specialist_dispatcher(state) — tiny. Looks up current.route (or "core_data"), gets fn from registry, calls it. Logs dispatch target.
│   │   ├── factory/                        # NEW self-contained subpackage (colocated; easy to promote/refine later)
│   │   │   ├── __init__.py
│   │   │   ├── agent_factory.py            # AgentFactory + get_/reset_agent_factory. Jinja2 env, create_specialist (validate, render, write py+header, init SpecialistStorage for cat, build entry, registry update, dynamic load for current process, optional llm refine, _commit_artifacts via subprocess if auto_commit).
│   │   │   └── templates/
│   │   │       └── specialist_agent.py.j2  # The single template (explicit, matches core_data style, uses base storage, handles classifications for its cat, falls back to research narrative).
│   │   └── specialists/
│   │       ├── __init__.py                 # from .base import SpecialistStorage
│   │       └── base.py                     # SpecialistStorage (per-cat flat JSON + strategy.json writer/reader, atomic, ensure dirs, current_strategy, migrate_to stub with comments for future agent-owned evolution). No god logic.
│   │       # + generated files (e.g. contact_specialist.py, financial_specialist.py) — committed with AUTO-GENERATED header; first-class source.
│   └── graphs/
│   │   └── core.py                         # SMALL: generalize Route to str | None, replace hardcoded core_data node + conditional with "specialist" dispatch node + always-dispatch _route_after_supervisor (returns "specialist" or "__end__"), import + wire specialist_dispatcher, update docs/comments/run_query strings.
│   └── models/
│       └── state.py                        # TINY: route: str | None = None (was Literal["core_data"]), update field description. No other changes.
├── tests/
│   ├── test_supervisor_routing.py          # Update existing smoke (pre-register agents or use tmp registry so classify test still works; add test for creation trigger with fake create + route change). Add registry smoke if not in dedicated test.
│   ├── test_core_graph.py                  # Update temp_storage fixture (add registry + specialists dir envs + resets). Enhance non_core test to tolerate/observe specialist routing + "via X" in debug if present.
│   ├── test_agent_factory.py               # NEW (smoke + logic): create with auto_commit=False + tmp dirs, verify py written with header, storage/strategy created, registry updated, fn loadable via get_agent_fn (exercises file-spec load), second create is no-op, refine stub test with mock.
│   └── conftest.py                         # Add reset_agent_registry (and reset_agent_factory if it has state) to the session cleanup tuple.
├── docs/
│   └── plans/
│       └── supervisor-intelligence-v1.md
│       └── agent-factory-phase2.md         # The high-level (reference only; do not edit)
│       └── agent-factory-phase2-plan.md    # or equivalent name for this published plan (stable snapshot after approval).
├── pyproject.toml                          # Add "jinja2>=3.1.0" to dependencies (via `uv add jinja2` in Step 1).
└── (explicitly untouched or minimal in Phase 2)
    - src/mycelium_mcp/server.py (list_specialist_routing can be enhanced in polish step to return real list from registry; not required for core success).
    - src/main.py, src/agents/core_identity.py, legacy (routing.py, enrich/*, person_prep, validator), storage/core.py (patterns only), most tests.
    - No changes to public PersonQuery/PersonResponse shape or CLI/MCP query surface.
```

Rationale:
- `data/agent_registry.json` + `data/agents/<cat>/` follow the `data/categories.json` + storage conventions (committed seed, env override for tests, atomic save).
- `src/agents/registry.py` is a peer to `supervisor.py` (narrow, explicit). Factory is a subpackage like `classification/`.
- `src/agents/specialists/` holds only generated + their base (first-class, git-tracked, reviewable).
- Minimal delta to supervisor (the intelligence + creation trigger point), graphs (the one-time dispatch abstraction), state (one type change), responses + core_data (propagate specialist name for observability).
- Resets + env + fixture updates required for isolation (exact pattern from Phase 1 + storage).
- No public API change. Creation is lazy/on-demand. Git commits are an explicit feature (not side effect).
- Later (post Phase 2): pre-generate the rest of the taxonomy, move core_data into specialists/ if desired, richer multi-specialist routing or specialist-to-specialist handoff, real data in specialist stores, agents editing their own .py or strategy via internal coordination.

## Detailed Design of the Agent Factory, Registry, Base Specialist, and Jinja2 Templates

### Agent Registry (src/agents/registry.py + data/agent_registry.json)
Fast in-memory lookup of agent fns. Persistent JSON. Core data pre-registered (non-generated). Generated entries added by factory only.

Pydantic models (lightweight; can live at top of registry.py or a small models.py — prefer single file for Phase 2 to keep slice count low):

```python
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Any

class RegisteredAgent(BaseModel):
    """A registered specialist (core or generated)."""
    name: str  # e.g. "core_data", "contact_specialist"
    category: str
    description: str
    module_path: str  # "agents.core_data" or "agents.specialists.contact_specialist"
    entrypoint: str   # "core_data_agent" or "contact_specialist"
    storage_path: str | None = None
    strategy_path: str | None = None
    is_generated: bool = False
    created_at: str | None = None  # iso

class AgentRegistryData(BaseModel):
    version: str = "1.0"
    last_updated: datetime
    agents: dict[str, RegisteredAgent]  # name -> entry (name is key, no dup)
```

`AgentRegistry` class (mirrors CategoryTree exactly for familiarity):
- `__init__(registry_path: Path | None = None)`
- `_default_registry_path()` using `os.getenv("MYCELIUM_AGENT_REGISTRY_PATH", "data/agent_registry.json")`
- `_load`, `_save` (atomic tempfile + os.replace, mkdir, model_dump_json)
- `_create_seed()` from embedded `_SEED_REGISTRY`
- `reload`, `has_agent(name)`, `get_agent_fn(name) -> Callable | None`, `register_agent(entry: dict | RegisteredAgent, *, save=True)`, `list_agents() -> list[dict]`
- The critical loader (supports test isolation):

```python
import importlib
import importlib.util
import os
import sys
from pathlib import Path
...

def _load_agent_fn(self, entry: RegisteredAgent) -> Callable[[Any], dict] | None:
    if entry.name == "core_data" or entry.module_path == "agents.core_data":
        from agents.core_data import core_data_agent
        return core_data_agent
    # Generated: support custom dir (tests) via file spec; fall back to normal import for committed
    specialists_dir = Path(os.getenv("MYCELIUM_SPECIALISTS_DIR", "src/agents/specialists"))
    py_file = specialists_dir / f"{entry.name}.py"
    if py_file.exists():
        spec = importlib.util.spec_from_file_location(f"dyn_specialist_{entry.name}", str(py_file))
        if spec and spec.loader:
            mod = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = mod
            spec.loader.exec_module(mod)
            return getattr(mod, entry.entrypoint, None)
    # Fallback for normal committed layout
    try:
        mod = importlib.import_module(entry.module_path)
        return getattr(mod, entry.entrypoint, None)
    except Exception:
        return None
```

Module singletons + `get_agent_registry()`, `reset_agent_registry()` exactly like category tree.

**Initial seed content** (committed `data/agent_registry.json` must match the effect of `_SEED_REGISTRY`):

```json
{
  "version": "1.0",
  "last_updated": "2026-06-03T00:00:00+00:00",
  "agents": {
    "core_data": {
      "name": "core_data",
      "category": "core",
      "description": "Core identity (id, name, employer) — the always-present fallback specialist.",
      "module_path": "agents.core_data",
      "entrypoint": "core_data_agent",
      "storage_path": null,
      "strategy_path": null,
      "is_generated": false,
      "created_at": null
    }
  }
}
```

(Exact match required between committed JSON and the constant in registry.py; verified by "delete registry json, re-run" smoke.)

### Base Specialist (src/agents/specialists/base.py)
Common storage helper + future upgrade hooks. No business logic.

```python
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

class SpecialistStorage:
    """Per-specialist flat-JSON storage with explicit strategy metadata for future self-evolution.

    Each generated specialist gets its own directory under data/agents/<category>/.
    The specialist code (committed) can later contain intelligence that decides when
    to call .migrate_to(...) based on its own data volume, query patterns, etc.
    """

    def __init__(self, category: str, base_dir: Path | None = None) -> None:
        self.category = category
        self.base_dir = (base_dir or Path(os.getenv("MYCELIUM_AGENT_DATA_DIR", "data/agents"))) / self._slug(category)
        self.storage_file = self.base_dir / "storage.json"
        self.strategy_file = self.base_dir / "storage_strategy.json"
        self._ensure_initialized()

    def _slug(self, c: str) -> str:
        return c.strip().lower().replace(" ", "_").replace("-", "_")

    def _ensure_initialized(self) -> None:
        self.base_dir.mkdir(parents=True, exist_ok=True)
        if not self.strategy_file.exists():
            strategy = {
                "strategy": "flat_json_v1",
                "version": "1.0",
                "last_migrated": None,
                "upgrade_path": {
                    "flat_json_v1": {
                        "description": "Simple per-agent JSON file. Suitable for small-to-medium specialist datasets.",
                        "next_candidates": ["minisql_v1"]
                    }
                }
            }
            self._atomic_write(self.strategy_file, strategy)
        if not self.storage_file.exists():
            initial = {
                "version": "1.0",
                "last_updated": datetime.now(timezone.utc).isoformat(),
                "records": {},  # person_id or key -> specialist data blob (future schema per cat)
                "meta": {"created_by": "agent-factory"}
            }
            self._atomic_write(self.storage_file, initial)

    def _atomic_write(self, path: Path, payload: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        data = json.dumps(payload, indent=2)
        fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=".json.tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(data)
            os.replace(tmp, path)
        except Exception:
            try:
                os.unlink(tmp)
            except Exception:
                pass
            raise

    def load(self) -> dict[str, Any]:
        if not self.storage_file.exists():
            self._ensure_initialized()
        return json.loads(self.storage_file.read_text(encoding="utf-8"))

    def save(self, data: dict[str, Any]) -> None:
        data = dict(data)
        data["last_updated"] = datetime.now(timezone.utc).isoformat()
        self._atomic_write(self.storage_file, data)

    def get_strategy(self) -> dict[str, Any]:
        if not self.strategy_file.exists():
            self._ensure_initialized()
        return json.loads(self.strategy_file.read_text(encoding="utf-8"))

    def current_strategy(self) -> str:
        return self.get_strategy().get("strategy", "flat_json_v1")

    def migrate_to(self, target: str) -> None:
        """Future hook for agent self-managed storage evolution.

        A specialist agent (the generated .py) can decide (based on its own data volume,
        access patterns, config, or even LLM advice) to call this. Base implementation
        can later contain actual migration (copy data, swap files, update strategy json).
        For Phase 2 this is a deliberate no-op / documented extension point.
        """
        current = self.current_strategy()
        if current == target:
            return
        # Placeholder — real migration code will live here or in a mixin added later.
        # The specialist .py itself (being editable committed source) can grow the
        # intelligence that decides *when* to call migrate_to.
        raise NotImplementedError(
            f"Storage migration from {current} to {target} not implemented in this "
            f"version of the {self.category} specialist. "
            "Edit the specialist or extend base.py to add migration logic."
        )
```

`__init__.py` simply re-exports `SpecialistStorage`.

### Jinja2 Templates
One template for now: `src/agents/factory/templates/specialist_agent.py.j2`

Full content (lightweight, explicit, mirrors core_data.py structure + comments, uses base storage, pulls attrs from state.classifications when present, always populates core results via CoreIdentity, uses research narrative for Phase 2):

```jinja2
"""{{ agent_name }} — auto-generated specialist agent for category "{{ category }}".

AUTO-GENERATED by Agent Factory on {{ created_at }}.
Category: {{ category }}
Description: {{ description }}
Examples: {{ examples | join(", ") if examples else "(none at creation)" }}

DO NOT EDIT THIS FILE BY HAND UNLESS YOU MEAN IT.
- Preferred: edit the template (src/agents/factory/templates/specialist_agent.py.j2) and re-generate via factory.
- Acceptable: edit this file directly (it is committed source). Future readers will see the header.
- Storage strategy + data live beside this file in data/agents/{{ category }}/ (see storage_strategy.json).
- Future storage evolution hooks are in agents/specialists/base.py (migrate_to etc.). The specialist
  code itself can later contain the intelligence that decides when to evolve its store.

This specialist owns its domain data and storage. It is a first-class peer to core_data.
"""

from __future__ import annotations

from typing import Any

from agents.specialists.base import SpecialistStorage
from agents.core_identity import get_core_identity
from agents.responses import debug_for_query, response_non_core, response_not_found
from models.state import MyceliumGraphState, Person


_storage: SpecialistStorage | None = None


def get_specialist_storage() -> SpecialistStorage:
    """Lazy per-module storage (respects MYCELIUM_AGENT_DATA_DIR for tests)."""
    global _storage
    if _storage is None:
        _storage = SpecialistStorage(category="{{ category }}")
    return _storage


def _coerce(state: MyceliumGraphState | dict[str, Any]) -> MyceliumGraphState:
    if isinstance(state, MyceliumGraphState):
        return state
    return MyceliumGraphState.model_validate(state)


def _resolve_invocation_ids(state: MyceliumGraphState) -> tuple[str | None, str | None]:
    return state.invocation_thread_id, state.invocation_trace_id


def {{ agent_name }}(state: MyceliumGraphState | dict[str, Any]) -> dict[str, Any]:
    """
    Specialist agent for the "{{ category }}" category.

    Resolves the person via CoreIdentity (so results stay consistent), then
    "looks up" in its own store (initially empty → research narrative).
    Later versions of this specialist can return real data from storage and
    can decide to evolve the storage strategy.

    This is a synchronous function (supports both invoke and ainvoke paths).
    """
    current = _coerce(state)
    identity = get_core_identity()
    matches: list[Person] = identity.find_by_key(current.query.person_key)

    my_store = get_specialist_storage()
    thread_id, trace_id = _resolve_invocation_ids(current)
    id_kwargs = {"thread_id": thread_id, "trace_id": trace_id}
    clf_kwargs = {"classifications": current.classifications} if current.classifications else {}

    # Which attrs does this specialist own for this query? Prefer classifications (Phase 2 source of truth).
    my_attrs: list[str] = []
    for c in (current.classifications or []):
        if c.get("category") == "{{ category }}" and c.get("attribute"):
            my_attrs.append(c["attribute"])
    if not my_attrs:
        # Fallback: take requested that look relevant (coarse but safe for initial specialists)
        my_attrs = [a for a in current.query.requested_attributes]

    if not matches:
        resp = response_not_found(current.query, **id_kwargs, **clf_kwargs)
        outcome = "not_found"
    else:
        # Phase 2: specialists start with the same "researching" narrative as core_data non-core.
        # The specialist= kwarg (added in responses) makes the provenance visible.
        resp = response_non_core(
            current.query,
            matches,
            my_attrs or ["{{ category }} data"],
            specialist="{{ agent_name }}",
            **id_kwargs,
            **clf_kwargs,
        )
        outcome = "specialist_researching"

    store_snapshot = my_store.load()
    record_count = len(store_snapshot.get("records", {}))
    logs = [
        f"{{ agent_name }}: lookup {outcome} for person_key={current.query.person_key!r} (category={{ category }}).",
        f"{{ agent_name }}: specialist store has {record_count} record(s).",
    ]

    payload: dict[str, Any] = {
        "response": resp,
        "route": None,
        "audit_log": logs,
        "persons": matches,
        "classifications": current.classifications or [],
    }
    if len(matches) == 1:
        payload["person"] = matches[0]
    if current.invocation_thread_id is not None:
        payload["invocation_thread_id"] = current.invocation_thread_id
    if current.invocation_trace_id is not None:
        payload["invocation_trace_id"] = current.invocation_trace_id
    return payload
```

(The template is reviewed as part of the plan + Step 4. It produces runnable, style-consistent code.)

Example rendered output (for "contact" / "contact_specialist") is essentially the above with the literals substituted + the header timestamp.

### Agent Factory Implementation Notes
- Jinja2 env created once in the factory instance (lazy via get_agent_factory).
- `create_specialist(..., auto_commit: bool = True)` — the production path sets True; tests and the trigger in supervisor can be made safe via the implementation (see risks + steps).
- Git commit also stages the registry.json + the two storage files for the category (so a single atomic-feeling commit captures "new specialist + its initial storage").
- Optional refine path is clearly separated, temperature 0, with guard that the improved code still contains the expected `def <agent_name>(`.
- All paths respect the same env overrides used by registry for isolation.

## How the Supervisor Will Trigger Agent Creation (Minimal Changes)
Current supervisor is still small. We add creation + routing logic **only** for non-core requested attributes that have a concrete assigned_agent from classification.

**Realistic small diff** (the only material change in supervisor):

```diff
 from __future__ import annotations

 from typing import Any

 from agents.classification import get_category_tree
+from agents.factory import get_agent_factory
+from agents.registry import get_agent_registry
 from models.state import MyceliumGraphState


 def _coerce(state: MyceliumGraphState | dict[str, Any]) -> MyceliumGraphState:
     ...

 def supervisor_agent(state: MyceliumGraphState | dict[str, Any]) -> dict[str, Any]:
     ...
     if query.requested_attributes:
         ...
         for attr in ...:
             cl = tree.classify(attr)
             ...
+    # Phase 2: use classification to pick a real specialist. Create on demand if needed.
+    route = "core_data"
+    if classifications:
+        for cl in classifications:
+            cat = cl.get("category")
+            ag = cl.get("assigned_agent")
+            if cat and cat != "unknown" and ag and ag != "core_data":
+                reg = get_agent_registry()
+                if not reg.has_agent(ag):
+                    factory = get_agent_factory()
+                    factory.create_specialist(
+                        category=cat,
+                        agent_name=ag,
+                        description=cl.get("description") or f"Data related to {cat}.",
+                        examples=[],
+                        llm_refine=False,
+                        # auto_commit is True in real runs; tests isolate via env + pytest guard inside factory
+                    )
+                route = ag
+                break
+
     audit_log.append(f"Supervisor: routing to {route} specialist.")
     ...
```

Audit can be extended with an explicit "created new specialist X for category Y" line (easy one-liner before/after the if).

This is the **only** place creation is triggered. Supervisor stays a pure coordinator.

## Updates to Graph, State, Dispatch, Responses, Core Data (Minimal but Necessary)
- `state.py`: `route: str | None = None` (drop Literal; update description to mention it now drives dispatch to any registered specialist).
- `graphs/core.py`: Introduce `specialist_dispatcher`; change wiring to a single "specialist" node after supervisor; generalize the conditional and Route type; update every comment/docstring that mentioned the old hardcoded core_data path. The dispatch is the abstraction that makes dynamic routes work without per-agent nodes or runtime graph rebuilds.
- New `dispatch.py` (tiny, ~25 LOC):
  ```python
  def specialist_dispatcher(state: ... ) -> dict:
      current = _coerce(state)
      target = current.route or "core_data"
      fn = get_agent_registry().get_agent_fn(target)
      if fn is None:
          from agents.core_data import core_data_agent
          fn = core_data_agent
      # Optional: audit "Dispatch: invoking {target}"
      return fn(current)
  ```
- `responses.py` + `core_data.py`: One-line param + conditional message tweak so provenance is visible when a real specialist (vs core_data) handled the non-core part. Core calls pass `specialist="core_data"` for consistency; generated code passes its own name.

These changes are small, localized, and fully described with diffs in the Cursor slices.

## Risk / Mitigation Section (Focus on Generated Code Quality, Git, Storage Hooks)
- **Generated code quality / "bad" specialists**: Strong, hand-written, reviewed Jinja2 template (the source of truth) + prominent auto-generated header + git commit (human reviews the exact diff before/after the fact). Optional LLM refine is off by default, runs only when explicitly requested, and is still committed for review. No free-form "LLM write me an agent" — everything is templated + small delta.
- **Git clutter / noisy commits**: Clear conventional messages ("feat(agents): auto-generate contact_specialist for category 'contact'"). One commit per creation (includes the .py + registry.json + the two storage sidecars). Acceptable for Phase 2; batching or "pending creations" queue can be added later if volume becomes an issue. All artifacts are intentional and reviewable.
- **Test isolation (writes + git + imports)**: Factory and registry fully respect `MYCELIUM_AGENT_REGISTRY_PATH` + `MYCELIUM_SPECIALISTS_DIR`. `create_specialist(..., auto_commit=False)` (default behavior under pytest via guard). Dynamic load always prefers `spec_from_file_location` when the file lives under the (possibly tmp) specialists dir. No src/ pollution, no real commits, no sys.path hacks. Full matrix includes "delete registry, re-run" + tmp dir scenarios.
- **Future storage intelligence hooks missing or weak**: `SpecialistStorage` + `storage_strategy.json` + `migrate_to` stub + explicit comments in base.py and every generated specialist from day one. Because the specialist .py is committed editable source, the "agent" (its code) can later grow the decision logic ("if len(records) > N: self.storage.migrate_to(...)") without any central change. This is the deliberate architectural hook requested.
- **Name collisions / duplicate agents / bad names**: Strict validation in factory.create (regex ^[a-z][a-z0-9_]*_specialist$, no reserved, registry as source of truth before write). Category dir is derived from the category (stable).
- **Supervisor no longer thin / god logic leaks**: Creation trigger is a 10-15 line explicit if + one call. All real work lives in factory/registry/dispatch. Audit makes the decision visible. Matches architecture.md and CORE_PROMPT ("no god-agents", "supervisor narrow").
- **Restart / persistence of generated agents**: Registry json is committed; generated .py files are committed under specialists/. On import of registry the fns are loaded (core special-cased, others via normal import or file spec). If a .py is manually deleted, next load fails gracefully (factory can recreate on next trigger, or human `git checkout`).
- **Hot-path LLM or expensive creation**: Creation only happens on first use of a never-before-seen assigned_agent for a non-unknown cat. Subsequent uses (and all restarts) are pure registry lookup + import or file load. LLM refine is opt-in and off by default. classify() LLM behavior is unchanged from Phase 1.
- **Scope creep (full specialist data, complex routing, moving core_data, etc.)**: Strict scope boxes per slice (files + "no edits outside listed"). Creation produces minimal viable specialists (research narrative + own store skeleton). Real data population, specialist-to-specialist calls, and richer graph topologies are explicitly future.
- **MCP / observability surface**: list_specialist_routing enhancement is polish-only. All new routing/creation is visible in existing audit_log + response.debug + state.route + state.classifications + LangSmith — no new public fields required.

All mitigations are implemented in the smallest possible way and reuse Phase 1 patterns.

## Step-by-Step Implementation Tasks for Cursor (Small, Reviewable)
Follow WORKFLOW.md + test policy + smoke-first strictly. Scope boundaries: only the files listed in the structure section (plus this plan). One small diff per step where possible. Reference this plan + agent-factory-phase2.md + architecture.md + CORE_PROMPT.

**Step 1: Scaffold + seed registry + jinja2 + package dirs + stubs (pure structure + data, zero behavior change)**
- Run `uv add jinja2` (updates pyproject.toml + uv.lock; this is the controlled way to introduce the dep).
- Create `data/agent_registry.json` with the exact initial seed JSON from the "Agent Registry" design section (only core_data entry).
- `mkdir -p src/agents/specialists src/agents/factory/templates`
- Create package files:
  - `src/agents/specialists/__init__.py` (will export later)
  - `src/agents/factory/__init__.py`
  - `src/agents/registry.py` (module doc + constants + _SEED_REGISTRY + stub functions that raise NotImplemented or return core_data for get)
  - `src/agents/factory/agent_factory.py` (stub class with create_specialist that raises or no-ops)
  - `src/agents/factory/templates/specialist_agent.py.j2` (the full template from the design section, or a minimal placeholder that will be filled in Step 4)
  - `src/agents/specialists/base.py` (stub SpecialistStorage that at least ensures dirs and returns empty dicts)
  - `src/agents/dispatch.py` (stub)
- No changes to any existing runtime .py yet. No tests modified.
- Verify: `git status`, `cat data/agent_registry.json | head -30`, `uv run python -c "
import jinja2, json, pprint
print('jinja2:', jinja2.__version__)
pprint.pprint(list(json.load(open('data/agent_registry.json'))['agents'].keys()))
"`, `uv run pytest -m smoke -q` (must be green).

**Step 2: Registry implementation + singletons + load logic + basic tests**
- Implement the full `src/agents/registry.py` (models, AgentRegistry class with atomic _save/_load exactly as in classification/engine.py, _default using MYCELIUM_AGENT_REGISTRY_PATH, seed, has/get/list/register, the _load_agent_fn with core special-case + spec_from_file_location path using MYCELIUM_SPECIALISTS_DIR, module-level get_agent_registry / reset_agent_registry).
- Update `tests/conftest.py`: import reset_agent_registry and add it to the cleanup tuple.
- Update/add smoke tests (preferably in test_supervisor_routing.py or a tiny addition): after reset, get_agent_registry() has "core_data", get_agent_fn("core_data") is callable and the real function, list_agents contains it, register works (in-memory + save to a tmp path).
- Verify: `uv run pytest -m smoke -q`; manual with env:
  `MYCELIUM_AGENT_REGISTRY_PATH=/tmp/test-reg-$$.json uv run python -c '
  from agents.registry import get_agent_registry, reset_agent_registry
  reset_agent_registry()
  r = get_agent_registry()
  print(r.has_agent("core_data"))
  print(r.list_agents())
  fn = r.get_agent_fn("core_data")
  print(fn)
  '`

**Step 3: Base SpecialistStorage (full, with strategy hooks)**
- Implement `src/agents/specialists/base.py` with the complete SpecialistStorage from the design (atomic writes, _ensure that writes both json files with the exact initial shapes, load/save, get_strategy/current_strategy, migrate_to stub with the explanatory comment for future agent self-evolution).
- `src/agents/specialists/__init__.py`: `from .base import SpecialistStorage; __all__ = ["SpecialistStorage"]`
- Add smoke test (in test_supervisor_routing.py or alongside): `from agents.specialists.base import SpecialistStorage; import tempfile, os; d=tempfile.mkdtemp(); s=SpecialistStorage("demo", base_dir=Path(d)); data=s.load(); assert "records" in data; s.save({"records":{"p1":{"email":"a@b"}}}); assert s.load()["records"]["p1"]; st=s.get_strategy(); assert st["strategy"]=="flat_json_v1"`.
- Verify: `uv run pytest -m smoke -q`; manual creation of a tmp specialist dir and inspection of the two json files.

**Step 4: Agent Factory (render + write + storage init + registry update + dynamic load + git + stub refine) + dedicated factory tests**
- Implement `src/agents/factory/agent_factory.py`:
  - Lazy jinja2.Environment pointing at the templates/ sibling.
  - create_specialist full body (name validation, early return if has_agent, render with all context vars the template needs, write the .py, instantiate SpecialistStorage(category) to ensure its files, build RegisteredAgent dict and call registry.register_agent, force a get_agent_fn to exercise the load path for current process, if auto_commit: _commit_artifacts, return rich summary dict).
  - `_commit_artifacts` (find repo root by walking for .git, git add the py + registry json + the two storage files for the cat, git commit -m "feat(agents): auto-generate {name} for category '{cat}'", best-effort, return bool).
  - `_refine_with_llm` stub (documented, returns original for now; will be filled later).
  - get_agent_factory / reset_agent_factory singletons (factory can take/hold a registry).
- Create `tests/test_agent_factory.py` (new file) with several @pytest.mark.smoke tests exercising create with auto_commit=False + monkeypatched or env-driven tmp registry + tmp specialists dir, assert files on disk, header present, fn callable and produces expected shape for a stub state, registry updated, second create no-op, storage files present with correct strategy.
- Verify: `uv run pytest -m smoke -q -k "factory or agent_registry"`; manual creation under env overrides (no real git commit, no src pollution):
  `MYCELIUM_AGENT_REGISTRY_PATH=/tmp/r.json MYCELIUM_SPECIALISTS_DIR=/tmp/s uv run python -c '
  ... reset...
  f = get_agent_factory()
  info = f.create_specialist("contact", "contact_specialist", "Direct contact info", auto_commit=False)
  print(info)
  print((Path("/tmp/s") / "contact_specialist.py").read_text()[:200])
  '`

**Step 5: Dispatch + graph wiring + state update + supervisor creation trigger + test adjustments**
- Create `src/agents/dispatch.py` with specialist_dispatcher (full small implementation from design, plus audit-style log).
- Update `src/models/state.py`: route type + description.
- Update `src/graphs/core.py`: imports, Route type, _route_after_supervisor, build_core_graph (add specialist node, conditional, edges; remove direct core_data node), update every docstring/comment that assumed the old shape, run_query docs.
- Update `src/agents/supervisor.py`: the creation trigger block (exact logic from "How the Supervisor..." section) + audit line for creation when it happens + update module docstring.
- Update tests that hard-assert route=="core_data" for the classification case:
  - In the existing classify test, pre-register the contact_specialist (via registry, save=False) so has_agent is true → route becomes the specialist name; update the assert.
  - Add a new smoke test `test_supervisor_triggers_creation_for_unregistered...` that uses a tmp registry (no contact entry), monkeypatches the factory.create_specialist to record the call, calls supervisor_agent with an email attr, asserts create was called with correct cat/name, and result["route"] == "contact_specialist".
- Verify: `uv run pytest -m smoke -q`; `uv run mycelium query --person-key "Nichanan Kesonpat"` (still works, route core_data); a non-core query at this point will hit the trigger (but see Step 6 for full isolation).

**Step 6: Responses + core_data propagation + full test fixtures + integration + mcp list (optional polish)**
- Update `src/agents/responses.py`: add `specialist: str | None = None` param to `response_non_core` (and optionally the others for symmetry), conditional message tweak + debug entry when specialist is truthy. Keep default=None for zero breakage.
- Update `src/agents/core_data.py`: pass `specialist="core_data"` at the two response_non_core / response_not_found / response_found call sites inside _build_lookup_response.
- Update `tests/conftest.py` and `tests/test_core_graph.py` temp_storage fixture: setenv MYCELIUM_AGENT_REGISTRY_PATH and MYCELIUM_SPECIALISTS_DIR to tmp paths, call reset_agent_registry() (and reset_agent_factory if needed) in setup and teardown. Update the non_core full test to assert the research message still appears and that classifications (or debug) reflect the specialist that handled it (now that dispatch + creation may have run inside the isolated tmp).
- Run full relevant tests: `uv run pytest -m full -q -k "non_core or query_non_core or supervisor or graph"`.
- Polish (fits in this slice because small): update `src/mycelium_mcp/server.py` list_specialist_routing to call get_agent_registry().list_agents() and return a real list (update its docstring from "Phase 1 stub").
- ruff on all touched files.
- Verify matrix (see Verification section).

**Step 7: LLM refine, final cross-checks, docs touch, full verification + cleanup**
- Fill the real body of `_refine_with_llm` in agent_factory.py (lazy ChatOpenAI, explicit "review for style match with core_data.py, keep structure and explicitness, output only complete .py" prompt, temperature 0, guard that the agent fn def is still present, return improved or original).
- Add a smoke test for the refine path (fake llm that returns a slightly modified code string; assert factory used it when llm_refine=True).
- Small high-value doc updates only: 1-2 sentences in `docs/architecture.md` (supervisor / Derivative sections) + any TODO.md note.
- `uv run ruff check src/agents/registry.py src/agents/factory/... src/agents/specialists/... src/agents/dispatch.py src/agents/supervisor.py src/graphs/core.py ...`
- Full pytest smoke + the full non_core/graph subset.
- Final manual matrix (see Verification).
- After Cursor delivers a slice: read its output.md + review.md, re-run the verification commands yourself, write any follow-up notes.

## Verification (End-to-End + Regression)
Cursor must run these (smoke default; full for graph tests). Grok will re-run independently on review.

**Automated (must be green):**
- `uv run pytest -m smoke -q`
- `uv run pytest -m full -q -k "non_core or query_non_core or supervisor_agent or graph"`
- `uv run ruff check` on every file listed in the structure section.
- (Optional mypy if the project runs it on the touched modules.)

**Manual hot-path + creation (real git commit happens here):**
- Core only: `uv run mycelium query --person-key "Nichanan Kesonpat"` → route still "core_data" in audit, normal "Found core record", no creation side effects.
- Non-core that triggers creation (e.g. financial already in categories): `uv run mycelium query --person-key "Nichanan Kesonpat" --attributes net_worth` →
  - First run: audit contains "created new specialist financial_specialist for category 'financial'" (or equivalent), "routing to financial_specialist specialist."
  - response.message still contains "still researching" (or the via variant), results have the core person, debug contains the specialist name or classifications.
  - `git status` shows clean (the .py, registry.json, data/agents/financial/* were committed).
  - `git log --oneline -1 --stat` shows the auto-generated commit with the new files.
  - `cat src/agents/specialists/financial_specialist.py | head -20` shows the AUTO-GENERATED header, correct category, def financial_specialist, use of SpecialistStorage, call to response_non_core with specialist=...
  - `ls data/agents/financial/` shows storage.json + storage_strategy.json (both committed, small).
- Subsequent same attr: no "created" line, direct route, still works.
- Another category (e.g. email): creates contact_specialist (or uses if already created in prior manual step).
- Ambiguous name + attr (regression): `uv run mycelium query --person-key "Kevin Zhang" --attributes x_handle` → still 2 results, classifications + specialist routing visible, no breakage.

**Test isolation & creation without pollution:**
- With envs: `MYCELIUM_AGENT_REGISTRY_PATH=/tmp/r$$.json MYCELIUM_SPECIALISTS_DIR=/tmp/s$$ uv run python -c 'from agents.factory import ...; f=...; f.create_specialist("hobby", "hobby_specialist", "...", auto_commit=False); ...'` → writes only under /tmp, registry updated in /tmp, no src/ files, no git commit attempted.
- Full graph fixture test (non_core) now runs inside its own tmp registry + specialists dir; any creation that occurs stays in tmp.
- "Delete registry json" reseed: move data/agent_registry.json aside, run a core query → still works (falls back to _SEED), may rewrite the file. Restore after.

**Dispatch + restart load:**
- After a real creation: `uv run python -c '
from agents.registry import reset_agent_registry, get_agent_registry
reset_agent_registry()
r = get_agent_registry()
print("has financial_specialist:", r.has_agent("financial_specialist"))
fn = r.get_agent_fn("financial_specialist")
print("callable:", callable(fn))
# stub minimal state
from models.state import MyceliumGraphState, PersonQuery
s = MyceliumGraphState(query=PersonQuery(person_key="test"))
out = fn(s)
print("returned keys:", list(out.keys()))
print("response message snippet:", out.get("response").message[:80] if out.get("response") else None)
'`
- The fn works without re-creation.

**Observability / state / debug:**
- state.route (inspectable in Studio/LangSmith) is the specialist name when one was chosen.
- audit_log + response.debug surface the creation event (once) + the routing target + "via <specialist>" if responses updated.
- classifications list still present and correct.

**Git hygiene + committed artifacts:**
- After creation steps: the new specialist .py, updated agent_registry.json, and data/agents/<cat>/* are in the commit and in the tree.
- Header grep: `git grep -l "AUTO-GENERATED by Agent Factory" -- src/agents/specialists/`
- No stray files in src/ or data/ from test runs.

**No hot-path creation cost after first use + no LLM in creation unless asked:**
- Second query for same attr: no creation log line, no LLM call (unless you passed llm_refine=True explicitly in a manual factory call).
- Grep enforcement (in step 7): only factory code contains the jinja + ChatOpenAI for refine.

**After Cursor delivers each slice:**
- Read `prompts/cursor/done/<the-task>/output.md` + review.md + any diffs.
- Re-run the relevant verification subset above.
- Only then proceed or commit (per prior pattern).

## Success Criteria
- Supervisor can trigger creation of a new specialist for an unknown (to the registry) assigned_agent coming from classification, on first use of a non-core attr in that category.
- New agent .py is written, committed to git with clear message and header, registry + storage sidecars committed, dynamically loaded in the same process, and the query succeeds with correct specialist in the audit/routing path.
- After process restart the specialist is loadable from the committed registry + .py with zero creation.
- Generated code is clean, style-consistent, uses the base storage + strategy, and is reviewable as a normal source file.
- Clear, implemented hooks exist for future agent self-managed storage evolution (strategy json + migrate_to + comments in the generated specialist).
- All automated tests (smoke + relevant full) green; manual matrix (core, non-core creation, restart load, isolation, git) passes.
- Supervisor + graph changes were minimal and the dispatch abstraction keeps future routing flexible.
- System remains stable, observable, and debuggable. Ready for the next evolution of specialist intelligence.

This plan is self-contained, references the authoritative high-level documents, is scoped exactly to Phase 2 (Agent Factory + minimal routing support), follows all project conventions (WORKFLOW, smoke policy, reset singletons, env paths, atomic persistence, explicit code, small slices), and gives Cursor 7 small reviewable steps with exact commands, scope, and verification. Ready for exit_plan_mode + user review/approval before any Cursor prompt is created or implementation code is touched.

(End of plan)
