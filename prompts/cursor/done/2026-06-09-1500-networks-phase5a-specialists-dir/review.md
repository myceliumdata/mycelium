# Review: Networks Phase 5a — per-network `specialists/` + env wiring

**Reviewer:** Grok  
**Date:** 2026-06-07  
**Verdict:** **Approved** — merge-quality; queue `1600`.

---

## Scope check

| Requirement | Status |
|-------------|--------|
| `NetworkPaths.specialists_dir` → `<root>/specialists` | ✅ |
| `apply_network_paths` sets `MYCELIUM_SPECIALISTS_DIR` | ✅ |
| `refresh_runtime_from_disk` preserves specialists dir | ✅ |
| Factory storage paths from `MYCELIUM_AGENT_DATA_DIR` + slug | ✅ |
| Network-relative registry paths when under `MYCELIUM_NETWORK_ROOT` | ✅ |
| Two-root isolation test | ✅ |
| Integration test env clearing updated | ✅ |
| No CLI / ontology / docs scope creep | ✅ |

Independent verification: `pytest -m smoke tests/test_network_paths.py` — 8 passed; ruff clean.

---

## What looks good

- **`_registry_storage_paths()`** is a clean extraction; network-relative paths (`agents/foo/storage.json`) will serialize correctly in per-network `agent_registry.json`.
- **Isolation test** exercises the full chain: `apply_network_paths` → factory write → `get_agent_fn` loads from active root's `specialists/`.
- **MCP parity:** `MYCELIUM_SPECIALISTS_DIR` in `_NETWORK_PATH_ENV_KEYS` matches the Phase 4.5 path-preservation pattern.

---

## Non-blocking niggles (polish backlog — not 5a blockers)

1. **`bin/reset-mycelium`** still hardcodes `src/agents/specialists/`. → **Queued:** `2026-06-09-1750-networks-phase5-polish` (after 5c, before 5d).
2. **`_NETWORK_PATH_ENV_KEYS` duplicated** in test modules. → **Queued:** `1750`.
3. **`_registry_storage_paths`** mkdir side effect via `SpecialistStorage`. → **Queued:** `1750`.

---

## Next step

Proceed with **`2026-06-09-1600-networks-phase5b-ontology-generator`** (done) → **`1700`** → **`1750`** → **`1800`**.