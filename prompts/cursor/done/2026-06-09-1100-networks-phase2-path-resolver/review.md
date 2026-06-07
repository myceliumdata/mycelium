# Review: Networks Phase 2 — path resolver + CLI/MCP wiring (slice 1100)

**Reviewer:** Grok  
**Verdict:** **Approved** — ready to commit and check off TODO.

## Scope compliance

| Requirement | Status |
|-------------|--------|
| `src/network/paths.py` — resolve, `NetworkPaths`, `apply_network_paths` | **Done** |
| Precedence: `--network-dir` → `MYCELIUM_NETWORK_ROOT` → `<framework>/data` | **Done** |
| `MYCELIUM_FRAMEWORK_ROOT` + package inference | **Done** |
| CLI `--network-dir` on `query` | **Done** |
| MCP `_bootstrap()` + `health_check` `info.network_root` | **Done** |
| `bin/reset-mycelium` respects active root | **Done** |
| Legacy shim (zero config = prototype `data/`) | **Done** — verified |
| Smoke tests `tests/test_network_paths.py` (7) | **Done** |
| README `--network-dir` | **Done** |
| No `--network` name registry | **Done** |
| No CRM move / examples | **Done** |

## Code quality

- Central `apply_network_paths()` sets all `MYCELIUM_*` paths consumed by seed, registry, classification, factory, storage, checkpoints — clean reuse of existing env-based wiring.
- Framework root from package location (not cwd) is correct for MCP with framework `cwd` + external network paths.
- `network_display_name()` is a nice forward-compatible helper (reads `network.json`); not yet surfaced in `health_check` — acceptable for Phase 2.

## Verification (re-run)

```
uv run pytest -m smoke -q  →  64 passed (+7 network paths)
uv run ruff check src tests bin/  →  clean
```

Legacy resolution:

```
resolve_network_root() → .../mycelium/data (seed.json present)
framework_root() → repo root
```

## Non-blocking notes

1. **`mycelium seed`** subcommand does not call `_configure_network_paths()` — still legacy SQLite load with pre-network defaults. Fine for deprecated `seed` cmd; document or wire in Phase 3/4 if needed.
2. **`health_check` error payload** falls back to `Path("data").resolve()` (cwd-relative) if env unset — rare; could use `framework_root() / "data"` in a polish slice.
3. **`network_display_name`** could be added to `health_check` `info` in Phase 3 polish (optional).
4. Consider one-line `.env.example` note for `MYCELIUM_NETWORK_ROOT` / `MYCELIUM_FRAMEWORK_ROOT` in Phase 3 or 4.

## Success criteria

Met. Unblocks parallel MCP servers via per-config `MYCELIUM_NETWORK_ROOT`. Proceed to **Phase 3** (`2026-06-07-1200-networks-phase3-network-registry.md`).