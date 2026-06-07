# Review: Networks Phase 5c — `mycelium network create` CLI

**Reviewer:** Grok  
**Date:** 2026-06-07  
**Verdict:** **Approved** — merge-quality; queue `1750` polish then `1800` docs.

---

## Scope check

| Requirement | Status |
|-------------|--------|
| `mycelium network create` subcommand + all flags | ✅ |
| `src/network/create.py` orchestration | ✅ |
| Seed validate before ontology | ✅ |
| `network.json` manifest fields | ✅ |
| Write categories, registry, specialists, seed | ✅ |
| `register_network` + optional `--default` | ✅ |
| `--dry-run` / `--force` / `--no-mcp-snippet` | ✅ |
| MCP snippet with `MYCELIUM_NETWORK_ROOT` | ✅ |
| Mocked tests + full integration (non-CRM ontology query) | ✅ |
| Manual checklist template (post-1800) | ✅ |
| No framework git commit on create | ✅ |

Independent verification:

```bash
pytest -m smoke tests/test_network_create.py  # 6 passed
pytest -m full tests/test_network_create.py   # 1 passed
ruff check src/network/create.py src/main.py tests/test_network_create.py  # clean
```

---

## What looks good

- **`ontology_fn` injection** on `create_network()` — clean test seam; integration test proves custom ontology drives query (not `_SEED_CATEGORIES`).
- **Ordering:** validate name/seed → ontology → artifacts → register; invalid seed never calls ontology.
- **CLI UX:** Rich summary, dry-run preview, MCP snippet; catches `OntologyGenerationError`.
- **Specialist render** uses `AgentFactory.render_specialist_py` + `SpecialistStorage` under active `NetworkPaths` — aligns with 5a layout.
- **Name validation** (`^[a-z][a-z0-9_]*$`) documented in `output.md`.

---

## Non-blocking niggles → **`1750` polish**

1. **`--dry-run` mkdir** — `create_network` creates `network_root` before dry-run return; empty dir may exist with no artifacts. Optional: defer `mkdir` until non-dry-run, or document in `1800`.
2. **`--force` stale specialists** — re-create overwrites matching `categories.json` / registry / py files but does not remove orphan `specialists/*.py` from a prior ontology with different agent names. Optional: prune `specialists/` to registry agent set on force.
3. **Non-atomic JSON writes** — `_write_categories` / `_write_agent_registry` use direct `write_text`; registry engine uses temp+replace. Low risk for create; optional align later.
4. **No CLI subprocess test** — API-level tests sufficient for v1; optional `mycelium network create` subprocess smoke in polish or post-ship.

---

## Next step

Proceed with **`2026-06-09-1750-networks-phase5-polish`**, then **`1800`**.