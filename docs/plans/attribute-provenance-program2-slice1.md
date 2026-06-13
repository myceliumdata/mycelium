# Program 2 — Slice 1: Unified write + MVR in specialist storage

**Status:** Ready (June 2026)  
**Program:** [`attribute-provenance-program2.md`](attribute-provenance-program2.md)  
**Depends on:** Program 1 shipped; MVR redesign M1–M10 shipped

---

## Objective

Introduce a **unified attribute write API** for MVR bind fields. Canonical values and `versions[]` live in **taxonomy-owned specialist storage**; `entities.json` holds cache + protocol + indexes only. Route all bind/create entry points through the API.

No query provenance / admin timeline changes in this slice (Slice 2). No research prompt operator block yet (Slice 3).

---

## Implement

### 1 — Taxonomy bootstrap

- Add `name` to **demographic** `examples` and `employer` to **professional** `examples` in [`docs/examples/sample-categories.json`](../examples/sample-categories.json).
- Ensure `attribute_map` includes `"name": "demographic"`, `"employer": "professional"`.
- On `network create` / ontology materialization paths that copy sample categories, MVR bind fields are mapped.
- Add helper `resolve_attribute_owner(attribute: str) -> (category, assigned_agent)` using loaded `categories.json` (classification engine or thin wrapper). **Fail loud** when an `mvr.bind_fields` field is missing from `attribute_map`.

### 2 — `src/agents/attribute_write.py` (new)

Core functions (names may vary; behavior locked):

| Function | Behavior |
|----------|----------|
| `write_bind_fields(entity_id, fields: dict[str, str], *, actor, source, validation_state?)` | For each MVR field: append/init version in owning specialist storage; update registry cache columns; update `bind_index` + field indexes |
| `ensure_entity_bind(name, employer, *, source, validation_state)` | Allocate id if needed; delegate to unified write (replaces inline body of `ensure_bound_entity` for field values) |

**Version body (bind / seed / create):**

```json
{
  "id": "v1",
  "at": "<iso>",
  "status": "found",
  "value": "<string>",
  "actor": { "kind": "bind" | "seed_bootstrap", "category": "...", "specialist": "..." }
}
```

**Indexes:**

- Recompute or incrementally update `bind_index` via existing `make_bind_key(name, employer)` for CRM v1.
- Call `EntityRegistry` field index rebuild after entity save (existing `_rebuild_field_indexes`).

**Replace policy:** When an existing entity’s bind field value changes, remove old normalized keys from field indexes and `bind_index` before adding new keys (no aliases).

### 3 — `src/agents/entity_registry.py`

- Refactor `ensure_bound_entity` / `bind_provisional` to call `attribute_write` for field persistence.
- Registry row still stores cached `name` / `employer` for hot reads.
- **Do not** add `bind_versions[]`.

### 4 — Entry-point wiring

- `src/network/seed_import.py` — seed bootstrap binds use unified write (`actor: seed_bootstrap`).
- `src/agents/target_deliver.py` — `bind_provisional_from_scope` uses unified write for all `mvr.bind_fields` present in scope lookup (CRM: name + employer); remove hardcoded field loop where possible.

### 5 — `src/agents/specialists/base.py`

- Update default `storage_strategy.json` notes: MVR bind fields **may** be stored in specialist `storage.json` when network uses Program 2 strategy (bump strategy id or add `mvr_field_ownership: taxonomy` flag).
- Extended attrs remain `versioned_provenance_v1`.

### 6 — Tests

Add `tests/test_attribute_write.py`:

- Bind creates specialist `versions[]` for name + employer in correct categories.
- Entity row cache matches current version values.
- `bind_index` + `field_indexes` match after bind.
- Replace employer updates indexes; old key no longer resolves.
- Unmapped MVR field → clear error.
- `import_seed_for_test` + `bind_provisional_from_scope` integration smoke.

Update existing tests that assume MVR values exist **only** on registry row without specialist storage — refresh fixtures or assert both cache + specialist versions.

### 7 — Docs (minimal)

- [`attribute-provenance-and-storage.md`](attribute-provenance-and-storage.md) — mark Program 2 Slice 1 decisions implemented (no `bind_versions`).
- One paragraph in [`architecture.md`](../architecture.md) § Storage: MVR canonical values in taxonomy-owned specialist storage; entity row is cache.

---

## Do NOT (Cursor lane)

- Do not add `bind_versions[]` on entity rows.
- Do not change `QueryResponse.provenance` or admin field timelines (Slice 2).
- Do not add operator edit endpoints (Program 3).
- Do not add research prompt operator deference (Slice 3).
- Do not edit `TODO.md`.
- Do not hardcode CRM category map in Python — use `attribute_map`.

---

## Smoke expectations

- `./bin/ci-local` green.
- CRM two-step bind (existing MVR smoke) still passes with specialist storage populated for name/employer.
- `mycelium network status --entity` still shows bind values (from cache).

---

## Paul decisions (locked)

| # | Decision |
|---|----------|
| P2-1 | No entity-level history |
| P2-3 | Taxonomy ownership |
| P2-5 | Replace indexes, no aliases |
| P2-7 | Hard cutover / refresh to reset |