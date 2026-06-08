# Task: Demo slice 1 — `bin/refresh-example-network`

**Read these first (mandatory):**
- `prompts/cursor/WORKFLOW.md`
- `TODO.md` → Demo (phase) → Slice 1
- `bin/copy-example-network` (logic to absorb)
- `src/network/registry.py`, `src/network/paths.py`
- `README.md`, `examples/networks/crm/README.md`, `data/README.md`

**Depends on:** Networks Phase 5 complete (`1500`–`1800` in `prompts/cursor/done/`).

**Blocks:** Demo slice 2 (`2026-06-08-1100-demo-slice2-network-status.md`).

---

## Objective

Replace **`bin/copy-example-network`** with **`bin/refresh-example-network`**: bootstrap or **reset** a live example network from committed sources under `examples/networks/<name>/`. Primary demo path:

```bash
./bin/refresh-example-network crm
```

Paul uses this before demos to wipe stale specialist research and restore a clean CRM seed.

---

## Behavior

### Arguments

```
./bin/refresh-example-network <name> [--root PATH] [--register] [--default] [--yes] [--dry-run]
```

| Arg | Meaning |
|-----|---------|
| `<name>` | Subfolder of `examples/networks/` (e.g. `crm`). Must exist. |
| `--root` | Live `network_root` (default: `~/mycelium-networks/<name>`). Must be absolute after expand. |
| `--register` | Register `<name>` in `networks.json` (default **on** for refresh script). |
| `--default` | Mark registered network as default. **Auto-on when `<name>` is `crm`** unless `--no-default` (add flag if cleaner than magic). |
| `--yes` | Skip interactive confirmation when live root already exists (required for tests/CI). |
| `--dry-run` | Print planned actions (wipe path, copy list, register) without writes. |

### Flow

1. **Validate** `<name>` — `examples/networks/<name>/` must exist.
2. **Resolve** live `--root` (default `~/mycelium-networks/<name>`).
3. **If live root exists** (directory present **or** registered with that path):
   - Without `--yes`: prompt stdin — e.g. `Replace network at <path>? [y/N]` — exit 0 on decline.
   - With `--yes` or user confirms: **wipe entire live root** (`shutil.rmtree` if exists, then recreate). This removes runtime artifacts: `specialists/`, `agents/`, `categories.json`, `agent_registry.json`, checkpoints, DB, etc.
4. **Copy** committed example files into live root — same rules as today’s `copy-example-network`:
   - Copy: `seed.json`, `network.json`, etc.
   - **Skip:** `README.md`, `prepare_seed.py`, runtime artifacts (`categories.json`, `agent_registry.json`, `agents/`, `*.db`, `*.sqlite`, wal/shm).
5. **Register** — `register_network(name, root, default=...)` when `--register` (default on). Registry name defaults to `network.json` `name` field or `<name>`.
6. **Print** summary: source → destination, files copied, registry status.

### Implementation notes

- Extract shared copy logic into **`src/network/example.py`** (e.g. `copy_example_network(name, target: Path) -> list[str]`) so refresh and tests call one code path.
- `bin/refresh-example-network` — thin script (venv bootstrap pattern from `copy-example-network`).
- **Delete** `bin/copy-example-network` after migration.
- Do **not** touch framework-committed `src/agents/specialists/*_specialist.py` CRM reference modules.

---

## Retire legacy `data/` shim

Product bootstrap is `refresh-example-network crm` → user `network_root`, not `<framework>/data/`.

1. **Remove** `data/README.md` and the `data/` directory from the repo (if empty after README removal).
2. **`resolve_network_root()`** — when no CLI/env/registry default is set, **raise `ValueError`** with a clear message, e.g. *"No network configured. Run: ./bin/refresh-example-network crm"* — do **not** fall back to `<framework>/data`.
3. Keep **`legacy_network_root()`** only if tests need it temporarily; prefer updating tests to expect the new error or to use explicit `--network-dir` / registry fixtures.
4. Update **`.gitignore`** — remove `data/*` runtime entries if `data/` is gone; keep ignores under `examples/networks/**` as today.
5. Grep and fix doc references to `copy-example-network`, bootstrap via `./data`, and legacy `data/` fallback in **README**, `examples/networks/crm/README`, `docs/architecture.md` (minimal), `docs/full-code-walkthrough.md` (one line if needed).

---

## Docs / runbook

**README** quick start must use:

```bash
./bin/refresh-example-network crm
```

Include short **demo runbook** blurb: run before demos; restart Claude MCP after refresh; use fresh `thread_id` per query attribute.

---

## Tests

| Test | Notes |
|------|-------|
| Refresh into empty `tmp_path` root | `--yes`; seed.json exists; no prompt |
| Refresh replaces existing root | pre-seed runtime junk; `--yes`; only committed example files remain + clean tree |
| Decline without `--yes` | mock stdin `n` → exit 0, root unchanged |
| `crm` registers as default | isolated `MYCELIUM_NETWORKS_CONFIG` |
| Integration: refresh → query Nichanan | replace `test_copy_example_register_and_query_nichanan` to call refresh script |
| `test_legacy_shim_without_committed_data_seed` | update for no silent `data/` fallback — expect error or explicit shim removal |
| `tests/test_example_network.py`, `tests/test_categories_sample.py` | update script paths |

Use `tests/network_helpers.py` patterns; `--yes` for subprocess calls.

---

## Verification

```bash
uv run pytest -m smoke -q
uv run ruff check src tests bin/
test ! -f bin/copy-example-network
./bin/refresh-example-network crm --dry-run
```

---

## Scope boundaries

**May modify:** `bin/`, `src/network/`, `src/main.py` (only if error messages reference bootstrap), `tests/`, README, `examples/networks/crm/README.md`, minimal architecture doc lines, `.gitignore`

**Out of scope:** `mycelium network status` (slice 2), admin daemon/UI, `network unregister` CLI

---

## Deliverables

`prompts/cursor/done/2026-06-08-1000-demo-slice1-refresh-example-network/` with `prompt.md`, `output.md` (checklist + manual demo steps).