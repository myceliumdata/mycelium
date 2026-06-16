# Specialist agent class — OO autonomy + unified I/O path

> **READY** — Claim per `prompts/cursor/WORKFLOW.md` (move to `in-progress/` before starting).

**Context:** Paul + Grok (June 2026). The baseball example exposed that specialist storage/bootstrap is too slow and that the June 16 storage-boundaries slice fixed **framework coupling** but not **agent autonomy**. Today:

- `SpecialistStorage` is a shared JSON helper, not the agent.
- `handlers.py` implements all CRM specialists identically.
- `dispatch_write_bind_fields_multi` **bypasses** specialist module handlers and calls `handlers.write_bind_fields_multi` directly — so bootstrap/bind never reaches per-specialist logic.
- Generated specialists are module-level graph functions + thin `attach_protocol_handlers` wrappers.

**Paul's goal:** Each specialist is an **autonomous agent object**. Framework ships default agent **classes** users **subclass** to override behavior (storage policy, research, etc.). Centralized base class with overridable methods — classic OO extension model.

**This slice:** Introduce `SpecialistAgent` and route **all** specialist I/O (including multi-bind) through agent instances. **Do not** implement SQLite / `minisql_v1` yet — that is the **next** slice, enabled by per-agent `optimize_storage()`.

---

## Locked decisions (Paul, June 2026)

| # | Decision |
|---|----------|
| A1 | **Specialist = class instance**, not shared `handlers.py` procedures. |
| A2 | Framework ships **`SpecialistAgent` base** (or `TaxonomySpecialist`) with CRM-sensible defaults (JSON `versioned_provenance_v1`). |
| A3 | Users override by **subclassing** and registering their class (or replacing module `AGENT` singleton). |
| A4 | **`optimize_storage() -> bool`** lives on the agent class (default `False`). No global optimizer. |
| A5 | **All writes** including `write_bind_fields_multi` go through **agent instance methods** — no direct `handlers.write_fields(category, ...)` from protocol for production paths. |
| A6 | **Framework** still maintains `entities.json` cache + indexes temporarily (unchanged from slice 1200). |
| A7 | **Graph node entrypoint** (`demographic_specialist(state)`) delegates to `agent.run(state)` on the same instance — one object, two entry surfaces. |
| A8 | `handlers.py` may remain as **internal helpers** called **from** base class methods during migration, but protocol must not call `handlers` directly. |

---

## Read first

- `prompts/cursor/WORKFLOW.md`
- `docs/architecture.md` — specialists own storage; framework dispatches
- `prompts/cursor/done/2026-06-16-1200-specialist-storage-boundaries/prompt.md` + `review.md` (what shipped; honest limits §2–3)
- `src/agents/specialists/base.py` — `SpecialistStorage`
- `src/agents/specialists/protocol.py` — dispatch (note `dispatch_write_bind_fields_multi` bypass)
- `src/agents/specialists/handlers.py` — shared implementation to fold into base class
- `src/agents/specialists/_protocol_exports.py`
- `src/agents/factory/templates/specialist_agent.py.j2`
- `src/agents/registry.py` — `get_agent_fn`; extend for `get_agent_instance`
- `src/agents/attribute_write.py` — bind write path
- `tests/test_specialist_storage_boundaries.py`
- `tests/test_program2_bootstrap_matrix.py`, `tests/test_example_network_capstones.py`

---

## Architecture target

```
Framework                              SpecialistAgent (per category)
─────────                              ─────────────────────────────
resolve_owner(field)                   instance.write_fields(...)
dispatch_* → get_agent(name)    ──→    instance.read_fields(...)
write_bind_fields_multi         ──→    agent_a.write_fields + agent_b.write_fields
                                       (rollback via instance snapshots)
registry cache sync               ←──   returned current values
graph dispatch → entrypoint       ──→    AGENT.run(state)
```

**Extension model (document in architecture addendum):**

```python
class SpecialistAgent:
    def optimize_storage(self) -> bool: ...
    def write_fields(self, entity_id, fields, *, actor_kind, at=None) -> dict[str, str]: ...
    def read_fields(self, entity_id, fields, *, include_provenance=False) -> dict: ...
    def bootstrap_entity(self, entity_id, fields, *, actor_kind="seed_bootstrap") -> dict: ...
    def run(self, state) -> dict: ...  # graph node

class DemographicSpecialist(SpecialistAgent):
    category = "demographic"
    def optimize_storage(self) -> bool:
        return self.storage.record_count() >= 50  # example override
```

Each committed specialist module exposes:

```python
AGENT = DemographicSpecialist()
def demographic_specialist(state): return AGENT.run(state)
def write_fields(...): return AGENT.write_fields(...)
# attach_protocol_handlers may delegate to AGENT or be replaced by explicit exports
```

Registry resolution: `get_agent_instance(name) -> SpecialistAgent` via module attribute `AGENT` (preferred) or `get_agent()` factory; fall back to wrapping legacy module handlers only in tests if needed.

---

## Implement

### 1 — `SpecialistAgent` base class

Add `src/agents/specialists/agent.py` (or extend `base.py` if cleaner — prefer separate file to keep `SpecialistStorage` as storage backend):

- Constructor: `category`, `agent_name`, optional `storage: SpecialistStorage | None`.
- Move default JSON write/read/bootstrap logic from `handlers.py` into base methods (may call private helpers extracted from handlers).
- `optimize_storage(self) -> bool`: default `False`.
- Before each `write_fields` / `bootstrap_entity` save path: if `optimize_storage()`: call `self.migrate_to(...)` (stub/no-op OK if `migrate_to` still raises — hook must exist on agent, delegating to storage).
- `analyze_storage() -> dict` for admin/status (replaces direct `analyze_category_storage(category)` coupling where possible via agent instance).
- `record_count()` helper for policy (count records in storage).

### 2 — Default framework specialists

Refactor committed modules (`demographic_specialist`, `professional_specialist`, `contact_specialist`, `social_specialist`):

- Define `class XSpecialist(SpecialistAgent)` with `category` + `agent_name` set.
- Module singleton `AGENT = XSpecialist()`.
- Graph entrypoint: `return AGENT.run(state)` (move existing graph body into `run` on base or subclass).
- Module-level `write_fields` / `read_fields` / `bootstrap_entity` delegate to `AGENT.*`.

Update **factory template** `specialist_agent.py.j2` to generate the same pattern for new specialists.

### 3 — Registry + protocol

- `AgentRegistry.get_agent_instance(name) -> SpecialistAgent | None` — load module, return `AGENT` or call `get_agent()`.
- Refactor `protocol._call_handler` to prefer agent instance methods when `AGENT` present.
- **`dispatch_write_bind_fields_multi`:** resolve owning agent per field; call `agent.write_fields` per category; preserve Program 2 rollback (snapshot per agent storage before multi-write). **Remove** direct `handlers.write_bind_fields_multi` call from protocol.
- `dispatch_analyze_category_storage`: resolve agent by category mapping (`assigned_agent` from categories.json) → `agent.analyze_storage()`.
- Other dispatch functions: route through instance methods consistently.

### 4 — Confine `handlers.py`

- Either deprecate public functions and keep as thin wrappers around default `SpecialistAgent` logic, or move logic into `agent.py` and leave `handlers.py` as re-exports for backward compat inside specialists package only.
- **Boundary test** must still fail if framework imports `handlers` or `SpecialistStorage` directly.

### 5 — Tests

| Test | Requirement |
|------|-------------|
| `test_specialist_storage_boundaries.py` | Still green; update allowlist if needed |
| CRM capstones / Program 2 bootstrap matrix | Green — behavior unchanged |
| **New:** `test_specialist_agent_class.py` | Subclass override: custom `write_fields` or `optimize_storage` called via dispatch |
| **New:** `test_write_bind_fields_multi_routes_through_agent` | Mock/spy agent instance — handlers not called directly from protocol |
| Baseball refresh smoke (if fast enough) | Optional; may mock git seed |

Add unit test proving user override:

```python
class CountingSpecialist(SpecialistAgent):
    writes = 0
    def write_fields(self, ...):
        self.writes += 1
        return super().write_fields(...)
```

Dispatch bind write → `writes > 0` on that instance.

### 6 — Docs (minimal)

- `docs/architecture.md` short addendum: specialists are **classes**; framework dispatches to instances; users subclass to override storage/research; `handlers.py` is internal.
- Do **not** edit `TODO.md` (Cursor).

---

## Out of scope (follow-up slices)

- SQLite `minisql_v1` implementation (uses `optimize_storage()` hook from this slice)
- Entity registry `entities.json` → identity specialist
- Entity bootstrap deferred-save / entity SQLite
- Baseball-specific specialist subclasses (pitching warehouse, etc.)
- Removing `agents.specialists.fields` imports from framework modules (slice 1400 follow-up)

---

## Success criteria

1. `SpecialistAgent` base exists with overridable `optimize_storage`, `write_fields`, `read_fields`, `bootstrap_entity`, `run`.
2. All four committed CRM specialists use `AGENT = …Specialist()` pattern; factory template matches.
3. `dispatch_write_bind_fields_multi` routes through agent instances — **not** `handlers.write_bind_fields_multi` from `protocol.py`.
4. `get_agent_instance` (or equivalent) resolves agents from registry/modules.
5. `./bin/ci-local` green.
6. Boundary test green.
7. CRM refresh capstone + Program 2 bootstrap matrix green.

---

## Deliverables

Per `WORKFLOW.md`:

- `prompts/cursor/done/2026-06-17-1800-specialist-agent-class/prompt.md`
- `output.md` with verification counts + **For Grok + Paul** (note: enables SQLite storage slice next; baseball perf still needs entity batch save)
- Suggested commit message: `refactor(specialists): SpecialistAgent class; route all I/O through instances`
- **Do not commit or push**

---

## Suggested follow-up prompt (Grok will queue after approval)

`2026-06-17-1900-specialist-minisql-v1.md` — implement `migrate_to("minisql_v1")`, default `optimize_storage` thresholds per specialist subclass, baseball-scale bootstrap perf.