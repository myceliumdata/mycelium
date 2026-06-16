# Bootstrap progress reporting (stderr phases + x/y)

## Summary

Added **`BootstrapProgress`** (`src/network/bootstrap/progress.py`) with stderr phases: **Retrieving data…**, **Processing records (x/y)…**, **Cleaning up…**. Wired through seed fetch, `BootstrapContext`, Lahman handler (player bind loop), light CRM seed import, and deferred entity flush in `run_network_bootstrap`.

## Key changes

| Area | Change |
|------|--------|
| `src/network/bootstrap/progress.py` | TTY `\r` updates; non-TTY coarse intervals; `MYCELIUM_BOOTSTRAP_PROGRESS` env |
| `src/network/bootstrap/run.py` | `_bootstrap_deferred_with_progress` emits cleaning up before `commit_deferred_save` |
| `src/network/seed_fetch.py` | `retrieving` during git clone |
| `src/network/example.py` | Shared progress instance for fetch + bootstrap |
| `lahman_seed.py` | Warehouse retrieving + player loop `(x/y)` |
| `default_seed.py` | Optional processing counter for seed rows |
| `tests/test_bootstrap_progress.py` | Disabled/forced-on phases, CRM unchanged |
| `examples/networks/baseball/README.md` | stderr progress note |

## Verification

```bash
./bin/ci-local
# CI local: all steps passed.
# 466 passed, 97 deselected
```

## For Grok + Paul

- Operators can watch stderr during **timing test 5**; no timing expectation change from this slice alone.
- `next/` is empty after this slice.
- Suggested commit:

```
feat(bootstrap): stderr progress phases for long network refresh

Add BootstrapProgress (retrieving / processing x/y / cleaning up) wired
through bootstrap context, seed fetch, Lahman handler, and deferred
entity flush. TTY-aware updates; MYCELIUM_BOOTSTRAP_PROGRESS env knob.
```

- Do not commit from Cursor unless Paul asks.
