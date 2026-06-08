# Review: Demo slice 1 — `bin/refresh-example-network`

**Reviewer:** Grok  
**Date:** 2026-06-08  
**Verdict:** **Approved** — fixes landed in `1050`; merge-ready; slice 2 unblocked.

---

## Scope check

| Requirement | Status |
|-------------|--------|
| `bin/refresh-example-network <name> [--root] [--register] [--default] [--no-default] [--yes] [--dry-run]` | ✅ |
| Prompt when live root exists; wipe on confirm / `--yes` | ✅ (see dry-run bug below) |
| Copy committed example files; skip README, `prepare_seed.py`, runtime artifacts | ✅ |
| Register by default; `crm` auto-default unless `--no-default` | ✅ (see `--no-default` caveat) |
| Shared logic in `src/network/example.py` | ✅ |
| `bin/copy-example-network` deleted | ✅ |
| `data/README.md` removed; no `data/` fallback in `resolve_network_root()` | ✅ |
| Docs: README quick start, demo runbook, CRM README, minimal architecture / walkthrough | ✅ |
| `.gitignore` — `data/*` entries removed | ✅ |
| Tests: empty root, replace, decline, crm default, dry-run, integration Nichanan | ✅ |
| `test_network_paths.py` — unconfigured raises with refresh pointer | ✅ |
| `uv run pytest -m smoke -q` | ✅ 110 passed |
| `uv run pytest -q` (full) | ✅ 129 passed |
| `uv run ruff check src tests bin/` | ✅ clean |

---

## What looks good

- **`src/network/example.py`** is a clean extraction: `_should_skip`, `copy_example_network`, `live_root_exists` (directory **or** registry path), `RefreshExampleResult`, and injectable `input_fn` for tests.
- **Wipe semantics** match the demo story — `shutil.rmtree` removes `specialists/`, `agents/`, DB, checkpoints, etc.; the replace test pre-seeds junk and asserts a clean tree.
- **`resolve_network_root()`** fails loud with `NO_NETWORK_CONFIGURED_MSG` pointing at `./bin/refresh-example-network crm` — no silent `<framework>/data` fallback.
- **Thin CLI** (`bin/refresh-example-network`) follows the venv bootstrap pattern; decline exits 0 with a clear message.
- **Test coverage** hits the spec table: subprocess decline, API-level replace/decline, isolated registry default, categories skip (`test_categories_sample.py`), and `test_refresh_example_register_and_query_nichanan` integration.
- **README demo runbook** (refresh → restart MCP → fresh `thread_id`) is exactly what Paul needs pre-demo.

---

## Issues

### Issue 1 — Severity: bug
- File: `src/network/example.py:138`
- Description: Confirmation runs **before** the `dry_run` branch (`155`). When a live root exists and `--yes` is omitted, `./bin/refresh-example-network crm --dry-run` blocks on stdin (EOFError in non-interactive use) and contradicts “print planned actions without writes.” Verified locally: fails without `--yes` when `~/mycelium-networks/crm` exists; passes with `--yes`.
- Suggestion: Skip the prompt when `dry_run=True`, or move the `dry_run` early-return above the confirmation block.
- Status: **fixed** (1050)

### Issue 2 — Severity: suggestion
- File: `tests/test_example_network.py:197`
- Description: `test_refresh_dry_run` always passes `--yes`, so it never exercises dry-run against an existing root without confirmation.
- Suggestion: Add a test: existing root + `--dry-run` only (no `--yes`) → exit 0, no writes, no prompt (via `input_fn` asserting it was not called).
- Status: **fixed** (1050)

### Issue 3 — Severity: suggestion
- File: `src/mycelium_mcp/server.py:43`
- Description: MCP `instructions` still say unset config “uses legacy `<framework>/data/`” — product bootstrap no longer uses that path.
- Suggestion: Update to “default from `~/.config/mycelium/networks.json`” and point unconfigured users to `./bin/refresh-example-network crm`.
- Status: **fixed** (1050)

### Issue 4 — Severity: suggestion
- File: `src/mycelium_mcp/server.py:70`
- Description: `_network_health_info()` falls back to `legacy_network_root()` when `network_metadata()` fails — reports `<framework>/data` after shim retirement (may be missing or stale local artifacts).
- Suggestion: Return `network_root: null` plus a short hint, or surface `NO_NETWORK_CONFIGURED_MSG`; update `test_network_health_info_legacy_fallback` accordingly.
- Status: **fixed** (1050)

### Issue 5 — Severity: suggestion
- File: `src/network/registry.py:128`
- Description: `--no-default` sets `make_default=False`, but `register_network(..., default=False)` still forces default when the registry is empty (`default or not networks`). First `crm --no-default` refresh may still mark default.
- Suggestion: Document limitation or pass an explicit “allow no default when sole network” flag into `register_network` (follow-up slice).
- Status: **fixed** (1050)

### Issue 6 — Severity: nit
- File: `TODO.md:81`
- Description: Paul hands-on test line still says `copy-example-network` instead of `refresh-example-network`.
- Suggestion: One-line update when merging.
- Status: **fixed** (1050)

### Issue 7 — Severity: nit
- File: `output.md:35`
- Description: Verification claims `./bin/refresh-example-network crm --dry-run` → OK; that only holds when the default live root is absent or `--yes` is passed.
- Suggestion: Fix the bug first, then re-verify; update output.md.
- Status: **fixed** (1050)

---

## Next step

All issues fixed in **`2026-06-08-1050-demo-slice1-review-fixes`** (approved). Proceed to **`2026-06-08-1100-demo-slice2-network-status`**.