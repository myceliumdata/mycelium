# Review: Remove `bin/reset-mycelium` (`1760`)

**Reviewer:** Grok  
**Date:** 2026-06-07  
**Verdict:** **Approved** — merge-quality; queue **`1800`** (Phase 5 docs).

---

## Scope check

| Item | Status |
|------|--------|
| `bin/reset-mycelium` deleted | ✅ |
| `tests/test_reset_mycelium.py` deleted | ✅ |
| `test_reset_mycelium_scoped_to_active_network_root` removed from integration tests | ✅ |
| Runtime docs updated (README, `data/README.md`, `docs/architecture.md`, `docs/plans/networks-terminology.md`) | ✅ |
| No stale reset references in `src/`, `tests/`, `bin/` | ✅ |
| Historical `prompts/cursor/done/*` left unchanged | ✅ (per prompt) |
| Replacement workflows documented for `1800` | ✅ |
| `uv run pytest -m smoke -q` | ✅ 105 passed |

---

## Post-review cleanup (Grok)

Removed dead `_registry_storage_paths()` from `src/agents/factory/agent_factory.py` — leftover from 1750 polish; `create_specialist` already uses public `registry_storage_paths()` from `base.py`.

---

## What looks good

- Clean product-model shift: fresh start = `network create` or `copy-example-network`; rebuild same root = `--force`.
- README "Rebuild or start fresh" section gives accurate replacement commands before the full `1800` docs pass.
- `seed.json` never overwritten by create (even `--force`) — correctly noted for docs.

---

## Next step

**`2026-06-09-1800-networks-phase5d-docs`** — close Phase 5 documentation loop; then Paul hands-on testing and README banner removal.