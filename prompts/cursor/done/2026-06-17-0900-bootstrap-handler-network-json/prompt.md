# Bootstrap handler selection via `network.json` — clean cutover (CRM)

> **READY** — Claim per `prompts/cursor/WORKFLOW.md` (move to `in-progress/` before starting).

**Context:** Paul + Grok agreed June 2026. Bootstrap handler selection must be **explicit in `network.json`**, not inferred from file presence. Framework ships **built-in handlers** (registry keys → classes). Network packs ship **handlers under `network_root`** (e.g. future `LahmanSeedHandler` in `examples/networks/baseball/bootstrap_handlers/`). This is a **repeatable pattern** we will use for specialists next: manifest declares implementation; framework loads built-in or pack module from the active network root.

**Hard requirement:** **No legacy paths.** Remove `specialists/bootstrap_specialist.py` file-presence override and `run_bootstrap(ctx)` function hook entirely. **Clean cutover** — committed examples must declare `bootstrap`; bootstrap run fails clearly when config is missing or invalid.

**Scope:** CRM working end-to-end via `network.json` → `default_seed`. Do **not** implement `LahmanSeedHandler` or multi-MVR in this slice.

---

## Locked decisions (Paul, June 2026)

| # | Decision |
|---|----------|
| H1 | **`network.json` is source of truth** for which bootstrap handler runs. |
| H2 | **Built-in handlers** — registry key → framework class (e.g. `default_seed` → `DefaultSeedHandler`). |
| H3 | **Network-pack handlers** — `module` + `handler` (class name) resolved from **`<network_root>`** on `sys.path` (or equivalent safe `importlib` load). Not imported from `examples/networks/` at runtime. |
| H4 | **`run_network_bootstrap()`** unchanged as orchestrator shell. |
| H5 | **No legacy override** — delete file-presence / `bootstrap_specialist.py` / `_OverrideHandler` / `run_bootstrap` function contract. |
| H6 | **CRM unchanged in behavior** — 15 seed entities on refresh; empty-crm still 0. |
| H7 | **`refresh-example-network`** copies `bootstrap_handlers/` from committed examples when present (prepare for baseball; CRM may omit the directory). |

---

## `network.json` schema (this slice)

### Built-in (CRM)

```json
{
  "bootstrap": {
    "handler": "default_seed"
  }
}
```

Framework registry (initial):

| Key | Class |
|-----|--------|
| `default_seed` | `DefaultSeedHandler` (`network.bootstrap.handlers.default_seed`) |

### Network pack (pattern only — test with stub; baseball ships later)

```json
{
  "bootstrap": {
    "module": "bootstrap_handlers.lahman_seed",
    "handler": "LahmanSeedHandler"
  }
}
```

At runtime after refresh/copy:

```
<network_root>/bootstrap_handlers/lahman_seed.py   # defines class LahmanSeedHandler
```

**Validation rules:**

- `bootstrap` object **required** when `run_network_bootstrap` runs (raise `ValueError` with actionable message if missing).
- If `handler` matches a built-in registry key → use framework class (ignore `module` if present, or reject ambiguity — prefer **reject** if both key and `module` conflict).
- Else **`module` and `handler` (class name) both required** for pack load.
- Loaded class must implement `BootstrapHandler` (`run(self, ctx: BootstrapContext) -> BootstrapResult`); instantiate with no-arg constructor unless you document otherwise.

Add a small parser module (e.g. `src/network/bootstrap/config.py`) and use it from `resolve_handler(paths)`.

---

## Read first

- `prompts/cursor/WORKFLOW.md`
- `src/network/bootstrap/handlers/resolve.py` — **replace** (legacy removal)
- `src/network/bootstrap/run.py`
- `src/network/bootstrap/handlers/default_seed.py`
- `src/network/bootstrap/handlers/protocol.py`
- `src/network/example.py` — `copy_example_network`, `_SKIP_NAMES`
- `src/network/create.py` — `_write_network_manifest`
- `examples/networks/crm/network.json`, `empty-crm/network.json`, `crm-metering/network.json`
- `tests/test_network_bootstrap.py`
- `docs/architecture.md` § Seed bootstrap

---

## Implement

### 1 — Config parse + handler resolution

Refactor `handlers/resolve.py` (or split into `config.py` + `resolve.py`):

```python
def load_bootstrap_config(paths: NetworkPaths) -> BootstrapConfig: ...
def resolve_handler(paths: NetworkPaths) -> BootstrapHandler: ...
```

- Read `paths.root / "network.json"`.
- Parse `bootstrap` block.
- Built-in: `BUILTIN_HANDLERS["default_seed"]()` → `DefaultSeedHandler()`.
- Pack: add `paths.root` to import path (scoped — restore after, or use `importlib.util` from `paths.root / module_path.py`); `getattr(module, class_name)()`; wrap import/instantiate errors as `ValueError` with network path context.

**Delete entirely:**

- `_OverrideHandler`
- `_load_override_module` for `bootstrap_specialist.py`
- Any check for `paths.specialists_dir / "bootstrap_specialist.py"`

### 2 — Committed example manifests

Add `bootstrap` to:

- `examples/networks/crm/network.json` → `"handler": "default_seed"`
- `examples/networks/empty-crm/network.json` → `"handler": "default_seed"`
- `examples/networks/crm-metering/network.json` → `"handler": "default_seed"`
- `examples/networks/baseball/network.json` → `"handler": "default_seed"` for now (placeholder until Lahman handler slice; remove stale `experiment.bootstrap` only if redundant — keep `experiment` metadata if still useful, but bootstrap selection must use top-level `bootstrap` block)

### 3 — `network create`

Update `_write_network_manifest` so created networks include:

```json
"bootstrap": { "handler": "default_seed" }
```

(Alongside existing fields; do not drop `mvr` defaults — if create networks lack `mvr` today and rely on CRM default in `load_mvr()`, leave that unchanged unless create already writes `mvr`.)

### 4 — Example copy

Update `copy_example_network` / `_SKIP_NAMES` so **`bootstrap_handlers/`** is copied from committed examples when the directory exists (not skipped). Do **not** start copying generated runtime `specialists/` from examples.

### 5 — Tests

Rewrite `tests/test_network_bootstrap.py` legacy override tests:

| Test | Assert |
|------|--------|
| CRM manifest + seed | `run_network_bootstrap` → 15 entities, `handler_id == "default_seed"` |
| Missing `bootstrap` in network.json | `ValueError` on `run_network_bootstrap` |
| Unknown built-in key | `ValueError` |
| Pack handler stub | tmp root with `bootstrap_handlers/pack_handler.py` + manifest `module`/`handler` → stub runs, returns known `BootstrapResult` |
| Pack import failure | broken module → `ValueError` with path/module context |
| Guide in context | pack stub class asserts `ctx.guide_text` when `guide.md` present |
| **No** `bootstrap_specialist.py` test | removed — legacy gone |

Update `_prepare_root` in tests to write `bootstrap` into manifest (or copy updated CRM `network.json`).

Ensure Program 2 bootstrap matrix and example capstones still pass.

### 6 — Docs

Update **`docs/architecture.md`** § Seed bootstrap:

- Document `network.json` `bootstrap` schema (built-in vs pack).
- Document **network-pack loading pattern** (explicitly note: same pattern planned for specialists).
- Remove all references to `specialists/bootstrap_specialist.py` override.

Update **`docs/full-code-walkthrough.md`** §6 similarly.

Short note in **`examples/networks/crm/README.md`** — bootstrap handler declared in `network.json`.

**Optional (Grok doc pass later):** `docs/plans/baseball-example-program.md` — mention future `LahmanSeedHandler` in pack; only if trivial one-liner.

---

## Explicit non-goals

- `LahmanSeedHandler` implementation
- Multi-MVR / multi-registry
- Specialist loading pattern implementation (document only)
- Query graph changes
- `bootstrap_experiment.py` disposition
- Editing `TODO.md`

---

## Exit criteria

| # | Criterion |
|---|-----------|
| E1 | CRM/empty-crm/crm-metering `network.json` include `bootstrap.handler: default_seed` |
| E2 | No legacy `bootstrap_specialist.py` resolution code remains |
| E3 | Pack handler load works from `<network_root>/bootstrap_handlers/` (stub test) |
| E4 | Missing/invalid bootstrap config fails clearly |
| E5 | `network create` writes `bootstrap` block |
| E6 | `refresh-example-network` copies `bootstrap_handlers/` when present |
| E7 | Docs updated; architecture describes repeatable pack pattern |
| E8 | `./bin/ci-local` green |

---

## Completion (Cursor)

Per `prompts/cursor/WORKFLOW.md`: `./bin/ci-local`, `done/` folder with `output.md`, no commit/push.

**Suggested commit message:**

```
feat(network): bootstrap handler selection via network.json

Declare bootstrap.handler in network manifests; built-in registry for
default_seed; load network-pack handler classes from network_root.
Remove legacy bootstrap_specialist.py override path.
```

---

## For Grok + Paul

- Next slice: **multi-MVR entity stores**, then **LahmanSeedHandler** in `examples/networks/baseball/bootstrap_handlers/`.
- Specialist manifest loading can mirror this slice’s `module` + class pattern.