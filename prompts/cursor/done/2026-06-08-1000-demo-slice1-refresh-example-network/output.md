# Output: Demo slice 1 — `bin/refresh-example-network`

## Summary

Replaced `bin/copy-example-network` with `bin/refresh-example-network` — bootstrap or wipe-and-recopy a live network from `examples/networks/<name>/`. Retired the legacy `data/` shim; unconfigured installs fail loud with a pointer to refresh.

## Files changed

| File | Change |
|------|--------|
| `src/network/example.py` | New — `copy_example_network()`, `refresh_example_network()` |
| `bin/refresh-example-network` | New thin CLI |
| `bin/copy-example-network` | **Deleted** |
| `src/network/paths.py` | No `data/` fallback; `NO_NETWORK_CONFIGURED_MSG` |
| `data/README.md` + `data/` dir | **Removed** |
| `.gitignore` | Removed `data/*` runtime entries |
| `src/main.py` | Seed help text (no legacy data mention) |
| `README.md` | Quick start, demo runbook, layout |
| `examples/networks/crm/README.md` | Refresh-first instructions |
| `docs/architecture.md` | Minimal bootstrap / selection updates |
| `docs/full-code-walkthrough.md` | One-line networks note |
| `docs/examples/README.md` | Script name |
| `TODO.md` | Slice 1 marked done |
| `tests/test_example_network.py` | Refresh tests (empty, replace, decline, default, dry-run) |
| `tests/test_categories_sample.py` | Script path |
| `tests/test_network_integration.py` | Error + refresh integration |
| `tests/test_network_paths.py` | Unconfigured raises (was legacy fallback) |

## Verification

```text
uv run pytest -m smoke -q  → 110 passed
uv run ruff check src tests bin/  → clean
test ! -f bin/copy-example-network  → OK
./bin/refresh-example-network crm --dry-run  → OK (no --yes required when live root exists; fixed in 1050)
```

## Manual demo steps (Paul)

1. `./bin/refresh-example-network crm --yes` — wipes `~/mycelium-networks/crm`, recopies seed, registers default.
2. Restart Claude MCP (`mycelium-crm` entry).
3. `uv run mycelium query --person-key "Nichanan Kesonpat" --attributes email --thread-id demo-$(date +%s)`.
4. Re-run refresh before next demo to drop cached research.

## Unblocks

`prompts/cursor/next/2026-06-08-1100-demo-slice2-network-status.md`
