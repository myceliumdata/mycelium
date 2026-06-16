# Network manifest required — fail fast (remove MVR/entity legacy shims)

> **READY** — Claim per `prompts/cursor/WORKFLOW.md` (move to `in-progress/` before starting).

**Context:** Paul + Grok agreed June 2026. Slice `2026-06-17-1400-multi-mvr-entity-stores` shipped per-grain entity stores and `mvr.grains`, but kept **silent CRM defaults** (`_crm_default_config()` when manifest/MVR missing) and **legacy shims** (flat `mvr.bind_fields`, root `entities.json` read fallback). Paul wants a **clean cutover**: explicit manifest required, **fail fast**, no backward compatibility. **CRM remains the regression anchor** — all committed examples already declare full `mvr.grains`; tests must use those manifests and compare outcomes against current CRM behavior (15 seed entities, query smoke, capstones).

**Parent slice:** `prompts/cursor/done/2026-06-17-1400-multi-mvr-entity-stores/` (if present) or working tree from multi-MVR delivery.

---

## Locked decisions (Paul, June 2026)

| # | Decision |
|---|----------|
| F1 | **`network.json` required** for MVR and metering policy load — no silent defaults when file or section missing. |
| F2 | **`mvr.grains` required** — reject flat `mvr.bind_fields` at network root (no implicit `person` grain). |
| F3 | **`mvr.default_grain` always required** — even when only one grain is declared (no single-grain inference). |
| F4 | **Delete `_crm_default_config()` / `_crm_default_mvr()`** and all code paths that return them. |
| F5 | **Single entity store path** — `entity_store_path()` only; remove `resolve_entity_store_path()` legacy root `entities.json` read fallback. Registry read path = write path (except `MYCELIUM_ENTITIES_PATH` override for default grain). |
| F6 | **`metering` block required** in `network.json` when loading metering policy — delete `_crm_default_metering()` silent fallback (committed examples already declare `metering`). |
| F7 | **`network create`** writes complete manifest: `bootstrap`, `mvr` (with `default_grain` + `grains.person` for CRM-shaped creates), and `metering` (disabled CRM default object matching `examples/networks/crm/network.json`). |
| F8 | **CRM outcomes unchanged** — same 15 entities, same query behavior; only config strictness and path canonicalization change. |

---

## Required `network.json` shape (only valid forms)

### CRM examples (unchanged values; already committed)

```json
{
  "bootstrap": {
    "module": "network.bootstrap.handlers.default_seed",
    "handler": "DefaultSeedHandler"
  },
  "mvr": {
    "default_grain": "person",
    "grains": {
      "person": {
        "bind_fields": ["name", "employer"],
        "description": "CRM people: display name plus current employer before bind and research."
      }
    }
  },
  "metering": { "enabled": false, ... }
}
```

### Baseball (unchanged)

Two grains + `default_grain: "player"` — already in `examples/networks/baseball/network.json`.

### Invalid (must raise `ValueError` with actionable message)

| Case | Example |
|------|---------|
| No `network.json` | tmp root with only `categories.json` |
| No `mvr` key | `{}` manifest |
| No `mvr.grains` | `"mvr": { "default_grain": "person" }` |
| Flat `bind_fields` only | `"mvr": { "bind_fields": ["name", "employer"] }` |
| Missing `default_grain` | one or two grains without `default_grain` |
| Empty `grains` | `"grains": {}` |
| Grain missing `bind_fields` | `"person": { "description": "..." }` |
| No `metering` | manifest without `metering` key |

---

## Read first

- `prompts/cursor/WORKFLOW.md`
- `src/network/mvr.py` — `_crm_default_config`, flat `bind_fields` branch, `_resolve_default_grain` single-grain inference
- `src/network/paths.py` — `resolve_entity_store_path`, `_default_entity_store_path` try/except fallback
- `src/network/metering_policy.py` — `_crm_default_metering`
- `src/network/create.py` — `_write_network_manifest`, `_unlink_entity_stores`
- `src/agents/entity_registry.py` — `_resolve_registry_paths` read/write split
- `tests/test_multi_mvr_entity_stores.py` — legacy tests to **delete/replace**
- `tests/test_example_network.py`, `tests/test_network_bootstrap.py`, other tests setting `MYCELIUM_ENTITIES_PATH` to root `entities.json` without manifest
- `docs/architecture.md`, `docs/onboarding.md`, `docs/database-notes.md`, `README.md` — legacy fallback wording

---

## Implement

### 1 — Strict MVR loader (`src/network/mvr.py`)

Refactor `load_mvr_config()`:

- Require `network.json` exists and parses to object.
- Require `mvr` object with non-empty `grains`.
- Require `mvr.default_grain` **always** (remove `_resolve_default_grain` branch that picks the sole grain when `default_grain` omitted).
- Parse only `mvr.grains.<name>` entries; **reject** top-level `mvr.bind_fields` with message directing authors to `mvr.grains`.
- **Delete:** `_crm_default_config()`, `_crm_default_mvr()`, and every `return _crm_default_config()` path.
- Keep `_DEFAULT_DESCRIPTION` only as default for a grain entry when `description` is omitted inside `grains.<name>` (optional polish — or require `description`; committed examples always have it).

Raise `ValueError` including manifest path, e.g. `{path}: missing required mvr.grains`.

### 2 — Strict metering loader (`src/network/metering_policy.py`)

- Require `network.json` and `metering` object — same fail-fast style.
- **Delete `_crm_default_metering()`** silent fallback (keep parsing helpers for valid `metering` blocks).

### 3 — Paths (`src/network/paths.py`)

- **Delete `resolve_entity_store_path()`** (or make it a deprecated alias to `entity_store_path` and remove all callers — prefer delete).
- **`_default_entity_store_path`:** call `load_mvr_config` / `entity_store_path` — no broad `except Exception` fallback to `entities/person.json`.
- **`_unlink_entity_stores`:** stop unlinking root `entities.json` (legacy artifact); unlink only declared grain store paths from manifest.

### 4 — Entity registry (`src/agents/entity_registry.py`)

- `_resolve_registry_paths`: single path from `entity_store_path` for read and write (default grain + `MYCELIUM_ENTITIES_PATH` override unchanged).
- Update module docstring: per-grain stores at `entities/<grain>.json`, not root `entities.json`.

### 5 — `network create` manifest (`src/network/create.py`)

Extend `_write_network_manifest` to include CRM-shaped defaults:

```json
"mvr": {
  "default_grain": "person",
  "grains": {
    "person": {
      "bind_fields": ["name", "employer"],
      "description": "CRM people: display name plus current employer before bind and research."
    }
  }
},
"metering": {
  "enabled": false,
  "default_funding_model": "marginal",
  "meter_first_delivery": true,
  "quote_provider": "builtin",
  "principal": { "marginal_optional": true, "required_for_funding_models": ["sponsor_public", "pool"] },
  "payment": { "enabled": false, "provider": "mock", "require_paid_before_accept": true }
}
```

(Trim to match what `load_metering_policy` actually requires; mirror `examples/networks/crm/network.json` metering block.)

### 6 — Tests

**Remove / replace:**

| Test | Action |
|------|--------|
| `test_legacy_flat_mvr_parses_implicit_person_grain` | **Delete**; replace with `test_flat_bind_fields_rejected` |
| `test_legacy_entities_json_read_fallback` | **Delete**; replace with `test_entity_store_uses_grain_path_only` |
| `test_baseball_manifest_requires_default_grain_for_two_grains` | Keep; add `test_single_grain_requires_default_grain` |

**Add fail-fast matrix** in `tests/test_multi_mvr_entity_stores.py` or `tests/test_network_manifest_required.py`:

- missing `network.json`
- missing `mvr` / `grains` / `default_grain` / `metering`
- flat `bind_fields` rejected

**Fix tests** that point at root `entities.json` without manifest:

- Copy `examples/networks/crm/network.json` into tmp roots (or use `_prepare_root` helper).
- Use `entities/person.json` (or `NetworkPaths.from_root(...).entities_path`) for `MYCELIUM_ENTITIES_PATH` when env override is needed.

**Regression (must stay green):**

- `test_refresh_crm_imports_seed_into_entities` → 15 entities at `entities/person.json`
- `test_run_network_bootstrap_crm_seed` → 15 entities
- Program 2/3 smoke, MVR, example capstones

### 7 — Docs + stray references

Update prose to **remove** legacy fallback language:

- `docs/architecture.md` — no flat `bind_fields`, no root `entities.json` fallback
- `docs/onboarding.md` — grain path only
- `docs/database-notes.md`, `README.md` — canonical path `entities/<default_grain>.json`
- `src/main.py` help text for `--seed` (if still says `entities.json`)
- `src/network/example.py` — `_SKIP_NAMES` may still skip `entities.json` and `entities/` for copy (runtime artifacts); document that root `entities.json` is **not** used

Sweep `grep -r "legacy read fallback\|flat.*bind_fields\|_crm_default"` in `src/` `tests/` `docs/` — zero hits except archival/historical docs (do not rewrite `legacy-ingest-and-storage-reference.md` unless one line references new shim).

**Do not edit `TODO.md`.**

---

## Explicit non-goals

- `LahmanSeedHandler` / baseball data ingest
- Query graph grain selection
- Requiring `bootstrap` in MVR loader (bootstrap config already fails separately — no change needed unless you unify validators)
- Auto-migrating live `~/mycelium-networks/` roots (Paul refreshes manually)

---

## Exit criteria

| # | Criterion |
|---|-----------|
| E1 | `_crm_default_config`, `_crm_default_mvr`, `_crm_default_metering` deleted |
| E2 | Flat `mvr.bind_fields` and missing manifest sections → `ValueError` |
| E3 | `default_grain` required for single- and multi-grain manifests |
| E4 | No `resolve_entity_store_path` legacy fallback; reads use grain path only |
| E5 | `network create` writes `mvr` + `metering` blocks |
| E6 | CRM refresh/bootstrap capstones unchanged (15 entities, `entities/person.json`) |
| E7 | Docs/README/onboarding updated — one canonical layout |
| E8 | `./bin/ci-local` green |

---

## Completion (Cursor)

Per `prompts/cursor/WORKFLOW.md`: `./bin/ci-local`, `done/` folder with `output.md`, no commit/push.

**Suggested commit message:**

```
refactor(network): require explicit network.json mvr and metering

Remove CRM silent defaults and legacy flat bind_fields / root
entities.json shims. Fail fast on missing manifest sections;
network create writes full mvr.grains and metering blocks.
```

---

## For Grok + Paul

- After approval: next slice remains **`LahmanSeedHandler`** (baseball pack bootstrap).
- Paul should `./bin/refresh-example-network crm --yes` on live roots once before relying on strict loaders (one-time migration).
- **Deferred (1400 review N1, not this slice):** `write_bind_fields` must use passed registry's MVR (`reg._mvr`), not `load_mvr()` — track in `TODO.md` under baseball queue; implement in grain query orchestrator slice.