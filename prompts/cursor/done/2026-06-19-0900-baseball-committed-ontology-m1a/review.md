# Review — baseball committed ontology (M1a)

**Verdict:** **Approved**  
**Reviewer:** Grok  
**Date:** 2026-06-19

## Scope checked

Full read of M1a deliverables:

- `examples/networks/baseball/categories.json` — matches locked ontology (6 categories, `ontology_pack: baseball`, no CRM categories).
- `src/network/pack_ontology.py` — generic install (`is_pack_ontology`, `install_pack_ontology_from_example`, `maybe_install_pack_ontology`); agent registry + stub specialists only when `.py` missing.
- `src/network/example.py` — install after copy (full refresh + `--sync-only`).
- `src/network/bootstrap/run.py` — `maybe_install_pack_ontology` before MVR merge.
- `src/network/category_mvr_bootstrap.py` — pack path merges bind fields only; never replaces with CRM sample.
- `src/agents/classification/models.py` — optional `ontology_pack` on `CategoryTreeData`.
- `tests/test_baseball_pack_ontology.py` — validation, refresh install, routing, CRM regression.
- `bin/smoke-baseball-e2e` — `career_hr` step-2 routes to `batting_specialist` via debug blob.
- `examples/networks/baseball/README.md` — ontology table + sync-only note.

## CI

| Check | Result |
|-------|--------|
| `./bin/ci-local` | **556** smoke passed, ruff clean, admin-ui build ok |
| `./bin/smoke-baseball-e2e` (clean env) | **7** scenarios passed |

Note: `./bin/smoke-baseball-e2e` fails if `MYCELIUM_NETWORK_ROOT` points at an old benchmark tree with legacy `network.json` (`default_grain`). Script default (temp fixture) is fine; operators should unset or refresh stale roots.

## Architecture fit

- Framework stays generic — `ontology_pack` convention, no Lahman logic in supervisor/classification hot path.
- CRM refresh test confirms sample taxonomy unchanged.
- Refresh re-applies committed pack ontology (intended for `--sync-only` ontology updates); stub specialists not overwritten when `.py` already exists (ready for M1b pack override).

## Polish nits (non-blocking)

| # | Nit | Suggestion |
|---|-----|------------|
| P1 | `install_pack_ontology_from_example` always rewrites `agent_registry.json` on refresh | Document that pack refresh resets registry; operator-custom agents need a follow-up story. |
| P2 | `_agents_from_category_tree` dedupes by `assigned_agent` — only first category wins in registry if one agent ever owns two categories | Fine for baseball; note if multi-category agent pattern appears later. |
| P3 | Smoke script sensitive to stale `MYCELIUM_NETWORK_ROOT` | Optional: script unsets env or validates manifest before import (follow-up). |

## Commit plan

Commit **M1a files only** (exclude unrelated fuzzy/docs/TODO working-tree edits in same commit).

**Suggested message:** `baseball: committed pack ontology (M1a) + refresh install`