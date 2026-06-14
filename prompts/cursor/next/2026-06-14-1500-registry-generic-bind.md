# Program 3 — Slice 1500: Generic registry bind_values + bind_index

> **READY** — Claim per `prompts/cursor/WORKFLOW.md` before starting.

**Program:** [`docs/plans/entity-protocol-legacy-cleanup-program.md`](../../docs/plans/entity-protocol-legacy-cleanup-program.md)  
**Prerequisite:** Program 2 complete (`program_2` tag). No prior P3 slices required.

**Paul (D1):** **Option A** — `bind_values` only on `entities.json` rows; no top-level `name`/`employer` columns. Breaking changes OK.

---

## Objective

Make the registry row and `bind_index` **network-agnostic**: driven by `network.json` → `mvr.bind_fields`, not CRM hardcoding.

---

## Read first

- [`src/agents/entity_registry.py`](../../src/agents/entity_registry.py) — `RegistryEntity`, `make_bind_key`, `bind_index`
- [`src/agents/attribute_write.py`](../../src/agents/attribute_write.py) — `_apply_cache_field`, `write_bind_fields`, `ensure_entity_bind_fields`
- [`src/agents/field_index.py`](../../src/agents/field_index.py) — `_entity_field_value`
- [`src/network/seed_import.py`](../../src/network/seed_import.py)
- [`src/agents/target_resolve.py`](../../src/agents/target_resolve.py) — `_same_name_different_employer_suggestions` (uses `entity.name`)
- [`tests/test_entity_registry_bind.py`](../../tests/test_entity_registry_bind.py), [`tests/test_example_network.py`](../../tests/test_example_network.py)

---

## Locked design

### 1. `RegistryEntity` shape

**On disk (`entities.json`):**

```json
{
  "id": "uuid",
  "bind_values": {
    "name": "Andrea Kalmans",
    "employer": "Lontra Ventures"
  },
  "validation_state": "validated",
  "field_states": { "name": "validated", "employer": "validated" },
  "source": "seed_bootstrap",
  "created_at": "…"
}
```

- **Remove** top-level `name` and `employer` from the Pydantic model serialization (`model_dump` / JSON).
- Add helpers on `RegistryEntity` if useful for internal reads, e.g. `bind_value(field: str) -> str | None` — **not** serialized as duplicate columns.

### 2. Generic `bind_index`

Replace `make_bind_key(name, employer)` with **`make_bind_key(bind_values: dict[str, str], bind_fields: list[str])`**:

- For each field in `bind_fields` (in order), take normalized value from `bind_values` (same normalization as `field_index.normalize_field_index_value`).
- Join with `|`. All fields required for index key (full MVR bind tuple).
- `assign_bind_index` / `pop_bind_index` / `lookup_by_bind_key` → rename to **`lookup_by_bind_values(bind_values: dict[str, str])`** (or keep method name with new signature).

Duplicate-bind detection in `ensure_entity_bind_fields` uses **full** `bind_values` for all present MVR fields in the write, not hardcoded name+employer.

### 3. `attribute_write.py`

- `_apply_cache_field` → write into `entity.bind_values[field]`.
- `_cache_values` → return snapshot of `bind_values` for fields in `mvr.bind_fields`.
- `write_bind_fields` updates `bind_index` via generic key from old/new `bind_values`.
- `ensure_entity_bind_fields`: remove CRM-only `if "name" not in bind_values` unless replaced by policy (require all `mvr.bind_fields` for **new** entity allocation, or document which subset is required for seed — CRM seed still has name+employer per row).

Keep **`ensure_entity_bind(name, employer, …)`** as thin wrapper building `{"name": name, "employer": employer}` for seed import only (internal), or migrate seed_import to call `ensure_entity_bind_fields` directly.

### 4. `field_index.py`

- `_entity_field_value` reads **`entity.bind_values[field]`** only (remove name/employer branches).

### 5. `registry_entity_to_match`

Continue returning flat `name` / `employer` in match dicts for graph/response builders — **derived from `bind_values`**, not separate storage.

### 6. Seed import

- `seed.json` `people[]` rows stay `{name, employer}` for CRM examples.
- Import maps each row → `bind_values` per `mvr.bind_fields` before `ensure_entity_bind_fields`.

### 7. Hard cutover

- No migration layer reading old `name`/`employer` columns.
- Update test fixtures that construct `RegistryEntity(name=…)` or assert `entity["name"]` in JSON.

---

## Tests (smoke — mandatory)

| Test | Assert |
|------|--------|
| **Update** registry bind tests | `entities[id].bind_values`; `bind_index` keys use generic compound |
| **Update** `test_example_network` / refresh capstones | 15 seed rows; bind_index length 15 |
| **New:** `test_registry_entity_json_omits_top_level_name_employer` | Serialized entity has `bind_values`; no top-level `name`/`employer` keys |
| **New:** `test_make_bind_key_respects_bind_fields_order` | Unit test for compound key from `mvr.bind_fields` |

Keep `./bin/ci-local` green. Legacy `entity_key` tests may still pass via env flag until slice 1530/1540 — do not break them unnecessarily, but registry JSON assertions in touched tests must use `bind_values`.

---

## Out of scope (later slices)

- CLI `network status` / `resolve` JSON (1520)
- Removing `EntityQuery.entity_key` (1530)
- `required_bind_fields(entity_key,…)` removal (1510)

---

## Docs (this slice only)

- One-line note in [`docs/plans/entity-protocol-legacy-cleanup-program.md`](../../docs/plans/entity-protocol-legacy-cleanup-program.md) slice 1500 → done in `output.md` (Grok updates plan status after review).
- Do **not** edit `TODO.md`.

---

## Deliverable

`prompts/cursor/done/2026-06-14-1500-registry-generic-bind/` with `prompt.md`, `output.md`. Suggested commit:

```
feat(registry): generic bind_values and bind_index for MVR fields
```