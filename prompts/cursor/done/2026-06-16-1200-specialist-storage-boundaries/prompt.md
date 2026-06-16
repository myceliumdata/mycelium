# Specialist storage boundaries — eliminate framework storage coupling

> **READY** — Claim per `prompts/cursor/WORKFLOW.md` (move to `in-progress/` before starting).

**Context:** Paul + Grok agreed June 2026. Program 2’s unified write API (`attribute_write.py`) reaches into `agents/{category}/storage.json` directly. That violates the core philosophy: **specialists own storage strategy; nothing outside specialists should know how they store or manage data.** Baseball (multi-grain registries) makes the long-term direction clear: even `entities.json` should eventually move to an identity specialist; this slice fixes storage boundaries now while keeping registry/index maintenance in the framework temporarily.

---

## Locked decisions (Paul, June 2026)

| # | Decision |
|---|----------|
| S1 | **Framework (for now):** may route via taxonomy and maintain `entities.json` cache + indexes (`bind_index`, per-field indexes). |
| S2 | **Future:** `entities.json` ownership moves to an identity/registry specialist — design must not block that. |
| S3 | **Bootstrap:** registry-first import, then dispatch `bootstrap_entity` to owning specialists. |
| S4 | **Write sync:** specialists return current field values after writes; framework updates registry cache/indexes from responses only. |
| S5 | **Scope:** eliminate **all** framework code paths that read or write specialist storage directly — not a partial bind-only fix. |

---

## Read first

- `prompts/cursor/WORKFLOW.md`
- `docs/architecture.md` — “Everything is ultimately owned by specialist agents”
- `docs/plans/attribute-provenance-program2.md` — what Program 2 shipped (to unwind storage coupling, not indexes)
- `src/agents/attribute_write.py` — primary violator
- `src/agents/context.py` — reads all `storage.json` files
- `src/tools/research.py` — writes storage directly
- `src/agents/query_provenance.py`, `src/agents/entity_growth.py`, `src/network/introspection.py`
- `src/agents/specialists/base.py`, `src/agents/factory/templates/specialist_agent.py.j2`
- `src/network/seed_import.py`, `src/agents/target_deliver.py`
- `tests/test_program2_bootstrap_matrix.py`, `tests/test_example_network_capstones.py`

---

## Objective

Introduce a **specialist I/O protocol** invoked by the framework. Refactor every bind, seed, research, provenance, and context path so framework code **dispatches to specialists** and syncs `entities.json` from returned values — never opening `SpecialistStorage` or knowing `records` / `versions[]` layout outside the specialists package.

**External behavior unchanged:** CRM refresh + query capstones, empty-crm create-on-deliver, provenance mode, research writes, admin entity views must still pass existing smoke tests (updated assertions where they currently peek at `storage.json` from framework/integration tests).

---

## Architecture target

```
Framework                          Specialists (opaque)
─────────                          ────────────────────
taxonomy routing                   write_fields(entity_id, fields, actor)
entities.json cache + indexes  ←──  returns {field: current_value, ...}
dispatch bootstrap_entity    ──→  bootstrap_entity(entity_id, fields)
dispatch read_fields         ←──  read_fields(entity_id, fields[, provenance])
```

- **`SpecialistStorage`** and **`specialist_fields` append/load helpers** are **implementation details** inside `src/agents/specialists/` (committed specialists + factory template + generated network specialists).
- Framework modules **must not** `import SpecialistStorage` or read `agents/*/storage.json` paths.
- Add a **boundary test** (e.g. `tests/test_specialist_storage_boundaries.py`) that fails if any module under `src/` outside `src/agents/specialists/` imports `SpecialistStorage` or `agents.specialists.base` for storage I/O. Allowlist only the protocol/dispatch module if it must live adjacent (prefer keeping dispatch under `src/agents/specialists/`).

---

## Implement

### 1 — Specialist protocol + dispatch

Add protocol surface (location TBD — prefer `src/agents/specialists/protocol.py` or `io.py`):

| Function | Role |
|----------|------|
| `resolve_owner(field) -> (category, agent_name)` | Existing taxonomy resolution (may wrap `attribute_write.resolve_attribute_owner`) |
| `dispatch_write_fields(agent_name, entity_id, fields, *, actor_kind, source, validation_state)` | Load specialist module; call `write_fields`; return current values dict |
| `dispatch_read_fields(agent_name, entity_id, fields, *, include_versions=False)` | For context/provenance |
| `dispatch_bootstrap_entity(agent_name, entity_id, fields, *, actor_kind="seed_bootstrap")` | Seed/create bootstrap |
| `dispatch_read_category_slice(agent_name, entity_ids, fields)` | Replace `context.py` bulk file load |

Each committed specialist (`demographic_specialist`, `professional_specialist`, `contact_specialist`, `social_specialist`) and the **factory template** must expose module-level handlers:

```python
def write_fields(entity_id: str, fields: dict[str, str], *, actor_kind: str, at: str | None = None) -> dict[str, str]: ...
def read_fields(entity_id: str, fields: list[str], *, include_versions: bool = False) -> dict[str, Any]: ...
def bootstrap_entity(entity_id: str, fields: dict[str, str], *, actor_kind: str) -> dict[str, str]: ...
```

Implementation uses `SpecialistStorage` + `specialist_fields` **inside** the specialist module only.

**Registry sync helper** (may live in `attribute_write.py` renamed/refocused): given returned current values + entity metadata, update `RegistryEntity.bind_values`, `bind_index`, field indexes, `validation_state`, `source` — **no storage file access**.

### 2 — Refactor write entry points

Route these through dispatch + registry sync:

- `ensure_entity_bind_fields` / `write_bind_fields` (replace direct `_apply_specialist_bind_writes`)
- `seed_import.import_seed_file` — **two-phase:**
  1. Create registry rows (uuid4, bind_values cache, indexes) — or allocate ids then sync after bootstrap
  2. For each MVR field, dispatch `bootstrap_entity` to owning specialist
- `target_deliver.bind_provisional_from_scope` — dispatch write, not direct storage
- `tools/research.py` — research result persistence via `dispatch_write_fields` on the owning specialist (actor `research`)

Preserve actor kinds: `seed_bootstrap`, `bind`, `research`, `operator` (schema only if no UI yet).

Preserve multi-category rollback behavior from Program 2 polish (snapshot/rollback if one specialist write fails mid-bind).

### 3 — Refactor read entry points

- **`context.py`:** remove `SpecialistStorage` loop. Build specialist context slices via `dispatch_read_category_slice` (or per-agent `read_fields`) for registered agents only.
- **`query_provenance.py`:** provenance timelines via `dispatch_read_fields(..., include_versions=True)`.
- **`entity_growth.py`:** diagnostics via dispatch read API.
- **`network/introspection.py`:** do not construct or expose `storage.json` filesystem paths as the public introspection contract. Admin may list registered agents and categories; storage location/strategy is specialist-internal (or opaque “managed by specialist”).

### 4 — Factory + create paths

- **`agent_factory.py`:** may still create storage dirs as part of specialist provisioning, but factory setup is specialist-lifecycle code — move storage initialization into specialist module init or a `specialists/setup.py` helper **inside** the specialists package. Framework registry records `assigned_agent` only; avoid documenting/storage-path coupling in non-specialist modules.
- **`network/create.py`:** same rule — no direct `SpecialistStorage` from `network/`.

### 5 — Move / confine helpers

- **`specialist_fields.py`:** move to `src/agents/specialists/fields.py` (or keep path but enforce import boundary test). Only specialists package + tests for specialist units may import it.
- **`specialists/__init__.py`:** export protocol dispatch; do **not** re-export `SpecialistStorage` to framework consumers.

### 6 — Tests

| Requirement | Detail |
|-------------|--------|
| Boundary test | No forbidden imports outside specialists package |
| CRM capstone | `test_matrix_a_crm_refresh_seed_bootstrap_storage` still passes — assert via dispatch read or query deliver, not raw `storage.json` reads from test body unless testing specialist module directly |
| empty-crm | create-on-deliver still passes |
| attribute_write tests | Update to mock dispatch or test via specialist unit tests |
| provenance | `test_query_provenance` green |
| research | `test_specialist_sync_research` / `test_research` green |

**Negative fixture rule** (`WORKFLOW.md`): cold-start tests must not pre-call storage helpers the production path does not call.

### 7 — Docs (minimal, task-scoped only)

- Short addendum in `docs/architecture.md` § Supervisor / seed bootstrap: framework dispatches to specialists; registry cache is derived from specialist responses; `entities.json` registry ownership is temporary.
- Update `docs/plans/attribute-provenance-program2.md` with a “Superseded for storage I/O” note pointing at new boundary — do not rewrite the whole program doc.

---

## Success criteria

- [ ] `./bin/ci-local` green
- [ ] Grep: no `SpecialistStorage` import in `src/` outside `src/agents/specialists/` (except allowlisted protocol if unavoidable — justify in `output.md`)
- [ ] Grep: no `storage.json` path reads in `src/agents/context.py`, `src/tools/research.py`, `src/agents/query_provenance.py`, `src/network/introspection.py`
- [ ] CRM refresh: 15 entities; seed bootstrap versions exist with `actor.kind == seed_bootstrap` (verified via dispatch read or provenance)
- [ ] empty-crm create-on-deliver: step 2 `found`; bind versions `actor.kind == bind`
- [ ] Query + provenance smoke behavior unchanged for existing CRM examples
- [ ] Factory-generated specialists include `write_fields` / `read_fields` / `bootstrap_entity` in template

---

## Out of scope

- Baseball / Lahman / warehouse bootstrap
- Multi-grain / multi-registry `entities.json` (future identity specialist)
- Operator edit UI (Program 3)
- Changing MVR bind field definitions or public query API shape
- **`TODO.md`** — do not edit; note changes in `output.md` → “For Grok + Paul”

---

## May modify

- `src/agents/specialists/**`
- `src/agents/attribute_write.py` (refactor to dispatch + registry sync)
- `src/agents/context.py`, `src/agents/query_provenance.py`, `src/agents/entity_growth.py`
- `src/agents/target_deliver.py`, `src/network/seed_import.py`
- `src/tools/research.py`
- `src/agents/factory/**`
- `src/network/introspection.py`, `src/network/create.py` (storage coupling only)
- `tests/**` as needed
- `docs/architecture.md` (short addendum only)

---

## Deliverables (WORKFLOW completion checklist)

1. `./bin/ci-local` green
2. `prompts/cursor/done/2026-06-16-1200-specialist-storage-boundaries/`
   - `prompt.md` (this file)
   - `output.md` with **For Grok + Paul**: doc follow-ups, identity-specialist future note, suggested commit message
3. Do **not** commit; do **not** edit `TODO.md`

Suggested commit message:

```
refactor(specialists): enforce storage boundaries via dispatch protocol

Framework routes writes/reads through specialist handlers; registry
cache/indexes sync from returned values. Seed bootstrap is registry-first
then specialist bootstrap_entity. Eliminates direct SpecialistStorage
access outside specialists package.
```