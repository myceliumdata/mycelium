# Output: Remove `bin/reset-mycelium` (1760)

## Deleted

| File | Notes |
|------|-------|
| `bin/reset-mycelium` | Dev reset script (obsolete in networks model) |
| `tests/test_reset_mycelium.py` | Unit tests for script |

## Edited (runtime docs / tests)

| File | Change |
|------|--------|
| `tests/test_network_integration.py` | Removed section 6 `test_reset_mycelium_scoped_to_active_network_root` |
| `README.md` | Replaced "Dev reset" with "Rebuild or start fresh"; removed tree entry |
| `data/README.md` | Point to `network create` / manual wipe instead of reset script |
| `docs/architecture.md` | Seed copy/rebuild wording; no reset-mycelium |
| `docs/plans/networks-terminology.md` | Bootstrap wiring note (no reset script) |
| `TODO.md` | Marked 1760 complete |

Historical references in `prompts/cursor/done/*` and `prompts/resets/*` left unchanged.

## Replacement workflows (for `1800` docs pass)

| Old mental model | Replacement |
|------------------|-------------|
| Nuke generated specialists | `mycelium network create <name> --root <new_path> ...` or delete the network directory |
| Reset categories to CRM six-pack | Custom ontology from creation prompt; `network create --force` on same root |
| Reset SQLite / checkpoints | New `--root` (isolated artifacts) or manual `rm` under `<network_root>/` |
| CRM quick start | `./bin/copy-example-network crm --root ~/mycelium-networks/crm --register --default` |
| Remove network from registry | **No `unregister` CLI yet** — edit `~/.config/mycelium/networks.json` (or path in `MYCELIUM_NETWORKS_CONFIG`) manually |

`seed.json` is never overwritten by `network create` (even with `--force`). Only ontology/runtime artifacts are rebuilt.

## Verification

```text
uv run pytest -m smoke -q   → 105 passed
uv run ruff check src tests bin/  → clean
test ! -f bin/reset-mycelium  → OK
```

## Unblocks

`prompts/cursor/next/2026-06-09-1800-networks-phase5d-docs.md`
