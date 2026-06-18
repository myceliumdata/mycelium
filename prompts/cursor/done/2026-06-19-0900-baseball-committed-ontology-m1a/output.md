# Output — baseball committed ontology (M1a)

## Summary

Shipped committed `examples/networks/baseball/categories.json` (`ontology_pack: baseball`) and generic pack install on refresh/bootstrap. Baseball attributes route to baseball specialists (`career_hr` → `batting_specialist`, `team` → `team_identity_specialist`); CRM refresh unchanged.

## Changes

| Area | Change |
|------|--------|
| `examples/networks/baseball/categories.json` | Locked Lahman-informed ontology (6 categories, full `attribute_map`) |
| `src/network/pack_ontology.py` | `is_pack_ontology`, `install_pack_ontology_from_example`, `maybe_install_pack_ontology`; agent registry + stub specialists |
| `src/network/example.py` | Install pack ontology after `copy_example_network` (full + sync-only) |
| `src/network/bootstrap/run.py` | `maybe_install_pack_ontology` before `ensure_categories_for_mvr_bind` |
| `src/network/category_mvr_bootstrap.py` | Pack ontology path merges MVR fields only — never replaces with CRM sample |
| `src/agents/classification/models.py` | Optional `ontology_pack` field on `CategoryTreeData` |
| `tests/test_baseball_pack_ontology.py` | Pack validation, refresh install, classification routing, CRM regression |
| `bin/smoke-baseball-e2e` | `career_hr` step-2 routes to `batting_specialist` |
| `examples/networks/baseball/README.md` | Committed ontology table; sync-only note |

## Install contract

- Only copies when example `categories.json` has non-empty `ontology_pack` (stray/invalid CRM files ignored).
- `categories.json` remains in `_SKIP_NAMES` for blind copy; explicit install is the path.
- `ensure_categories_for_mvr_bind` respects existing pack ontology.

## Verification

| Check | Result |
|-------|--------|
| `./bin/ci-local` | **556** smoke passed |
| `./bin/smoke-baseball-e2e` | **7** scenarios passed |

## For Grok + Paul

- Mark **M1a** done in `TODO.md` when approved.
- **M1b next:** first warehouse specialist + computation-centric provenance writer.
- Existing `~/mycelium-networks/baseball` roots: `./bin/refresh-example-network baseball --sync-only` picks up ontology without Lahman re-bootstrap.
- Specialists are stubs — step-2 outcomes may be `found`/`assembled` with empty/pending attrs; routing is the gate.
- No commit (per workflow).

**Suggested commit message:**

```
baseball: committed pack ontology (M1a) + refresh install

Install schema-informed categories.json for baseball example; route
career_hr/team/bio to baseball specialists instead of CRM taxonomy.
```
