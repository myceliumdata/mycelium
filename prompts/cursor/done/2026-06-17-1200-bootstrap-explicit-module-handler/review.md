# Review: Bootstrap explicit `module` + `handler` only

**Verdict:** **Approved**  
**Reviewer:** Grok  
**Date:** 2026-06-17

---

## CI

| Suite | Result |
|-------|--------|
| `./bin/ci-local` | **420 passed**, 93 deselected; ruff clean; admin-ui build ok |

---

## Delivery

`output.md` matches working tree. Registry key code removed; single-schema parser and dual load roots implemented.

---

## Diff reviewed

Read in full:

- `src/network/bootstrap/config.py`
- `src/network/bootstrap/handlers/resolve.py`
- `src/network/create.py`
- `examples/networks/crm/network.json`, `empty-crm`, `crm-metering`, `baseball`
- `tests/test_network_bootstrap.py`
- `tests/test_network_create.py`
- `tests/test_example_network.py`
- `docs/architecture.md`, `docs/full-code-walkthrough.md`, `examples/networks/crm/README.md`

Grep `src/`: no `BUILTIN_HANDLER`, `builtin_key`, or registry-key resolution.

---

## Spec compliance

| # | Criterion | Result |
|---|-----------|--------|
| E1 | No registry key code | **Pass** |
| E2 | All examples use `module` + `handler` | **Pass** |
| E3 | CRM behavior unchanged | **Pass** (15 entities; framework handler test) |
| E4 | Pack handler tests pass | **Pass** |
| E5 | Legacy handler-only rejected | **Pass** |
| E6 | Docs updated | **Pass** |
| E7 | `./bin/ci-local` green | **Pass** |

Locked N1–N6: **Pass**.

---

## Design critique

**Strong:**

- One manifest shape — addresses Paul’s “`default_seed` is magic” concern.
- `network.*` vs pack split is simple and documented.
- Shared `_instantiate_handler` avoids duplicated protocol checks.
- Explicit tests for missing module/handler and legacy `"handler": "default_seed"`.
- `test_framework_handler_does_not_require_network_root_module` proves CRM path doesn’t need pack files.

**Minor (non-blocking):** `BootstrapResult.handler_id` still returns `"default_seed"` from `DefaultSeedHandler` — internal run label, not manifest config. Could rename to `DefaultSeedHandler` later for consistency.

---

## Nits

None blocking.

---

## For Paul

**Commit message:**

```
refactor(network): bootstrap manifest uses module and handler class only

Remove default_seed registry keys; CRM declares DefaultSeedHandler via
framework module path; pack handlers unchanged under network_root.
```

**Next:** multi-MVR entity stores, then `LahmanSeedHandler` in baseball `bootstrap_handlers/`.

**Note:** Live roots with old `"handler": "default_seed"` manifests need one-line update to explicit module + class (or re-run refresh from updated examples).