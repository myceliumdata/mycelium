# Entity ID unification — Slice 13 (uuid4 everywhere)

**Status:** Shipped (June 2026)
**Track:** Seed elimination (step 1 of N)  
**Depends on:** Entity program Slices 1–12 shipped  
**Follow-on:** Slice 14 — remove runtime seed resolution; import-only `seed.json`

---

## Objective

Use **one ID allocation strategy** (`uuid4`, opaque, immutable) for all entities. Retire seed's `uuid5(name|employer)` path. Persist IDs in **`entities.json`** via `bind_index` so MCP's per-query seed reload keeps stable foreign keys into specialist storage.

This slice **does not** remove `agents/seed.py` or seed-based resolution yet. It removes the **dual UUID algorithm** and makes the registry the **ID persistence layer** for bootstrap rows.

---

## Why this slice exists

| Today | Problem |
|-------|---------|
| Seed loader | `uuid5("mycelium-seed-v1:" + name\|employer)` at enrich time |
| Registry bind | `uuid4()` on new provisional row |
| MCP `refresh_runtime_from_disk` | `reset_seed_data()` + reload seed **every query** |

Naively swapping seed to uuid4 without persistence would assign **new IDs on every MCP query**, orphaning specialist storage keyed by `entity_id`. uuid5 masked this because reload was deterministic.

**Fix:** ID authority = `entities.json` `bind_index`. Allocate uuid4 once per bind key; reuse on seed reload.

---

## Locked decisions

| # | Decision |
|---|----------|
| D1 | **Canonical rule:** `entity_id` is allocated once, never derived from MVR, never recomputed on reload |
| D2 | **Allocator:** `uuid4()` only — delete uuid5 seed namespace (`_ID_PREFIX`, `_ID_NAMESPACE`) |
| D3 | **Persistence:** `EntityRegistry` `bind_index` is the reuse authority (`make_bind_key(name, employer)`) |
| D4 | **Seed bootstrap rows:** `source: "seed_bootstrap"`, `validation_state: "validated"` (same gating as today) |
| D5 | **Query bind rows:** unchanged — `source: "query_bind"`, start `provisional`, promote via Slice 5 path |
| D6 | **Duplicate bind key:** idempotent — existing row wins regardless of `source` |
| D7 | **No deterministic import IDs** — demos/tests do not require stable UUIDs across full network wipe |

---

## Implementation plan

### 1 — Shared registry helper

Add to `src/agents/entity_registry.py` (names indicative):

```python
def ensure_bound_entity(
    self,
    name: str,
    employer: str,
    *,
    source: str,
    validation_state: str,
) -> tuple[RegistryEntity, bool]:
    """Return entity for bind key; allocate uuid4 + persist if missing.

    ``bool`` is True when an existing row was returned (duplicate bind).
    """
```

- Lookup `make_bind_key(name, employer)` in `bind_index`
- On miss: `id = str(uuid.uuid4())`, write row + index, `_save()`
- On hit: return existing row (do **not** change `id`, `source`, or `validation_state`)
- Refactor `bind_provisional` to call `ensure_bound_entity(..., source="query_bind", validation_state="provisional")` then apply duplicate-bind semantics already tested

### 2 — Seed loader uses registry

In `src/agents/seed.py`:

- Remove `_ID_NAMESPACE`, `_ID_PREFIX`, uuid5 logic from `_assign_id`
- Replace enrich path with registry `ensure_bound_entity` for each `name` + `employer` (employer `""` if absent — use normalized empty string consistently with bind key)
- `_enrich_person` sets `id` from returned `RegistryEntity.id`
- Import `get_entity_registry` / handle reset in tests (registry singleton resets already in fixtures)

**Note:** Seed file still has no `id` column. IDs live in `entities.json` after first load.

### 3 — Legacy SQLite seed path

`src/storage/core.py` `seed_from_file` imports `_assign_id` from seed today. Update to:

- Use the same `ensure_bound_entity` helper (or call seed enrich path), **or**
- `allocate_entity_id()` only if row already has explicit `id` in JSON (legacy)

Prefer: delegate to registry helper for consistency.

### 4 — Runtime reload

No change to `refresh_runtime_from_disk` call pattern. After this slice, reload sequence:

1. `reset_entity_registry()` — **add to** `refresh_runtime_from_disk` before seed reload (if not already reset elsewhere)
2. `reset_seed_data()` + `get_seed_data()` — seed enrich consults registry on disk → stable ids

Verify `reset_entity_registry()` is invoked in MCP refresh path. Today `runtime.py` resets seed but **not** entity registry — **add** `reset_entity_registry()` + reload so seed enrich reads fresh `entities.json` from disk.

### 5 — Docs (task-scoped only)

Update live descriptions (not historical plan archives):

- `src/agents/seed.py` module docstring
- `docs/architecture.md` — seed loader / ID allocation paragraph
- `docs/full-code-walkthrough.md` — seed loader bullet
- `README.md` — only if it mentions uuid5 (grep first)

Add one line to `docs/plans/entity-protocol-and-registry-program.md` slice map (Slice 13 entry).

**Do not edit `TODO.md`** (Cursor governance).

---

## Behavior changes (intentional)

| Scenario | Before | After |
|----------|--------|-------|
| First seed query for Andrea Kalmans | uuid5 id; no registry row | uuid4 id; row in `entities.json` (`seed_bootstrap`) |
| MCP second query same person | same uuid5 | same uuid4 (bind_index reuse) |
| `refresh-example-network` (wipes entities) | uuid5 restored | new uuid4s (acceptable) |
| Paul Murphy `query_bind` after seed row exists | separate ids possible | **bind_index idempotent** — if same name+employer already in registry from seed, bind returns existing id |
| Protocol test M12 note | "no entities.json write for seed hit" | **Obsolete** — seed hit creates/updates registry mirror |

---

## Non-goals

- Remove `find_by_key` / seed resolution order
- Delete `seed.json` from examples
- `bin/import-seed` standalone script (Slice 14)
- MVR / `identity_schema` versioning (separate design)
- Change `scope_hash`, metering, or quote flow
- Edit `TODO.md`

---

## Tests

### Required updates

| Area | Action |
|------|--------|
| New unit tests | `ensure_bound_entity`: new row → uuid4; duplicate → same id; seed vs query_bind source preserved on duplicate |
| MCP reload stability | New test: two `get_seed_data()` cycles with registry persisted → same `find_by_key("Andrea Kalmans")[0]["id"]` |
| `test_entity_registry_bind` | Confirm seed-preexisting bind does not create second id |
| Growth / protocol | Update any assertion that seed hits leave `entities.json` empty |
| Full suite | `uv run pytest -m smoke -q` and metering/registry tests |

### Acceptance patterns (unchanged)

Tests should continue to:

- Capture `id` from response step 1, compare step 2
- Never hardcode literal UUID strings

---

## Exit criteria

- [x] No `uuid5` in `src/` (grep clean)
- [x] `bind_provisional` and seed enrich share registry-backed allocation
- [x] MCP refresh path resets + reloads entity registry before seed
- [x] Two-pass seed reload test proves stable ids with persisted `entities.json`
- [x] Smoke + entity registry/growth/validation tests green
- [x] `uv run ruff check src tests`

---

## Follow-on — Slice 14 (outline only)

1. `bin/import-seed` / fold into `refresh-example-network` — write all seed rows to registry, drop runtime `get_seed_data()` from resolution
2. Remove seed branch from `resolve_entity`
3. Suggestions scan registry
4. Delete `agents/seed.py` when no imports remain

---

## Cursor prompt

`prompts/cursor/done/2026-06-10-1000-entity-uuid4-unification-slice13/`