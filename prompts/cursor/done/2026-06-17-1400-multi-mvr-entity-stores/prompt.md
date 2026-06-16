# Multi-MVR entity stores — framework slice (no query graph changes)

> **READY** — Claim per `prompts/cursor/WORKFLOW.md` (move to `in-progress/` before starting).

**Context:** Paul + Grok agreed June 2026. The baseball program needs **one network, multiple MVR bind policies, multiple entity stores** ([`docs/plans/baseball-example-program.md`](../../../docs/plans/baseball-example-program.md) problem #1). Bootstrap handler selection via `network.json` is shipped. **This slice** adds the **framework plumbing**: manifest-declared grains, per-grain entity files, per-grain MVR load, bootstrap reset/write for the default CRM grain. **Query orchestration** (grain selection in `target_resolve` / supervisor) and **`LahmanSeedHandler`** are **follow-on slices**.

**Regression anchor:** CRM end-to-end unchanged from the caller’s perspective — `get_entity_registry()` with no grain arg, existing query smoke/capstone tests, 15 seed entities on CRM refresh, empty-crm still 0.

---

## Locked decisions (Paul, June 2026)

| # | Decision |
|---|----------|
| G1 | **Per-grain entity stores** under `<network_root>/entities/<grain>.json` (self-contained files; not one combined doc). |
| G2 | **`network.json` `mvr.grains`** declares each grain’s `bind_fields` + `description`. Optional per-grain `entities_file` (default `entities/<grain>.json`). |
| G3 | **`mvr.default_grain`** names the query/default grain when callers omit `grain`. When absent: use `person` for legacy flat `mvr.bind_fields`; for multi-grain manifests use first grain in `grains` (stable sort) or require `default_grain` — **prefer require `default_grain` when `len(grains) > 1`** (baseball must set it). |
| G4 | **Legacy CRM compat:** flat `mvr.bind_fields` (no `grains`) → implicit single grain **`person`** with same bind policy. No manifest migration required for old live roots, but **committed examples** should use explicit `mvr.grains.person` (see below). |
| G5 | **`load_mvr(grain=None)`** → default query grain policy. All existing call sites that omit `grain` keep current behavior. |
| G6 | **`get_entity_registry(grain=None)`** → default query grain store. Query graph code **does not** pass `grain` in this slice. |
| G7 | **`DefaultSeedHandler`** writes the **`person`** grain (CRM seed rows). If the network has no `person` grain, write to **`default_grain`** instead. |
| G8 | **`run_network_bootstrap`** resets **all** grain registries (in-memory). Runtime grain files are bootstrap output — skip copying `entities/` from committed examples (like `entities.json` today). |
| G9 | **Legacy file read:** if the resolved grain path (`entities/person.json`) is missing but `<network_root>/entities.json` exists, **read** the legacy path (backward compat for existing live CRM roots). **Writes** go to the grain path (`entities/person.json`). |
| G10 | **`MYCELIUM_ENTITIES_PATH`** continues to override the **default grain** entity store path only (unchanged env contract for query path). |

---

## `network.json` schema

### CRM (committed examples — explicit grains)

```json
"mvr": {
  "default_grain": "person",
  "grains": {
    "person": {
      "bind_fields": ["name", "employer"],
      "description": "CRM people: display name plus current employer before bind and research."
    }
  }
}
```

### Legacy (must still parse — do not require committed examples to keep this)

```json
"mvr": {
  "bind_fields": ["name", "employer"],
  "description": "..."
}
```

Equivalent to G4 implicit `person` grain.

### Baseball (manifest only — no Lahman data this slice)

```json
"mvr": {
  "default_grain": "player",
  "grains": {
    "player": {
      "bind_fields": ["name", "team"],
      "description": "Player identity: display name plus team disambiguator (draft)."
    },
    "team": {
      "bind_fields": ["name"],
      "description": "Fan-facing team: full canonical city+name (draft)."
    }
  }
}
```

Remove the stale placeholder `mvr.bind_fields` CRM-shaped block from `examples/networks/baseball/network.json` when adding `grains`. Keep `experiment` metadata if still useful.

---

## Read first

- `prompts/cursor/WORKFLOW.md`
- `src/network/mvr.py`
- `src/agents/entity_registry.py`
- `src/network/paths.py`
- `src/network/bootstrap/run.py`
- `src/network/bootstrap/handlers/default_seed.py`
- `src/network/seed_import.py`
- `src/network/create.py` — `--force` entity cleanup
- `src/network/example.py` — `_SKIP_NAMES`
- `src/network/introspection.py` — `describe_network` MVR summary
- `examples/networks/crm/network.json`, `empty-crm`, `crm-metering`, `baseball`
- `tests/test_network_bootstrap.py`, `tests/test_example_network.py`
- `docs/architecture.md` — entity registry / MVR sections

---

## Implement

### 1 — MVR config loader (`src/network/mvr.py`)

Add a small config layer without breaking existing `MvrPolicy` / helper signatures:

```python
@dataclass(frozen=True)
class NetworkMvrConfig:
    default_grain: str
    grains: dict[str, MvrPolicy]  # grain name → policy

def load_mvr_config(*, paths: NetworkPaths | None = None) -> NetworkMvrConfig: ...
def load_mvr(*, paths: NetworkPaths | None = None, grain: str | None = None) -> MvrPolicy: ...
def default_mvr_grain(*, paths: NetworkPaths | None = None) -> str: ...
def list_mvr_grains(*, paths: NetworkPaths | None = None) -> list[str]: ...
```

- Parse `mvr.grains` object; each value uses existing `_parse_mvr_block` rules.
- Legacy flat `mvr.bind_fields` → `NetworkMvrConfig(default_grain="person", grains={"person": ...})`.
- Invalid/missing grain name on `load_mvr(grain="foo")` → clear `ValueError`.
- Keep `can_create_on_zero_matches`, `missing_mvr_bind_fields`, etc. working via `load_mvr()` default grain.

### 2 — Per-grain entity store paths (`src/network/paths.py`)

```python
def entity_store_path(paths: NetworkPaths, grain: str) -> Path: ...
def resolve_entity_store_path(paths: NetworkPaths, grain: str) -> Path:
    """Grain path with legacy root entities.json fallback for read resolution."""
```

- `entity_store_path`: `paths.root / entities_file` from grain config, default `entities/<grain>.json`.
- `NetworkPaths.entities_path` (and `MYCELIUM_ENTITIES_PATH` derivation) = **default grain** store path via `entity_store_path(paths, default_mvr_grain(...))`.
- Document in code: legacy `entities.json` at root is read fallback only (G9).

### 3 — Per-grain `EntityRegistry` (`src/agents/entity_registry.py`)

- `EntityRegistry(path, *, grain: str, mvr: MvrPolicy | None = None)` — rebuild indexes from **that grain’s** `bind_fields` (stop calling bare `load_mvr()` inside instance methods when `mvr` is set; thread grain policy through `_rebuild_field_indexes`, `_bind_fields`, `lookup_by_target_lookup`, `promote_validated`).
- `get_entity_registry(*, grain: str | None = None) -> EntityRegistry` — per-grain singleton cache (`dict[str, EntityRegistry]`).
- `reset_entity_registry(*, grain: str | None = None) -> None` — `grain=None` clears **all** cached registries (bootstrap uses this).
- **Read path:** construct registry with `resolve_entity_store_path` (legacy fallback).
- **Write path:** always `entity_store_path` (grain file).

`registry_entity_to_match` stays CRM-shaped (`name`/`employer` from bind_values) — query graph unchanged.

### 4 — Bootstrap integration

**`run_network_bootstrap`:** keep `reset_entity_registry()` (all grains) before handler.

**`DefaultSeedHandler` / `import_seed_rows`:** accept optional `grain: str = "person"`; resolve registry via `get_entity_registry(grain=...)` with fallback to `default_mvr_grain()` when `person` absent. CRM behavior identical.

**Optional (nice):** extend `BootstrapResult` with `entities_by_grain: dict[str, int]`; set `entities_committed` = sum or default-grain count for backward compat in callers/tests.

**`network create --force` without seed:** unlink default grain store **and** any known grain paths from manifest (not only legacy `entities.json`).

### 5 — Example manifests + copy skip list

Update committed `network.json` for **crm**, **empty-crm**, **crm-metering** → explicit `mvr.default_grain` + `mvr.grains.person` (G4 schema above).

Update **baseball** → two-grain manifest (no seed data).

**`copy_example_network`:** skip runtime `entities/` directory (add to `_SKIP_NAMES` or equivalent). Keep skipping root `entities.json`.

### 6 — Introspection

**`describe_network` / network metadata:** expose multi-grain MVR when present, e.g.:

```json
"mvr": {
  "default_grain": "person",
  "grains": {
    "person": { "bind_fields": [...], "description": "..." }
  }
}
```

Legacy flat manifest → same shape as implicit `person` grain (do not expose two competing formats to clients).

### 7 — Tests

| Area | Assert |
|------|--------|
| MVR parse | legacy flat → `person`; explicit grains; baseball two grains; `default_grain` required when >1 grain |
| Paths | `entities_path` = `entities/person.json` for CRM manifest; legacy read fallback from root `entities.json` |
| Registry | separate files per grain; indexes use correct `bind_fields`; `get_entity_registry()` = default grain |
| Bootstrap | CRM seed → 15 rows in **person** grain file; `reset_entity_registry()` clears all grains |
| Refresh capstones | `test_refresh_crm_imports_seed_into_entities` reads `entities/person.json` (or default grain path); 15 entities |
| empty-crm | 0 entities after refresh |
| Baseball manifest | parses two grains; bootstrap commits 0 player/team rows (no Lahman handler) |
| Query smoke | existing `test_entity_*`, `test_mvr_*`, `test_example_network` capstones green — **no grain args added to query code** |

Add focused unit tests for `load_mvr_config`, `entity_store_path`, per-grain registry isolation (write person grain does not touch team grain file).

### 8 — Docs

Update **`docs/architecture.md`**:

- Per-grain entity stores at `entities/<grain>.json`.
- `mvr.grains` + `default_grain` schema; legacy flat `bind_fields` → implicit `person`.
- Legacy `entities.json` read fallback; writes to grain path.
- Explicit note: **query path still uses default grain only** until orchestrator slice.

Short note in **`docs/onboarding.md`** entity registry row (multi-grain layout).

**Do not edit `TODO.md`.**

---

## Explicit non-goals

- `LahmanSeedHandler` or any baseball warehouse ingest
- `target_resolve`, `supervisor`, or query graph grain selection
- Multi-alias player bind index (`name` + multiple teams → same uuid)
- Per-grain `categories.json` or specialist routing
- Identity specialist / moving registry ownership out of framework
- `bootstrap_experiment.py` disposition
- LLM alias resolution

---

## Exit criteria

| # | Criterion |
|---|-----------|
| E1 | `mvr.grains` + `default_grain` parse; legacy flat `mvr.bind_fields` → implicit `person` |
| E2 | Per-grain entity files at `entities/<grain>.json`; isolated registries |
| E3 | `load_mvr()` / `get_entity_registry()` no-arg = default grain; query code unchanged |
| E4 | CRM refresh → 15 entities in person grain; empty-crm → 0 |
| E5 | Legacy root `entities.json` readable when grain file absent |
| E6 | Baseball `network.json` declares `player` + `team` grains (no data committed) |
| E7 | `describe_network` reports multi-grain MVR coherently |
| E8 | Docs updated |
| E9 | `./bin/ci-local` green |

---

## Completion (Cursor)

Per `prompts/cursor/WORKFLOW.md`: `./bin/ci-local`, `done/` folder with `output.md`, no commit/push.

**Suggested commit message:**

```
feat(network): multi-MVR entity stores per grain

Declare mvr.grains in network.json; per-grain entities/<grain>.json
stores; load_mvr/get_entity_registry default-grain compat; bootstrap
resets all grains. Query path unchanged (default grain only).
```

---

## For Grok + Paul

- **Next slice:** `LahmanSeedHandler` in `examples/networks/baseball/bootstrap_handlers/` — populate player/team grains + verification.
- **Then:** query orchestrator grain selection (`target_resolve`, supervisor, per-grain registry in step 1).