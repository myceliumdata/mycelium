# Output: Demo slice 1 — review fixes (1050)

## Review issue → fix

| Issue | Fix |
|-------|-----|
| 1 — dry-run prompts before dry_run branch | Moved `dry_run` early-return above confirmation in `src/network/example.py` |
| 2 — dry-run test without `--yes` | Added `test_refresh_dry_run_without_yes_leaves_root_unchanged` with sentinel `input_fn` |
| 3 — MCP instructions legacy `data/` | Updated `_build_mcp_instructions` to point at registry default + `refresh-example-network crm` |
| 4 — MCP health `legacy_network_root()` fallback | `_network_health_info()` returns `network_root: None` + `network_configure_hint`; test renamed |
| 5 — `--no-default` on empty registry | `register_network(..., allow_no_default=True)`; validation allows 0 or 1 default; wired from refresh |
| 6 — TODO `copy-example-network` | Updated to `refresh-example-network` |
| 7 — slice 1 output.md dry-run note | Updated verification line |
| 8 — networks-terminology stale bootstrap | One-line `refresh-example-network` update |
| 9 — `.gitignore` `data/` | Added top-level `data/` ignore |

`review.md` in slice 1 done folder: all issues marked **fixed** (1050).

## Files changed

- `src/network/example.py`
- `src/network/registry.py`
- `src/mycelium_mcp/server.py`
- `tests/test_example_network.py`
- `tests/test_network_polish.py`
- `.gitignore`
- `TODO.md`
- `docs/plans/networks-terminology.md` (one line)
- `prompts/cursor/done/2026-06-08-1000-.../output.md`
- `prompts/cursor/done/2026-06-08-1000-.../review.md`

## Verification

```text
uv run pytest -m smoke -q  → 112 passed
uv run ruff check src tests bin/  → clean
./bin/refresh-example-network crm --dry-run  → exit 0 (no --yes, live root exists)
```

## Unblocks

`prompts/cursor/next/2026-06-08-1100-demo-slice2-network-status.md`
