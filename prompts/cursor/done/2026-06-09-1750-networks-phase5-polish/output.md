# Output: Networks Phase 5 polish

## Checklist

| # | Item | Status |
|---|------|--------|
| 1 | `reset-mycelium` cleans `<network_root>/specialists/` (not `src/agents/specialists/`) | **PASS** |
| 1b | Git rm skipped for paths outside `REPO_ROOT` | **PASS** |
| 1c | Smoke test: dry-run `--specialist` reports network specialists path | **PASS** |
| 2 | Shared `NETWORK_PATH_ENV_KEYS` + `clear_network_path_env` in `tests/network_helpers.py` | **PASS** |
| 3 | `category_slug()` + public `registry_storage_paths()` in `base.py` | **PASS** |
| 4 | Ontology skips API key check when `llm=` injected | **PASS** |
| 5 | Ontology validation tests (duplicate slug, >8 categories) | **PASS** |
| 6a | `--dry-run` does not create `network_root` | **PASS** |
| 6b | `--force` prunes orphan `specialists/*.py` | **PASS** |
| 6c | Atomic writes for `categories.json` / `agent_registry.json` | **PASS** |
| 7 | Note for slice `1800` (below) | **PASS** |

## Verification

```bash
uv run pytest -m smoke -q   # 106 passed
uv run ruff check src tests bin/   # clean
```

## Note for slice `1800` (docs)

**`reset-mycelium`:** Operates on the active `network_root` (via `MYCELIUM_NETWORK_ROOT` or legacy `data/`). Specialist `.py` cleanup targets `<network_root>/specialists/` only. Framework-committed CRM modules in `src/agents/specialists/` are never removed by reset. Git staging applies only to paths under the repo root; user network roots outside the clone are filesystem-only.

**`network create --force`:** Overwrites ontology artifacts and prunes orphan `specialists/*.py` files not listed in the new `agent_registry.json` before re-rendering. `--dry-run` validates seed + ontology without creating `network_root` or writing files.

## Files changed

- `bin/reset-mycelium`
- `src/agents/specialists/base.py`
- `src/agents/factory/agent_factory.py`
- `src/network/ontology.py`
- `src/network/create.py`
- `tests/network_helpers.py` (new)
- `tests/test_network_paths.py`, `tests/test_network_integration.py`
- `tests/test_network_ontology.py`, `tests/test_network_create.py`
- `tests/test_reset_mycelium.py` (new)

## Next queue item

`prompts/cursor/next/2026-06-09-1800-networks-phase5d-docs.md`
