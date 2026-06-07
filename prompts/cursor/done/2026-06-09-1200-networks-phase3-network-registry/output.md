# Networks Phase 3 — output

## Summary

Added a user-local **network name registry** at `~/.config/mycelium/networks.json` (override: `MYCELIUM_NETWORKS_CONFIG`). Extended `resolve_network_root()` with name-based selection and default-network fallback. CLI gains `mycelium network register|list|use` and `query --network <name>`. MCP resolves via `MYCELIUM_NETWORK` or default from config when `MYCELIUM_NETWORK_ROOT` is unset.

## Resolution order (full)

1. CLI `--network-dir`
2. CLI `--network` (registry name)
3. `MYCELIUM_NETWORK_ROOT`
4. `MYCELIUM_NETWORK` (registry name)
5. Default from config (`default: true`)
6. Legacy `<framework>/data/`

## Files changed

| Area | Change |
|------|--------|
| `src/network/registry.py` | `NetworkEntry`, load/save, `register_network`, `set_default_network`, `list_networks` |
| `src/network/paths.py` | Extended `resolve_network_root()` with name + default |
| `src/main.py` | `network` subcommands; `query --network`; error handling |
| `src/mycelium_mcp/server.py` | Instructions mention `MYCELIUM_NETWORK` + config default |
| `tests/test_network_registry.py` | 9 smoke tests |
| `tests/test_network_paths.py` | Legacy test isolates config via `MYCELIUM_NETWORKS_CONFIG` |
| `README.md`, `.env.example` | Config + CLI examples |

## Config format

```json
{
  "version": "1",
  "networks": [
    { "name": "prm_crm", "root": "/absolute/path", "default": true }
  ]
}
```

Validation: unique names, resolved absolute roots, exactly one `default: true` when any networks are registered. First `register` auto-defaults when it is the only entry.

## Verification

```bash
uv run pytest -m smoke -q   # 73 passed
uv run ruff check src tests  # clean
```

## Manual CLI flow

```bash
uv run mycelium network register prm_crm --root "$(pwd)/data" --default
uv run mycelium network list
uv run mycelium query --network prm_crm --person-key "Nichanan Kesonpat"
uv run mycelium query --person-key "Nichanan Kesonpat"   # uses default
uv run mycelium network use prm_crm
```

## MCP

Set `MYCELIUM_NETWORK=prm_crm` instead of a full path when the name is registered locally on the machine running the server. Explicit `MYCELIUM_NETWORK_ROOT` still wins.

## Out of scope (unchanged)

- Distributed discovery
- Network creation wizard
- CRM example move (Phase 4)

## Next queue item

`prompts/cursor/next/2026-06-07-1300-networks-phase4-crm-example.md`
