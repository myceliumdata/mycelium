# Review: Bootstrap handler selection via `network.json`

**Verdict:** **Approved**  
**Reviewer:** Grok  
**Date:** 2026-06-17

---

## CI

| Suite | Result |
|-------|--------|
| `./bin/ci-local` | **417 passed**, 93 deselected; ruff clean; admin-ui build ok |

---

## Delivery

`output.md` matches working tree. New `src/network/bootstrap/config.py`; legacy override code removed from `resolve.py`. Example manifests updated; tests rewritten.

---

## Diff reviewed

Read in full:

- `src/network/bootstrap/config.py`
- `src/network/bootstrap/handlers/resolve.py`
- `src/network/create.py` (manifest + bootstrap order)
- `src/network/example.py`
- `examples/networks/crm/network.json`, `empty-crm/network.json`, `crm-metering/network.json`, `baseball/network.json`
- `tests/test_network_bootstrap.py`
- `tests/test_network_create.py`
- `tests/test_example_network.py`
- `docs/architecture.md`, `docs/full-code-walkthrough.md`, `docs/plans/baseball-example-program.md`
- `examples/networks/crm/README.md`

Grep: no remaining `bootstrap_specialist.py` resolution in `src/`.

---

## Spec compliance

| # | Criterion | Result |
|---|-----------|--------|
| E1 | Committed examples declare `bootstrap.handler: default_seed` | **Pass** |
| E2 | Legacy override removed | **Pass** |
| E3 | Pack handler stub test from `bootstrap_handlers/` | **Pass** |
| E4 | Missing/invalid config → clear `ValueError` | **Pass** |
| E5 | `network create` writes `bootstrap` | **Pass** |
| E6 | `copy_example_network` copies `bootstrap_handlers/` | **Pass** |
| E7 | Docs + pack pattern note | **Pass** |
| E8 | `./bin/ci-local` green | **Pass** |

Locked H1–H7: **Pass**. CRM seed behavior unchanged (15 entities, capstones via CI).

---

## Design critique

**Strong:**

- Clean cutover — manifest is sole selector; no file-presence magic.
- `BootstrapConfig` + `load_bootstrap_config` separate parsing from loading.
- Built-in registry (`BUILTIN_HANDLERS`) scales for future shipped handlers.
- Pack load scoped `sys.path` insert/remove; good error messages with expected file path.
- `network create` writes manifest **before** `bootstrap_seed_at_paths` — fixes ordering bug risk.
- Rejects built-in key + `module` conflict.

**Acceptable:**

- `bootstrap.handler` means registry key (built-in) or class name (pack when `module` set) — slightly overloaded but matches Paul’s agreed schema; docs explain it.

**Operational note (not a blocker):** Live `network_root` trees with old `network.json` (no `bootstrap` block) will fail on refresh until re-copied from examples or manifest patched. Intentional hard cutover.

---

## Nits

None blocking. Optional future doc: one-line schema table in `examples/networks/README` when that file exists.

---

## For Paul

**Commit message:**

```
feat(network): bootstrap handler selection via network.json

Declare bootstrap.handler in network manifests; built-in registry for
default_seed; load network-pack handler classes from network_root.
Remove legacy bootstrap_specialist.py override path.
```

**Next slice:** multi-MVR entity stores, then `LahmanSeedHandler` in `examples/networks/baseball/bootstrap_handlers/`.

**Push:** Local until you ask.