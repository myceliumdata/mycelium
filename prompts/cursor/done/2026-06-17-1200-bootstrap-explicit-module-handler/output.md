# Bootstrap handler — explicit `module` + `handler` only

## Summary

Removed built-in registry keys (`default_seed`, `BUILTIN_HANDLERS`). All networks now declare bootstrap via a single schema: **`bootstrap.module`** + **`bootstrap.handler`** (class name). Framework handlers use `network.*` module paths (imported from the installed package); pack handlers use modules under `<network_root>/bootstrap_handlers/`.

## Key changes

| Area | Change |
|------|--------|
| `bootstrap/config.py` | `BootstrapConfig` has only `module` + `class_name`; rejects handler-only manifests |
| `bootstrap/handlers/resolve.py` | `_load_framework_handler` vs `_load_pack_handler`; shared `_instantiate_handler`; no registry |
| `network/create.py` | Manifest writes explicit `DefaultSeedHandler` module path |
| Example manifests | `crm`, `empty-crm`, `crm-metering`, `baseball` updated |

## Schema (only valid shape)

```json
"bootstrap": {
  "module": "network.bootstrap.handlers.default_seed",
  "handler": "DefaultSeedHandler"
}
```

Pack handlers use the same keys with `bootstrap_handlers.*` modules.

## Tests

Updated `tests/test_network_bootstrap.py`: removed unknown built-in test; added missing `module`, missing `handler`, legacy handler-only rejection, framework load without `bootstrap_handlers/` dir. Updated `test_network_create.py` and `test_example_network.py` fixtures.

## Docs

- `docs/architecture.md` § Seed bootstrap
- `docs/full-code-walkthrough.md` §6
- `examples/networks/crm/README.md`
- `docs/plans/baseball-example-program.md`

## Verification

```bash
./bin/ci-local
# CI local: all steps passed.
# 420 passed, 93 deselected
```

## For Grok + Paul

- Next slice remains **multi-MVR entity stores**, then **LahmanSeedHandler** pack module in baseball example.
- Specialist manifest loading can mirror this `module` + class pattern.
- Suggested commit:

```
refactor(network): bootstrap manifest uses module and handler class only

Remove default_seed registry keys; CRM declares DefaultSeedHandler via
framework module path; pack handlers unchanged under network_root.
```

- Do **not** commit from this slice deliverable.
