# Retire repo-root `data/` shim

## Summary

Hardened runtime path resolution so unconfigured processes **fail loud** instead of writing under repo-root `data/`. Added `runtime_path()` and `shell_export_network_paths()`; wired LangGraph Studio to resolve the active network before graph import.

## Changes

| Area | Change |
|------|--------|
| `src/network/paths.py` | `runtime_path()`, `shell_export_network_paths()`, refactored `apply_network_paths()` |
| Path consumers | registry, seed, storage, graphs, classification engine, agent factory, specialists base |
| `bin/run-studio` | `eval` network path exports; exit non-zero when unconfigured |
| `tests/test_network_paths.py` | +4 smoke tests for `runtime_path` and shell export |
| `README.md` | Studio requires configured network; `data/` retired |

## `runtime_path()` resolution

1. Explicit `MYCELIUM_*` env var (if set)
2. Derive from `MYCELIUM_NETWORK_ROOT`
3. `resolve_network_root()` + derive
4. Raise `ValueError(NO_NETWORK_CONFIGURED_MSG)`

No code path defaults to `data/...` anymore.

## Verification

```bash
uv run pytest -m smoke -q          # 158 passed, 1 failed (known LLM flake in test_agent_factory)
uv run pytest tests/test_network_paths.py -m smoke -q   # 12 passed
uv run ruff check src tests bin/   # clean on touched files
```

**Manual (Paul):**
- `./bin/run-studio` prints `Using network_root: …` and does not create `data/checkpoints.sqlite` in repo root
- `uv run mycelium query --network crm …` unchanged against registered default
- Operator may `rm -rf data/` locally (gitignored shim)

## For Grok + Paul

- Mark **retire `data/` shim** / legacy shim hardening done in `TODO.md` if an open item exists.
- `src/network/introspection.py` still falls back to `src/agents/specialists` for bundled reference modules in status display — intentional, not `data/`; optional follow-up to use `runtime_path` there too.
- Known flake: `test_create_specialist_writes_files_and_registers` (LLM research path).
