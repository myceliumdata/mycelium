# Task: Demo slice 1 — review fixes

**Read these first (mandatory):**
- `prompts/cursor/WORKFLOW.md` — claim by moving this file to `in-progress/` before starting
- `prompts/cursor/done/2026-06-08-1000-demo-slice1-refresh-example-network/review.md` — source of all fixes below
- `prompts/cursor/done/2026-06-08-1000-demo-slice1-refresh-example-network/output.md`
- `src/network/example.py`, `src/network/registry.py`, `src/mycelium_mcp/server.py`
- `tests/test_example_network.py`, `tests/test_network_polish.py`, `tests/test_network_registry.py`

**Depends on:** Demo slice 1 implementation (local or merged).

**Blocks:** Demo slice 2 (`2026-06-08-1100-demo-slice2-network-status.md`) — complete this prompt first.

---

## Workflow

Follow `prompts/cursor/WORKFLOW.md`:

1. Move this file from `prompts/cursor/next/` → `prompts/cursor/in-progress/`.
2. Implement all fixes below.
3. Deliver to `prompts/cursor/done/2026-06-08-1050-demo-slice1-review-fixes/` with `prompt.md`, `output.md`.
4. Remove **only** your claimed file from `in-progress/`.
5. Update `review.md` in the slice 1 done folder: set each fixed issue's **Status** to `fixed` (or append a short “Fixed in 1050” note at the bottom).

---

## Objective

Fix every open issue from the slice 1 review so slice 1 is merge-ready and slice 2 can proceed.

---

## Fixes (all required)

### 1. Bug — dry-run must not prompt (`src/network/example.py`)

**Problem:** When a live root exists, confirmation runs before the `dry_run` branch. `./bin/refresh-example-network crm --dry-run` EOFs without `--yes`.

**Fix:** `--dry-run` must never call `input()` / `input_fn`. Either:
- Move the `dry_run` early-return **above** the confirmation block, or
- Add `and not dry_run` to the confirmation guard.

Behavior after fix:
- Existing root + `--dry-run` (no `--yes`) → exit 0, prints “Would refresh…”, no writes, no prompt.
- Existing root + real refresh (no `--yes`) → still prompts.

### 2. Test — dry-run without `--yes` (`tests/test_example_network.py`)

Add a smoke test that an existing root is left unchanged when dry-running **without** `--yes` and **without** stdin:

- Prefer API test: `refresh_example_network(..., dry_run=True)` on a pre-seeded `tmp_path` root; assert `declined` is false, files unchanged, and use a sentinel `input_fn` that raises `AssertionError("should not prompt")` if called.
- Keep existing `test_refresh_dry_run` (subprocess with `--yes` is fine as additional coverage).

### 3. MCP instructions — remove legacy `data/` (`src/mycelium_mcp/server.py`)

In `_build_mcp_instructions`, replace the sentence that says unset config “uses legacy `<framework>/data/`”.

**New wording (substance, not necessarily verbatim):** Each MCP process binds to one network via `MYCELIUM_NETWORK_ROOT`, `MYCELIUM_NETWORK`, or the **default** from `~/.config/mycelium/networks.json`. Unconfigured installs should run `./bin/refresh-example-network crm` first.

### 4. MCP health fallback — no `legacy_network_root()` (`src/mycelium_mcp/server.py`)

In `_network_health_info()`, when `network_metadata()` raises, do **not** fall back to `legacy_network_root()`.

**Preferred shape:**
```python
{
    "network_root": None,
    "network_name": env_name or None,  # keep MYCELIUM_NETWORK if set
    "network_display_name": None,
    "network_configure_hint": NO_NETWORK_CONFIGURED_MSG,  # import from network.paths
}
```

- Import `NO_NETWORK_CONFIGURED_MSG` from `network.paths`.
- Remove `legacy_network_root` import from this function if unused afterward.
- Update `tests/test_network_polish.py::test_network_health_info_legacy_fallback`:
  - Rename if helpful (e.g. `test_network_health_info_unconfigured_hint`).
  - Assert `network_root` is `None` and `network_configure_hint` matches refresh pointer.
- If `health_check` JSON consumers assume `network_root` is always a string, grep callers/tests and adjust only as needed (minimal).

### 5. `--no-default` must work on empty registry (`src/network/registry.py` + `src/network/example.py`)

**Problem:** `register_network(..., default=False)` still forces default when the registry is empty (`default or not networks`).

**Fix:** Add an optional parameter to `register_network`, e.g. `allow_no_default: bool = False`.

When `allow_no_default=True` and `default=False`:
```python
make_default = existing.default if existing else False
```

When `allow_no_default=False`, keep **existing** behavior (first registration becomes default — `test_first_registration_becomes_default` must still pass).

Wire from `refresh_example_network`:
- Pass `allow_no_default=True` when the user passed `--no-default` **or** when `make_default` is explicitly `False` from the `--default`/`--no-default`/`crm` auto logic (i.e. not the “first network auto-default” path).

Add smoke test: isolated `MYCELIUM_NETWORKS_CONFIG`, `refresh_example_network("crm", ..., yes=True, no_default=True)` → `result.is_default is False` and registry entry has `default=False`.

Do **not** change `network create` behavior unless required for compilation; `create.py` can keep `allow_no_default=False`.

### 6. Nit — `TODO.md`

Line ~81: change `copy-example-network` → `refresh-example-network` in the Paul hands-on test bullet.

### 7. Nit — slice 1 `output.md`

In `prompts/cursor/done/2026-06-08-1000-demo-slice1-refresh-example-network/output.md`, update verification to note `./bin/refresh-example-network crm --dry-run` works **without** `--yes` when a live root exists (after fix 1).

### 8. Nit — stale plan doc (minimal)

In `docs/plans/networks-terminology.md` line ~11: replace `bin/copy-example-network` with `bin/refresh-example-network` and remove “empty runtime shim until populated” (shim is retired). One paragraph only — no full doc sweep.

### 9. Hygiene — ignore retired `data/` directory (`.gitignore`)

Add a top-level `data/` ignore (directory) so leftover local runtime artifacts (`categories.json`, `*.sqlite`, etc.) cannot be accidentally committed after shim removal. Do not recreate `data/README.md`.

---

## Verification

```bash
uv run pytest -m smoke -q
uv run ruff check src tests bin/
./bin/refresh-example-network crm --dry-run    # must exit 0 without --yes (if ~/mycelium-networks/crm exists)
```

Document results in `output.md`. If you add the new `--no-default` registry test, it is smoke.

---

## Scope boundaries

**May modify:**
- `src/network/example.py`
- `src/network/registry.py`
- `src/mycelium_mcp/server.py`
- `tests/test_example_network.py`
- `tests/test_network_polish.py`
- `tests/test_network_registry.py` (only if needed for `allow_no_default`)
- `.gitignore`
- `TODO.md`
- `docs/plans/networks-terminology.md` (one line per fix 8)
- `prompts/cursor/done/2026-06-08-1000-demo-slice1-refresh-example-network/output.md`
- `prompts/cursor/done/2026-06-08-1000-demo-slice1-refresh-example-network/review.md` (status updates only)

**Out of scope:**
- Demo slice 2 (`network status`)
- Broader doc rewrites (`docs/plans/networks-phase5.md`, README, architecture)
- Removing `legacy_network_root()` from `paths.py` (tests may still use it; MCP must not)

If you believe a fix requires out-of-scope changes, stop, document in `output.md`, and do not expand scope.

---

## Deliverables

`prompts/cursor/done/2026-06-08-1050-demo-slice1-review-fixes/`:
- `prompt.md` (this file)
- `output.md` — checklist mapping each review issue → fix, verification commands, open questions

After merge-ready: slice 2 (`1100`) remains next in queue.