# Multi-MVR entity stores — framework slice

## Summary

Added framework plumbing for **per-grain entity stores** and **`mvr.grains`** in `network.json`. Query orchestration still uses the **default grain only**; no query graph changes.

## Key changes

| Area | Change |
|------|--------|
| `network/mvr.py` | `NetworkMvrConfig`, `load_mvr_config()`, `load_mvr(grain=...)`, `default_mvr_grain()`, `list_mvr_grains()`; legacy flat `bind_fields` → implicit `person` grain |
| `network/paths.py` | `entity_store_path()`, `resolve_entity_store_path()` (legacy `entities.json` read fallback); `entities_path` = default grain path |
| `agents/entity_registry.py` | Per-grain singleton cache; read/write path split; grain-threaded `MvrPolicy` |
| `bootstrap/default_seed.py` | Writes `person` grain (or `default_grain` when `person` absent); `entities_by_grain` on result |
| `network/create.py` | Force cleanup unlinks all declared grain entity files |
| `network/example.py` | Skip runtime `entities/` on example copy |
| Example manifests | CRM examples: `default_grain` + `grains.person`; baseball: `player` + `team` grains |
| `attribute_write.py` | `ensure_entity_bind_fields` uses registry grain's MVR policy when registry passed |

## Schema

```json
"mvr": {
  "default_grain": "person",
  "grains": {
    "person": {
      "bind_fields": ["name", "employer"],
      "description": "..."
    }
  }
}
```

Entity files: `<network_root>/entities/<grain>.json`. Legacy root `entities.json` readable when grain file missing; writes target grain path.

## Tests

New `tests/test_multi_mvr_entity_stores.py` (9 tests). Updated example network, capstone, create, admin, capabilities, and registry bind tests for grain paths.

## Docs

- `docs/architecture.md` — per-grain stores, `mvr.grains`, legacy fallback, query path note
- `docs/onboarding.md` — entity store layout

## Verification

```bash
./bin/ci-local
# CI local: all steps passed.
# 429 passed, 93 deselected
```

## For Grok + Paul

- **Next slice:** `LahmanSeedHandler` in `examples/networks/baseball/bootstrap_handlers/` — populate player/team grains.
- **Then:** query orchestrator grain selection (`target_resolve`, supervisor).
- Suggested commit:

```
feat(network): multi-MVR entity stores per grain

Declare mvr.grains in network.json; per-grain entities/<grain>.json
stores; load_mvr/get_entity_registry default-grain compat; bootstrap
resets all grains. Query path unchanged (default grain only).
```

- Do **not** commit from this slice deliverable.
