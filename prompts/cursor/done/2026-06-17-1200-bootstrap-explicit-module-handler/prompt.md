# Bootstrap handler — explicit `module` + `handler` only (remove registry keys)

> **READY** — Claim per `prompts/cursor/WORKFLOW.md` (move to `in-progress/` before starting).

**Context:** Paul + Grok agreed June 2026. Slice `2026-06-17-0900` introduced `network.json` bootstrap selection, but CRM uses magic registry key `"handler": "default_seed"` while network packs use `"module"` + class `"handler"`. Paul wants **one shape everywhere** — same pattern we will repeat for specialists. **Hard cutover:** remove built-in registry keys; all networks declare **module + handler class name**.

**CRM** uses a **framework module path** (import from installed package). **Baseball / packs** use a **network-root module path** (import from `<network_root>` on `sys.path`). Same JSON schema; two load roots.

---

## Locked decisions (Paul, June 2026)

| # | Decision |
|---|----------|
| N1 | **Single schema:** `bootstrap.module` + `bootstrap.handler` (class name) — **both required**. |
| N2 | **No registry keys** — delete `default_seed`, `BUILTIN_HANDLER_KEYS`, `BUILTIN_HANDLERS`, `builtin_key` on `BootstrapConfig`. |
| N3 | **Framework modules** — `module` starts with `network.` → `importlib.import_module` from installed framework (no `network_root` on path). |
| N4 | **Pack modules** — all other `module` values → load from `<network_root>` (existing pack logic). |
| N5 | **CRM behavior unchanged** — 15 seed entities on refresh; empty-crm 0. |
| N6 | **No legacy** — reject manifests with handler-only / registry-key form; clear `ValueError`. |

---

## `network.json` schema (only valid shape)

### CRM (framework handler)

```json
"bootstrap": {
  "module": "network.bootstrap.handlers.default_seed",
  "handler": "DefaultSeedHandler"
}
```

### Network pack (unchanged resolution, same keys)

```json
"bootstrap": {
  "module": "bootstrap_handlers.lahman_seed",
  "handler": "LahmanSeedHandler"
}
```

**Validation (`load_bootstrap_config`):**

- `bootstrap` object required.
- `module` and `handler` both required non-empty strings.
- Reject handler-only manifests (e.g. `"handler": "default_seed"` without `module`).

---

## Read first

- `src/network/bootstrap/config.py`
- `src/network/bootstrap/handlers/resolve.py`
- `examples/networks/crm/network.json`, `empty-crm`, `crm-metering`, `baseball`
- `src/network/create.py` — `_write_network_manifest`
- `tests/test_network_bootstrap.py`
- `docs/architecture.md` § Seed bootstrap

---

## Implement

### 1 — `BootstrapConfig` + parser

- `BootstrapConfig` fields: `module: str`, `class_name: str` only.
- Remove `builtin_key`, `BUILTIN_HANDLER_KEYS`, and error messages referencing built-in keys.
- Update example strings in errors to show CRM framework form.

### 2 — `resolve_handler`

- Remove `BUILTIN_HANDLERS` and `DefaultSeedHandler` direct import for dispatch (class still lives in `default_seed.py`).
- Single load path:
  - If `config.module.startswith("network.")` → `_load_framework_handler(config)`
  - Else → `_load_pack_handler(paths, config)` (existing network_root logic; rename for clarity)
- Share class instantiation + `run` protocol check between both loaders (small helper to avoid duplication).

### 3 — Update all committed manifests

Replace `"handler": "default_seed"` with explicit module + class in:

- `examples/networks/crm/network.json`
- `examples/networks/empty-crm/network.json`
- `examples/networks/crm-metering/network.json`
- `examples/networks/baseball/network.json`

### 4 — `network create`

`_write_network_manifest` bootstrap block:

```json
"bootstrap": {
  "module": "network.bootstrap.handlers.default_seed",
  "handler": "DefaultSeedHandler"
}
```

### 5 — Tests

Update `tests/test_network_bootstrap.py`:

| Change | Detail |
|--------|--------|
| CRM tests | Manifests use framework module + `DefaultSeedHandler` |
| Remove | `test_run_network_bootstrap_unknown_builtin_handler` |
| Add/replace | Missing `module` or missing `handler` → `ValueError` |
| Add | Reject legacy `"handler": "default_seed"` without module |
| Pack tests | Unchanged behavior (`bootstrap_handlers.*`) |
| Framework load | Optional explicit test that CRM manifest does not require files under `network_root` for handler module |

Update `tests/test_network_create.py`, `tests/test_example_network.py` fleet fixture bootstrap blocks.

### 6 — Docs

- `docs/architecture.md` — single schema; framework vs pack load roots; **no registry keys**; note this mirrors planned specialist manifest pattern.
- `docs/full-code-walkthrough.md` §6
- `examples/networks/crm/README.md` — show explicit bootstrap block

---

## Explicit non-goals

- `LahmanSeedHandler` implementation
- Multi-MVR
- Specialist loading implementation
- Editing `TODO.md`

---

## Exit criteria

| # | Criterion |
|---|-----------|
| E1 | No `default_seed` / `BUILTIN_*` registry code remains |
| E2 | All committed examples use `module` + `handler` |
| E3 | CRM refresh/create behavior unchanged |
| E4 | Pack handler tests still pass |
| E5 | Legacy handler-only manifest rejected |
| E6 | Docs updated |
| E7 | `./bin/ci-local` green |

---

## Completion (Cursor)

Per `prompts/cursor/WORKFLOW.md`: `./bin/ci-local`, `done/` + `output.md`, no commit.

**Suggested commit message:**

```
refactor(network): bootstrap manifest uses module and handler class only

Remove default_seed registry keys; CRM declares DefaultSeedHandler via
framework module path; pack handlers unchanged under network_root.
```

---

## For Grok + Paul

- After approval: next slice remains **multi-MVR entity stores**, then **LahmanSeedHandler** pack module in baseball example.