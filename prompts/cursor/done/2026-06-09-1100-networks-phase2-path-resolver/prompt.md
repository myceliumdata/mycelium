# Task: Networks Phase 2 — network path resolver + CLI/MCP wiring

**Read these first (mandatory):**
- `prompts/cursor/WORKFLOW.md`
- `docs/plans/networks-terminology.md` (selection model, standard layout)
- `src/main.py`, `src/mycelium_mcp/server.py`, `src/storage/core.py`
- `src/agents/seed.py`, `src/agents/registry.py`, `bin/reset-mycelium`
- Phase 1 done folder (if present) for doc wording

**Depends on:** Phase 1 docs (or plan doc if Phase 1 not merged yet). **Not** Phase 3 registry.

---

## Objective

Introduce **`network_root`** as the runtime source of truth for all network data paths. Wire CLI and MCP to select a network by **explicit path**. Preserve **legacy shim**: when unset, behave exactly like today (`<framework>/data/`).

---

## Standard layout under `network_root`

```
<network_root>/
  network.json       # optional in Phase 2; read display name if present
  seed.json
  categories.json    # runtime
  agent_registry.json
  agents/<category>/
  checkpoints.sqlite
  mycelium.db        # optional
```

---

## Implementation

### New module (e.g. `src/network/paths.py`)

- `resolve_network_root(*, cli_network_dir: str | None = None) -> Path`
  - Precedence Phase 2 only: CLI `--network-dir` → env `MYCELIUM_NETWORK_ROOT` → legacy `<framework>/data`
  - `MYCELIUM_FRAMEWORK_ROOT` or infer framework root from package location / cwd (document choice in `output.md`)
- `NetworkPaths` dataclass or helpers deriving:
  - `seed_path`, `registry_path`, `agents_dir`, `checkpoint_path`, `db_path`, `categories_path`
- `apply_network_paths(paths: NetworkPaths)` — set env vars or call existing singletons' path hooks used by seed/registry/storage (match how tests already monkeypatch `MYCELIUM_*_PATH`)

### CLI (`src/main.py`)

- Add `--network-dir` to `query` (and global if cleaner).
- Resolve paths before `reset_storage()` / `get_storage()` / `run_query`.
- **Do not** implement `--network <name>` registry lookup (Phase 3).

### MCP (`src/mycelium_mcp/server.py`)

- `_bootstrap()` uses `resolve_network_root()` from env `MYCELIUM_NETWORK_ROOT`.
- `health_check` `info` includes resolved `network_root` (string).
- FastMCP instructions: server bound to one network root via env.

### `bin/reset-mycelium`

- Respect active network root when resetting specialists (or document that reset targets legacy `data/` until Phase 4 — minimal change acceptable).

### Legacy shim

- Zero config → identical behavior to `prototype` tag (flat `data/` under repo).

---

## Tests (smoke)

New `tests/test_network_paths.py`:

- `tmp_path` as `network_root` with minimal `seed.json` → resolve + derive paths.
- Legacy fallback when no dir/env (monkeypatch framework root).
- CLI `--network-dir` overrides env (mock or subprocess-light).

Run: `uv run pytest -m smoke -q tests/test_network_paths.py`

---

## Scope boundaries (strict)

**May modify:** new `src/network/` (or `src/storage/network_paths.py`), `src/main.py`, `src/mycelium_mcp/server.py`, `bin/reset-mycelium` (minimal), `tests/test_network_paths.py`, README one paragraph on `--network-dir` if Phase 1 missed it.

**Out of scope:** `~/.config/mycelium/networks.json`, `--network <name>`, moving `data/seed.json`, `examples/networks/crm/`, graph topology changes.

---

## Verification

```bash
uv run pytest -m smoke -q
uv run ruff check src tests bin/
```

Manual (`output.md`): two temp network roots, CLI query each with `--network-dir`; MCP with different `MYCELIUM_NETWORK_ROOT` in two configs (describe steps).

---

## Deliverables

`prompts/cursor/done/2026-06-07-1100-networks-phase2-path-resolver/` with `prompt.md`, `output.md`.