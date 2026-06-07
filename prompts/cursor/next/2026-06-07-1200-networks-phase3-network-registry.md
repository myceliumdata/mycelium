# Task: Networks Phase 3 — local network registry + default

**Read these first (mandatory):**
- `prompts/cursor/WORKFLOW.md`
- `docs/plans/networks-terminology.md` (config file section)
- `src/network/paths.py` (or Phase 2 module) — extend resolution
- `src/main.py`

**Depends on:** Phase 2 path resolver landed.

---

## Objective

Add a **user-local config file** mapping network **names** → **`network_root` paths**, with one **default** network. Enables `mycelium query --network prm_crm` and plain `mycelium query` without repeating paths.

**Not in scope:** distributed discovery (long-term TODO).

---

## Config file

**Default path:** `~/.config/mycelium/networks.json`  
**Override:** `MYCELIUM_NETWORKS_CONFIG`

```json
{
  "version": "1",
  "networks": [
    { "name": "prm_crm", "root": "/absolute/path", "default": true }
  ]
}
```

### Module (e.g. `src/network/registry.py`)

- `load_network_registry() -> list[NetworkEntry]`
- `resolve_network_root` extended precedence (per plan):
  1. CLI `--network-dir`
  2. CLI `--network` (name lookup)
  3. `MYCELIUM_NETWORK_ROOT`
  4. `MYCELIUM_NETWORK` (name)
  5. Default from config
  6. Legacy `data/` shim
- `register_network(name, root, *, default=False)`
- `set_default_network(name)`
- `list_networks()`

Validate: absolute paths, unique names, exactly one default when any registered.

---

## CLI subcommands

Add `mycelium network` group:

| Command | Behavior |
|---------|----------|
| `network register <name> --root <path> [--default]` | Add/update entry |
| `network list` | Print name, root, default flag |
| `network use <name>` | Set default |

Wire `--network <name>` on `query` (and MCP env `MYCELIUM_NETWORK` if not already).

---

## Tests (smoke)

- Registry read/write in `tmp_path` via `MYCELIUM_NETWORKS_CONFIG`.
- Name resolution beats legacy shim when registered.
- Default used when no flags.

---

## Scope boundaries

**May modify:** `src/network/`, `src/main.py`, tests, README config section, `.env.example` one-line mention.

**Out of scope:** Distributed discovery, network creation prompt, CRM example move.

---

## Verification

```bash
uv run pytest -m smoke -q
uv run ruff check src tests
```

---

## Deliverables

`prompts/cursor/done/2026-06-07-1200-networks-phase3-network-registry/`