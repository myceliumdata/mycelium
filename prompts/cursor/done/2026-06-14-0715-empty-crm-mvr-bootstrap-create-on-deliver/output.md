# Fix: empty-crm create-on-deliver — MVR bootstrap before bind write

## Summary

Step 2 create-on-deliver on no-seed networks (`empty-crm`) failed when `categories.json` lacked MVR `name`/`employer` mappings (classification seed omits them). `bind_provisional_from_scope` now calls `ensure_categories_for_mvr_bind` before unified bind write — same merge path as seeded CRM refresh.

## Changes

| Area | Change |
|------|--------|
| **`src/agents/target_deliver.py`** | `bind_provisional_from_scope` → `ensure_categories_for_mvr_bind(NetworkPaths.from_root(resolve_network_root()))` before `ensure_entity_bind_fields` |
| **`tests/test_empty_crm_create_on_deliver.py`** (new) | Smoke: classification seed without `name`/`employer` in `attribute_map` → step 1 + step 2 succeed; bind versions in demographic + professional storage |
| **`examples/networks/empty-crm/README.md`** | One-line note: step 2 auto-ensures MVR mappings |

## Root cause

Classification engine `_SEED_CATEGORIES` writes `categories.json` without `attribute_map.name` / `.employer`. Seeded networks get MVR merge via `seed_import.bootstrap_seed_at_paths`; no-seed networks hit step 2 bind without that merge → `resolve_attribute_owner` raises. `target_resolve` mapped the error to misleading "No valid delivery".

## Verification

```bash
./bin/ci-local
# CI local: all steps passed.
# 383 passed, 26 deselected
```

Manual sanity (Paul):

```bash
./bin/refresh-example-network empty-crm --yes
uv run mycelium query --network empty-crm \
  --lookup-json '{"name":"Paul Murphy","employer":"Acme Corp"}'
uv run mycelium query --network empty-crm --delivery-id <delivery_id>
# → outcome found, specialist storage populated
```

## For Grok + Paul

- **Gate blocker fixed** — Program 2 manual gate Check 4 can use `empty-crm` for create-on-deliver (update `docs/manual-checks/2026-06-13-program2-post-program-gate.md` after review).
- **Idempotent** — Seeded CRM create-on-deliver tests unchanged; merge skipped when mappings already present.
- **Not committed** — awaiting review.
- **TODO.md:** Unblock Program 2 gate / note fix in HOLD if desired.

Suggested commit message:

```
fix: bootstrap MVR category mappings on empty-crm create-on-deliver

Call ensure_categories_for_mvr_bind before provisional bind write so
no-seed networks merge name/employer into categories.json; add smoke
test and empty-crm README note.
```
