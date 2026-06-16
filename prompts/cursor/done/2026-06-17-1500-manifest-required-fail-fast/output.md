# Manifest required — fail fast (remove MVR/entity legacy shims)

## Summary

Removed silent CRM defaults and legacy compatibility shims. **`network.json` is now required** with explicit `mvr.grains`, `mvr.default_grain`, and `metering`. Flat `mvr.bind_fields` and root `entities.json` read fallback are rejected.

## Key changes

| Area | Change |
|------|--------|
| `network/mvr.py` | Strict `load_mvr_config()`; rejects flat `bind_fields`; requires `default_grain` always; deleted `_crm_default_config()` / `_crm_default_mvr()` |
| `network/metering_policy.py` | Strict `load_metering_policy()`; deleted `_crm_default_metering()` silent fallback |
| `network/paths.py` | Deleted `resolve_entity_store_path()`; `entities_path` from manifest only |
| `agents/entity_registry.py` | Single canonical path via `entity_store_path()` (env override for default grain only) |
| `network/create.py` | Writes full `bootstrap`, `mvr.grains.person`, and `metering` before other setup |
| `tests/network_helpers.py` | `copy_crm_network_manifest()`, `write_metering_network_json()`, `crm_person_entities_path()` |
| Tests | All fixtures use CRM-shaped manifests; fail-fast tests use `_provisional_paths()` |

## Locked behavior

- Missing `network.json`, `mvr`, `metering`, or `default_grain` → `ValueError` with actionable message
- Flat `mvr.bind_fields` → rejected
- Root `entities.json` not read as fallback; writes go to `entities/<grain>.json`
- `network create` writes complete CRM-shaped manifest
- CRM regression: 15 seed entities, capstones green

## Tests

Updated fixtures across admin, status, metering, paths, integration, and graph tests. `tests/test_multi_mvr_entity_stores.py` includes `test_flat_bind_fields_rejected` and missing-section raises.

## Docs

- `docs/architecture.md`, `docs/onboarding.md`, `README.md`, `docs/database-notes.md` — canonical `entities/<grain>.json`, no fallback language

## Verification

```bash
./bin/ci-local
# CI local: all steps passed.
# 433 passed, 93 deselected
```

## For Grok + Paul

- **Next slice:** `LahmanSeedHandler` in `examples/networks/baseball/bootstrap_handlers/` — populate player/team grains.
- Suggested commit:

```
refactor(network): require explicit network.json mvr and metering

Remove CRM silent defaults and legacy flat bind_fields / root
entities.json shims. Fail fast on missing manifest sections;
network create writes full mvr.grains and metering blocks.
```

- Do **not** commit from this slice deliverable.
