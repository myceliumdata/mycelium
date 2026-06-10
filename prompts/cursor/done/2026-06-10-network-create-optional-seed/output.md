# Network create v2 — optional `--seed`

## Summary

`mycelium network create` now works without `--seed` (empty registry until first bind, matching `empty-crm`). Shared `bootstrap_seed_at_paths()` consolidates seed import for create and refresh. Refresh script reports seed bootstrap in stdout.

## Changes

| Area | Files |
|------|-------|
| **Bootstrap helper** | `src/network/seed_import.py` (`bootstrap_seed_at_paths`, `count_seed_rows`) |
| **Network create** | `src/network/create.py` (optional `seed_path`, `entities_bootstrapped`, force clears stale seed/entities) |
| **Refresh** | `src/network/example.py` (`seed_bootstrap_count` on `RefreshExampleResult`) |
| **CLI** | `src/main.py` (optional `--seed`, bootstrap stdout) |
| **Script** | `bin/refresh-example-network` (seed import line) |
| **Tests** | `tests/test_network_create.py` (+3), `tests/test_example_network.py` (bootstrap assertions) |
| **Docs** | `README.md` (with/without seed examples, refresh auto-import note) |

### API change

`create_network(name, root, creation_prompt, *, seed_path=None, ...)` — `seed_path` moved to keyword-only optional arg.

## Verification

```bash
uv run ruff check src tests                    # All checks passed
rg 'required=True' src/main.py                 # --seed not required (other flags still required)
rg 'SeedRecord|seed_records' src/network/create.py   # no matches
LANGCHAIN_TRACING_V2=false uv run pytest -q tests/test_network_create.py tests/test_example_network.py   # 28 passed
LANGCHAIN_TRACING_V2=false uv run pytest -q   # 305 passed in 33.49s
```

## For Grok + Paul

- **Network launch v2** — optional `--seed` on `network create` is implemented; empty networks are first-class.
- **README** updated with both invocation styles and refresh auto-import behavior.
- **Breaking (minor):** `create_network()` call sites must pass `creation_prompt` before `seed_path=` (keyword).
- Safe to batch commit with identity rename slices after Grok review.
- Suggested commit message in `prompt.md`.
