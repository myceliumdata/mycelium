# Networks Phase 2 — output

## Summary

Introduced `src/network/paths.py` as the single resolver for `network_root` and derived runtime paths. CLI `query`, MCP `_bootstrap()`, and `bin/reset-mycelium` now wire through `resolve_network_root()` + `apply_network_paths()` before storage/graph initialization.

**Precedence (Phase 2):** CLI `--network-dir` → env `MYCELIUM_NETWORK_ROOT` → legacy `<framework>/data/`.

**Framework root:** env `MYCELIUM_FRAMEWORK_ROOT`, else inferred from package location (`src/network/paths.py` → three parents up to repo root). Not cwd-based, so MCP/CLI work when `cwd` is the framework repo regardless of where the network lives.

## Files changed

| Area | Change |
|------|--------|
| `src/network/paths.py` | `resolve_network_root`, `NetworkPaths`, `apply_network_paths`, `network_display_name` |
| `src/main.py` | `--network-dir` on `query`; configure paths before `reset_storage()` |
| `src/mycelium_mcp/server.py` | `_bootstrap()` resolves/applies paths; `health_check` `info.network_root`; instructions note one network per process |
| `bin/reset-mycelium` | Respects `MYCELIUM_NETWORK_ROOT` / `.env`; prints `network_root`; data paths under active root |
| `tests/test_network_paths.py` | 7 smoke tests |
| `README.md` | `--network-dir` example and resolution paragraph |

## Env vars set by `apply_network_paths`

- `MYCELIUM_NETWORK_ROOT`
- `MYCELIUM_SEED_PATH`
- `MYCELIUM_AGENT_REGISTRY_PATH`
- `MYCELIUM_CATEGORIES_PATH`
- `MYCELIUM_AGENT_DATA_DIR`
- `MYCELIUM_CHECKPOINT_PATH`
- `MYCELIUM_DB_PATH`

## Verification

```bash
uv run pytest -m smoke -q          # 64 passed
uv run ruff check src tests bin/   # clean
```

## Manual checks (two network roots)

### CLI

```bash
# Network A — copy minimal layout from prototype data/
NET_A=$(mktemp -d)
cp -r data/seed.json data/agent_registry.json data/categories.json "$NET_A/"
mkdir -p "$NET_A/agents"

NET_B=$(mktemp -d)
cp data/seed.json "$NET_B/"
echo '{"people":[]}' > "$NET_B/seed.json"   # empty seed → person not found

uv run mycelium query --network-dir "$NET_A" --person-key "Nichanan Kesonpat"
# expect results (prototype seed)

uv run mycelium query --network-dir "$NET_B" --person-key "Nichanan Kesonpat"
# expect empty results (empty seed)
```

### MCP (two configs)

Run two MCP server entries in the client config, same `cwd` (framework repo), different env:

```json
"mycelium-a": { "command": "uv", "args": ["run", "mycelium-mcp"], "cwd": "/path/to/mycelium", "env": { "MYCELIUM_NETWORK_ROOT": "/path/to/net-a" } },
"mycelium-b": { "command": "uv", "args": ["run", "mycelium-mcp"], "cwd": "/path/to/mycelium", "env": { "MYCELIUM_NETWORK_ROOT": "/path/to/net-b" } }
```

Call `health_check` on each — `info.network_root` should match the respective root. `query_person` against each should read that network’s seed/registry only.

## Out of scope (unchanged)

- `~/.config/mycelium/networks.json`, `--network <name>`
- Moving `data/seed.json` or adding `examples/networks/crm/`

## Next queue item

`prompts/cursor/next/2026-06-07-1200-networks-phase3-network-registry.md`
