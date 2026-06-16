# Bootstrap handler selection via `network.json`

## Summary

Replaced the legacy `specialists/bootstrap_specialist.py` file-presence override with explicit **`network.json` → `bootstrap`** handler selection. Built-in handlers resolve via a framework registry (`default_seed` → `DefaultSeedHandler`); network-pack handlers load from `<network_root>/bootstrap_handlers/` using `module` + class `handler`.

## Key changes

| Area | Change |
|------|--------|
| `bootstrap/config.py` | `BootstrapConfig`, `load_bootstrap_config()` — validates bootstrap block, rejects built-in key + `module` conflict |
| `bootstrap/handlers/resolve.py` | `BUILTIN_HANDLERS`, pack load via `sys.path` + `importlib`; `_OverrideHandler` removed |
| `network/create.py` | `_write_network_manifest` includes `bootstrap`; manifest written **before** seed bootstrap |
| `network/example.py` | Comment: `bootstrap_handlers/` intentionally copied (not in `_SKIP_NAMES`) |
| Example manifests | `crm`, `empty-crm`, `crm-metering`, `baseball` declare `"bootstrap": {"handler": "default_seed"}` |

## Schema

**Built-in (CRM):**
```json
"bootstrap": { "handler": "default_seed" }
```

**Network pack (stub-tested; baseball later):**
```json
"bootstrap": { "module": "bootstrap_handlers.lahman_seed", "handler": "LahmanSeedHandler" }
```

## Tests

Rewrote `tests/test_network_bootstrap.py` (12 smoke tests): CRM seed, missing seed, missing bootstrap block, unknown built-in, pack stub, pack import failure, guide probe via pack class, `copy_example_network` includes `bootstrap_handlers/`.

Updated `tests/test_network_create.py` — manifest includes `bootstrap` block.

Updated `tests/test_example_network.py` — fleet example includes bootstrap for refresh.

## Docs

- `docs/architecture.md` § Seed bootstrap
- `docs/full-code-walkthrough.md` §6
- `examples/networks/crm/README.md`
- `docs/plans/baseball-example-program.md` — one-line stale override removed

## Verification

```bash
./bin/ci-local
# CI local: all steps passed.
# 417 passed, 93 deselected
```

## For Grok + Paul

- Next: **multi-MVR entity stores**, then **LahmanSeedHandler** in `examples/networks/baseball/bootstrap_handlers/`.
- Specialist manifest loading can mirror this slice's `module` + class pattern.
- Suggested commit:

```
feat(network): bootstrap handler selection via network.json

Declare bootstrap.handler in network manifests; built-in registry for
default_seed; load network-pack handler classes from network_root.
Remove legacy bootstrap_specialist.py override path.
```

- Do **not** commit from this slice deliverable.
