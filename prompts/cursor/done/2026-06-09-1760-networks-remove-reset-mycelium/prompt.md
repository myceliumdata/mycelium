# Task: Remove `bin/reset-mycelium` (obsolete in networks model)

**Read these first (mandatory):**
- `prompts/cursor/WORKFLOW.md`
- `docs/plans/networks-phase5.md`
- Paul decision: **start a new network** instead of resetting in place

**Depends on:** polish (`2026-06-09-1750`) in `prompts/cursor/done/`.

**Blocks:** slice `1800` (docs).

---

## Objective

Remove **`bin/reset-mycelium`** and related tests/docs references. The networks product model replaces “reset the checkout” with:

| Old mental model | Replacement |
|------------------|-------------|
| Nuke generated specialists in `data/` | `network create` to a **new** `--root`, or delete the network directory |
| Reset categories to CRM six-pack | Custom ontology from creation prompt; `network create --force` to rebuild **same** root |
| Reset SQLite / checkpoints | New network root (isolated artifacts) or manual `rm` under `<network_root>/` |

`--categories` reset re-seeds from embedded `_SEED_CATEGORIES` — **wrong** for custom networks. Do not port this behavior elsewhere.

---

## Remove

- `bin/reset-mycelium`
- `tests/test_reset_mycelium.py` (if present)
- `test_reset_mycelium_scoped_to_active_network_root` in `tests/test_network_integration.py` (or replace with a one-line note that removal is intentional)
- README, `docs/architecture.md`, `data/README.md`, and any other **runtime** references to the script (minimal edits only — full doc pass is `1800`, but remove broken links/commands now)

---

## Do not remove

- `src/agents/specialists/*.py` committed CRM reference modules (framework code, not reset targets)
- `network create`, `copy-example-network`, registry commands

---

## Optional (only if trivial)

- `mycelium network unregister <name>` — **out of scope** unless already trivial; document manual registry edit in `output.md` for `1800`

---

## Verification

```bash
uv run pytest -m smoke -q
uv run ruff check src tests bin/
# Confirm script gone:
test ! -f bin/reset-mycelium
```

---

## Deliverables

`prompts/cursor/done/2026-06-09-1760-networks-remove-reset-mycelium/` with `prompt.md`, `output.md` (list files deleted + replacement workflows for docs).