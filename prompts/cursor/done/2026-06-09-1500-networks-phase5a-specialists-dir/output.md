# Output: Networks Phase 5a — per-network `specialists/` + env wiring

## Summary

Wired per-network specialist Python modules under `<network_root>/specialists/` via `MYCELIUM_SPECIALISTS_DIR`. `apply_network_paths()` now sets the full network layout including specialists. `AgentFactory.create_specialist()` derives registry `storage_path` / `strategy_path` from `MYCELIUM_AGENT_DATA_DIR` (with `SpecialistStorage` slug logic) and uses network-relative paths when `agents/` lives under `MYCELIUM_NETWORK_ROOT`.

## Files changed

| File | Change |
|------|--------|
| `src/network/paths.py` | `specialists_dir` on `NetworkPaths`; `MYCELIUM_SPECIALISTS_DIR` in `apply_network_paths()` |
| `src/agents/runtime.py` | Preserve `MYCELIUM_SPECIALISTS_DIR` across dotenv reload |
| `src/agents/factory/agent_factory.py` | `_registry_storage_paths()` — no hardcoded `data/agents/` |
| `tests/test_network_paths.py` | Path assertions + `test_specialists_dir_isolated_per_network_root` |
| `tests/test_network_integration.py` | Include `MYCELIUM_SPECIALISTS_DIR` in env clearing |

## Verification

```bash
uv run pytest -m smoke -q tests/test_network_paths.py   # 8 passed
uv run pytest -m smoke -q                               # 91 passed
uv run ruff check src tests bin/                        # clean
```

## Checklist

| Item | Status |
|------|--------|
| `NetworkPaths.specialists_dir` → `<root>/specialists` | **PASS** |
| `apply_network_paths` sets `MYCELIUM_SPECIALISTS_DIR` | **PASS** |
| MCP refresh preserves `MYCELIUM_SPECIALISTS_DIR` | **PASS** |
| `create_specialist` storage paths from `MYCELIUM_AGENT_DATA_DIR` + slug | **PASS** |
| Two network roots → isolated `specialists/*.py` + `get_agent_fn` loads active root | **PASS** |

## Next queue item

`prompts/cursor/next/2026-06-09-1600-networks-phase5b-ontology-generator.md`
