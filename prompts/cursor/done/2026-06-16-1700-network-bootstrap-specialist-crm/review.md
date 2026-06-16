# Review: Network bootstrap specialist — CRM seed path

**Verdict:** **Approved + polish nits**  
**Reviewer:** Grok  
**Date:** 2026-06-16

---

## CI

| Suite | Result |
|-------|--------|
| `./bin/ci-local` | **413 passed**, 92 deselected; ruff clean; admin-ui build ok |

---

## Delivery

`output.md` matches working tree. All planned modules exist:

- `src/network/bootstrap/` (`run.py`, `context.py`, `handlers/default_seed.py`, `handlers/resolve.py`, `handlers/protocol.py`)
- `tests/test_network_bootstrap.py` (8 smoke tests)
- `docs/architecture.md`, `examples/networks/crm/README.md`, `src/network/seed_import.py`, `tests/network_helpers.py`

No missing implementation.

---

## Diff reviewed

Read in full:

- `src/network/bootstrap/run.py`
- `src/network/bootstrap/context.py`
- `src/network/bootstrap/handlers/default_seed.py`
- `src/network/bootstrap/handlers/resolve.py`
- `src/network/bootstrap/handlers/protocol.py`
- `src/network/bootstrap/__init__.py`
- `src/network/seed_import.py`
- `tests/test_network_bootstrap.py`
- `tests/network_helpers.py`
- `docs/architecture.md` (§ Seed bootstrap)
- `examples/networks/crm/README.md`

---

## Spec compliance

| # | Criterion | Result |
|---|-----------|--------|
| E1 | `run_network_bootstrap` sole orchestration path for refresh/create bootstrap | **Pass** — `bootstrap_seed_at_paths` delegates |
| E2 | CRM refresh/create behavior unchanged | **Pass** — capstone/matrix covered by CI |
| E3 | `empty-crm` still 0 entities | **Pass** (existing suite) |
| E4 | Override hook + test | **Pass** — `specialists/bootstrap_specialist.py` + `test_bootstrap_override_hook` |
| E5 | `docs/architecture.md` updated | **Pass** |
| E6 | `./bin/ci-local` green | **Pass** |
| E7 | `output.md` For Grok + Paul | **Pass** |

Locked decisions B1–B7: **Pass**. Wipe + refresh semantics unchanged. No baseball/LLM/query-graph scope creep.

---

## Legacy / dual-path

- `import_seed_file` / `import_seed_rows` preserved for tests; same validation and `ensure_bound_entity` semantics.
- `import_seed_for_test` still simulates categories + import (not full `run_network_bootstrap`) — documented in helper docstring; acceptable for query-path tests.
- `dispatch_bootstrap_entity` remains unused; default handler uses existing `ensure_bound_entity` → bind dispatch — allowed by prompt.

---

## Tests

New `test_network_bootstrap.py` covers CRM count, missing seed, invalid JSON, missing employer, idempotency, wrapper delegation, override hook. Regression anchor (Program 2 matrix, `test_import_seed_writes_specialist_versions`, network create) green via CI.

**Minor gap (non-blocking):** no test that broken override *import* raises the documented `ValueError` with path hint.

---

## Design critique

**Strong:**

- Self-contained `src/network/bootstrap/` — exactly the extension point Paul asked for before baseball.
- Clean orchestration: paths → categories → registry reset → handler.
- `BootstrapHandler` protocol + override loader are minimal and readable.
- `seed_import.py` shrunk to stable re-exports without behavior drift.

**Acceptable limits:**

- `guide_text` is loaded into `BootstrapContext` but unused by `DefaultSeedHandler` — correct for CRM slice; baseball handler will consume it.
- Override replaces default entirely (no chaining) — matches design.

---

## Nits (polish backlog)

| ID | Nit | Severity |
|----|-----|------------|
| N1 | Duplicate idempotency coverage: `test_network_bootstrap.test_import_seed_file_idempotent` and `test_example_network.test_import_seed_file_idempotent` | Low — dedupe in a future test hygiene pass |
| N2 | Add smoke test for override import failure message (`Cannot import bootstrap override at …`) | Low |
| N3 | Optional: assert `ctx.guide_text` is populated when `guide.md` exists (documents B6 wiring) | Low |

None block commit.

---

## For Paul

**Commit message:**

```
feat(network): formal bootstrap phase with CRM default seed handler

Introduce run_network_bootstrap() and relocate seed import into
src/network/bootstrap/. bootstrap_seed_at_paths delegates to the new
entry point; optional network override hook for future baseball cold start.
```

**Next:** Queue baseball bootstrap handler slice extending `network/bootstrap/handlers/` (warehouse source, multi-grain when ready). Grok can update `docs/plans/baseball-example-program.md` slice map on doc pass.

**Push:** Local only until Paul asks.