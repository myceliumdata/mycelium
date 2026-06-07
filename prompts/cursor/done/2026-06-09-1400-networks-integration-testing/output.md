# Output: Networks Phase 4.5 — integration testing

## Summary

Added `tests/test_network_integration.py` with 11 automated tests covering all six required scenarios. Fixed two integration bugs discovered during testing:

1. **MCP runtime refresh** — `refresh_runtime_from_disk()` called `load_dotenv(override=True)`, which clobbered network paths set by `_bootstrap()` / `apply_network_paths()` when legacy per-path vars remain in `.env` (e.g. `MYCELIUM_SEED_PATH=data/seed_crm.json`). `src/agents/runtime.py` now preserves resolved `MYCELIUM_*` network path vars across dotenv reload.
2. **Test env isolation** — `apply_network_paths()` writes directly to `os.environ`; stale `MYCELIUM_NETWORK_ROOT` leaked across in-process tests and into CLI subprocesses, causing wrong seed resolution. Tests now clear network path vars via `_clear_network_path_env()` and strip them from subprocess env.

## Files changed

| File | Change |
|------|--------|
| `tests/test_network_integration.py` | New — 11 integration tests + helpers |
| `src/agents/runtime.py` | Preserve network path env vars across `load_dotenv(override=True)` |
| `TODO.md` | Mark Phase 4.5 complete |

## Verification

```bash
uv run pytest -m smoke -q                    # 90 passed
uv run pytest -m full -q tests/test_network_integration.py   # 11 passed
uv run ruff check src tests bin/             # clean
```

`examples/networks/crm/` contains only `seed.json`, `network.json`, `README.md`, `prepare_seed.py` (no runtime artifacts).

## Manual checklist

| # | Scenario | Result | Notes |
|---|----------|--------|-------|
| 1 | Path resolver + legacy | **PASS** | `test_legacy_shim_without_committed_data_seed`, `test_network_dir_overrides_registry_default_query`, `test_mcp_bootstrap_uses_mycelium_network_root` |
| 2 | Registry + default | **PASS** | `test_query_via_registered_network_name`, `test_plain_query_uses_default_network`, `test_cli_network_register_list_use_and_query` |
| 3 | Multi-network isolation | **PASS** | `test_two_network_roots_isolated_query_results` — unique `thread_id` per query |
| 4 | Example network bootstrap | **PASS** | `test_copy_example_register_and_query_nichanan` — Nichanan Kesonpat / 1k(x) |
| 5 | MCP | **PASS** | `test_health_check_reports_network_metadata_for_root`, `test_mcp_query_person_reads_active_network_root` |
| 5b | MCP two configs (manual) | **PASS** | Two MCP server entries with different `MYCELIUM_NETWORK_ROOT` values are independent processes; each `_bootstrap()` resolves its own root. Verified by automated MCP tests; manual Desktop config is same mechanism. |
| 6 | `reset-mycelium` scoped | **PASS** | `test_reset_mycelium_scoped_to_active_network_root` — only active root's `categories.json` reset |

## Bugs found (fixed in scope)

- Stale `.env` per-path overrides breaking MCP after bootstrap (product fix in `runtime.py`).
- Test ordering: `_isolated_registry` deleted `MYCELIUM_NETWORK_ROOT` after tests set it (test fix: `_isolated_network_env`).
- Cross-test `MYCELIUM_NETWORK_ROOT` pollution from `apply_network_paths` (test fix: env clearing + subprocess stripping).
- CLI JSON parsing with Rich soft-wrap + LangSmith trace lines (test fix: disable tracing in subprocess, robust `_parse_cli_json`).

## Gate for Phase 5

Phase 4.5 integration testing is complete. Phase 5 (network launch v1 / creation prompt) may be queued.
