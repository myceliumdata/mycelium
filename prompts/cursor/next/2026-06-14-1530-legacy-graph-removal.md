# Program 3 — Slice 1530: Legacy graph and resolution removal

> **READY** — Claim per `prompts/cursor/WORKFLOW.md` before starting.

**Program:** [`docs/plans/entity-protocol-legacy-cleanup-program.md`](../../docs/plans/entity-protocol-legacy-cleanup-program.md)  
**Prerequisite:** Slices **1500–1520** approved.

---

## Objective

Remove the deprecated **entity_key + binding** query graph path and all public/internal resolution helpers that predate the target two-step protocol. After this slice, the only step-1 inputs are **`id`** and **`lookup`**.

---

## Read first

- [`src/models/state.py`](../../src/models/state.py) — `EntityQuery`, `entity_query_is_legacy_*`, `legacy_entity_key_allowed`
- [`src/agents/entity_resolution.py`](../../src/agents/entity_resolution.py) — `resolve_entity`, `resolve_entity_for_lookup`, `lookup_entities_by_key`, `lookup_by_name` usage
- [`src/agents/supervisor.py`](../../src/agents/supervisor.py) — legacy gate
- [`src/agents/dispatch.py`](../../src/agents/dispatch.py) — `target_resolve` legacy branch
- [`src/agents/routing.py`](../../src/agents/routing.py)
- [`src/agents/responses.py`](../../src/agents/responses.py) — `response_entity_unknown`, `entity_key_unresolved`, etc.
- [`src/agents/target_resolve.py`](../../src/agents/target_resolve.py) — `_same_name_different_employer_suggestions` (use field index not `lookup_by_name`)
- [`tests/conftest.py`](../../tests/conftest.py) — `MYCELIUM_ALLOW_LEGACY_ENTITY_KEY`

---

## Locked design

### 1. `EntityQuery` model

**Remove fields:**

- `entity_key`
- `binding`

**Remove helpers:**

- `entity_query_is_legacy_entity_key_step`
- `legacy_entity_key_allowed`

Update validators: step 1 requires `id` or non-empty `lookup`; step 2 requires `delivery_id`.

### 2. Remove functions / methods

- `resolve_entity()`, `resolve_entity_key()`, `resolve_entity_for_lookup()`
- `lookup_entities_by_key()` if only legacy
- `EntityRegistry.lookup_by_name()` — replace callers with **name field index** (`field_indexes()["name"]` or registry helper `lookup_by_field(field, value)`)

Keep: `resolve_status_for_target_lookup`, `resolve_target_step1`, target deliver path.

### 3. Supervisor + dispatch

- Remove legacy `entity_key` short-circuit branch in supervisor.
- Remove dispatch audit path “legacy entity_key — defer to supervisor”.
- Legacy single-step graph routing via `entity_key` — **gone**.

### 4. Legacy `QueryResponse` outcomes

Remove builders and outcome strings for public-retired outcomes, including:

- `entity_unknown`, `entity_key_unresolved`, `entity_bound_provisional`, `entity_validated`, `entity_under_specified` (as legacy names)

Target outcomes remain: `lookup_resolved`, `lookup_incomplete`, `lookup_suggested`, `found`, `assembled`, `not_found`, `quote_*`, `error`.

Update `QueryResponse` outcome Literal / field descriptions.

### 5. MCP / CLI schema

- Ensure `EntityQuery` JSON schema descriptions do not mention `entity_key` / `binding`.
- [`src/mycelium_mcp/server.py`](../../src/mycelium_mcp/server.py) — already mostly clean; verify.

### 6. Specialists / templates

Fix any remaining `query.entity_key` references (e.g. contact specialist error paths) → `query.id` or bind_values from context.

---

## Tests (smoke — mandatory)

| Test | Assert |
|------|--------|
| **Update** `test_mvr_polish_m10` | Remove `test_legacy_entity_key_disabled_without_env_flag` or replace with “entity_key rejected at model level” |
| **New:** `test_entity_query_rejects_entity_key_field` | `EntityQuery(entity_key="x")` raises validation error |
| **New:** `test_supervisor_no_legacy_entity_key_path` | No env flag needed; legacy field impossible |
| Keep target step-1 / deliver smokes green |

Slice **1540** will migrate the bulk of `entity_key` tests — this slice must leave **CI green** by updating or xfailing only tests that block removal (minimal fixes). Prefer updating critical smokes here; defer bulk migration to 1540.

`./bin/ci-local` green before completion.

---

## Out of scope

- Full test file deletion (1540)
- `describe_network` policy (1550)

---

## Docs

Do not edit `TODO.md`.

---

## Deliverable

`prompts/cursor/done/2026-06-14-1530-legacy-graph-removal/` — suggested commit:

```
refactor(query): remove legacy entity_key graph and resolution path
```