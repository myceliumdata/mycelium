# Review: Networks Phase 5 polish (`1750`)

**Reviewer:** Grok  
**Date:** 2026-06-07  
**Verdict:** **Approved** — merge-quality; queue **`1760`** (remove reset-mycelium), not `1800` yet.

---

## Scope check (revised prompt — reset out of scope for 1750)

| Item | Status |
|------|--------|
| Shared `network_helpers.py` + env clearing | ✅ |
| `category_slug()` + public `registry_storage_paths()` in `base.py` | ✅ |
| `ontology.py` uses public helper | ✅ |
| Skip API key when `llm=` injected + test | ✅ |
| Duplicate slug + >8 category tests | ✅ |
| `--dry-run` no mkdir + test | ✅ |
| `--force` orphan specialist prune + test | ✅ |
| Atomic writes in `create.py` | ✅ |
| `pytest -m smoke` green (106 per output) | ✅ |

**Note:** Cursor also landed `reset-mycelium` + `test_reset_mycelium.py` (from an earlier prompt revision). Paul decided to **delete** the script in **`1760`** — that work is throwaway, not a 1750 blocker.

---

## What looks good

- **`registry_storage_paths()`** in `base.py` is the right home — no mkdir, network-relative paths, shared by ontology + factory.
- **`--dry-run`** no longer creates an empty root (`assert not root.exists()`).
- **`--force` orphan prune** is a real fix from 5c review — tested.
- **Test helpers** deduped cleanly into `tests/network_helpers.py`.

---

## Non-blocking niggles

1. **Dead code:** `agent_factory.py` still defines unused `_registry_storage_paths()` (old SpecialistStorage path). `create_specialist` correctly calls `registry_storage_paths` from `base.py`. Delete the dead function in **`1760`** or a one-line fix before merge.
2. **`output.md` §1800 note** references `reset-mycelium` — superseded; **`1760` output** should document “new network, not reset” for docs slice.

---

## Next step

**`2026-06-09-1760-networks-remove-reset-mycelium`** → then **`1800`**.