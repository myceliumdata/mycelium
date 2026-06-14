# Example network capstone tests + gate ↔ CI pairing

> **READY** — Move to `in-progress/` before starting (see `prompts/cursor/WORKFLOW.md`).

**Context:** Regression gaps (empty-crm create-on-deliver, seed refresh specialist storage) slipped past smoke CI because fixtures pre-wired MVR mappings and example networks lacked end-to-end `refresh → query` capstones. Paul + Grok want suggestions **1–4** implemented. **CI stays smoke-only** (`./bin/ci-local`); Grok runs `pytest -m full` after approving a program’s final slice (documented in WORKFLOW §4).

**Prerequisite:** [`2026-06-14-0715-empty-crm-mvr-bootstrap-create-on-deliver`](../done/2026-06-14-0715-empty-crm-mvr-bootstrap-create-on-deliver/) approved (fix in `target_deliver.py` + `tests/test_empty_crm_create_on_deliver.py`).

---

## Read first

- `prompts/cursor/WORKFLOW.md` — Test Execution Policy; add negative-fixture rule here
- `docs/manual-checks/2026-06-13-program2-post-program-gate.md` — gate checks to pair
- `tests/test_example_network.py` — refresh tests (extend, do not duplicate blindly)
- `tests/test_empty_crm_create_on_deliver.py` — negative-fixture pattern to follow
- `tests/test_mvr_create_on_deliver.py` — Road Runner / duplicate-bind coverage
- `tests/network_helpers.py` — helpers that call `ensure_categories_for_mvr_bind` (document when appropriate)
- `examples/networks/crm/README.md`, `examples/networks/empty-crm/README.md`

---

## Objective

1. **Capstone smoke test per committed example** (`crm`, `empty-crm`): `refresh_example_network` → assert production-shaped outcomes (and query flow for empty-crm).
2. **Path matrix** (smoke): four cells covering seed vs create-on-deliver × storage assertions.
3. **Negative-fixture rule** in `WORKFLOW.md` so integration tests cannot pre-apply bootstrap helpers the code path under test does not call.
4. **Gate ↔ automated pairing** in Program 2 manual gate doc: each required check cites a smoke test name.

**Do not** change `./bin/ci-local` or GitHub CI to run `full` tests.

---

## Implement

### 1 — Capstone tests (`tests/test_example_network.py` or `tests/test_example_network_capstones.py`)

Prefer one focused new file if `test_example_network.py` is already large.

#### `crm` capstone (smoke)

After `refresh_example_network("crm", root=tmp, register=False, yes=True)`:

- `entities.json`: 15 entities
- `agents/demographic/storage.json` + `agents/professional/storage.json`: 15 records each
- First name version `actor.kind` == `seed_bootstrap`
- **Do not** call `ensure_categories_for_mvr_bind` in test setup — refresh must do the right thing

Name suggestion: `test_crm_refresh_capstone_seed_specialist_storage`

#### `empty-crm` capstone (smoke)

After `refresh_example_network("empty-crm", root=tmp, register=False, yes=True)`:

- No seed import; no pre-existing specialist storage
- Step 1 `run_query` full MVR lookup → `lookup_resolved`, `create_on_deliver`
- Step 2 `run_query` with `delivery_id` → `found`, 1 result
- Demographic + professional storage: 1 record each; `actor.kind` == `bind`

**Do not** pre-seed `categories.json` with MVR mappings or call `ensure_categories_for_mvr_bind` in fixture — let step 1 create classification seed without MVR (same pattern as `test_empty_crm_create_on_deliver.py`). May consolidate/reuse fixture helper to avoid duplication.

Name suggestion: `test_empty_crm_refresh_capstone_create_on_deliver_storage`

Use `MYCELIUM_USE_SYNC_CHECKPOINTER=1` and existing reset patterns from `tests/test_network_integration.py`.

### 2 — Path matrix (smoke, same file or `tests/test_program2_bootstrap_matrix.py`)

Four tests (can share helpers; keep each test readable):

| # | Setup | Action | Assert |
|---|--------|--------|--------|
| A | refresh `crm` | — | 15 entities; demo+prof storage 15; `seed_bootstrap` |
| B | refresh `empty-crm` | step 1 + 2 | 1 entity; demo+prof storage 1; `bind` |
| C | refresh `crm` | Road Runner create-on-deliver (Check 4) | new UUID; bind versions in storage |
| D | refresh `crm` | repeat Road Runner bind | name version count still 1 (Check 6 / polish P3) |

Reuse lookup `{"name":"Road Runner","employer":"Acme Corp"}` for C/D.

### 3 — Negative-fixture rule (`prompts/cursor/WORKFLOW.md`)

Under **Test Execution Policy**, add a short **Negative fixtures** subsection:

- Integration tests for a **production code path** must not call bootstrap helpers that path does not call (e.g. no `ensure_categories_for_mvr_bind` in fixtures for empty-crm create-on-deliver unless the test is explicitly for the seed-import path).
- Prefer disk state that mirrors post-step-1 reality (`_SEED_CATEGORIES` without MVR keys) over `sample-categories.json` when testing cold-start gaps.
- When a helper in `tests/network_helpers.py` applies bootstrap, document in its docstring which paths it simulates.

### 4 — Gate ↔ CI pairing (`docs/manual-checks/2026-06-13-program2-post-program-gate.md`)

For each **required** check below, add one line after **Pass** (or **Pass criteria**):

`**Automated:** \`test_name\`` (pytest smoke; runs in `./bin/ci-local`).

| Gate check | Pair to (create or cite existing test) |
|------------|----------------------------------------|
| 0 — Clean deploy | `test_crm_refresh_capstone_*` or refresh import test |
| 0b — Seed vs empty | capstone A + B (or dedicated contrast test) |
| 1 — Status bind versions | existing status/introspection test or minimal new smoke |
| 4 — Road Runner create-on-deliver | matrix C |
| 6 — No duplicate bind | matrix D |
| 7 — Seed refresh idempotency | `test_refresh_crm_imports_seed_into_entities` (existing) + capstone A |

Checks 2, 3, 5, 8–10 may stay manual-only — note `Automated: manual` or omit.

### 5 — Example tree hygiene (small)

`test_example_crm_layout` fails when `examples/networks/crm/entities.json` exists locally. Add a one-line comment in `tests/test_example_network.py` or `examples/networks/crm/README.md`: runtime artifacts must not live in the committed example tree. Optionally add `examples/networks/crm/entities.json` and `deliveries.json` to `.gitignore` if not already ignored.

### 6 — Full-test failure (if still failing after capstones)

`tests/test_network_create.py::test_create_network_query_uses_custom_ontology_not_crm_fallback` may fail because seed bootstrap merges MVR categories (`demographic`, `professional`) into custom ontologies. **Update test expectations** to match Program 2 policy (MVR merge on seed path is intentional), or assert MVR keys are present alongside custom categories. Run `pytest -m full -q` and document result in `output.md` — Grok uses this after program approval; fix if red.

---

## Scope boundaries (strict)

**May modify:**

- `tests/test_example_network.py` and/or new `tests/test_example_network_capstones.py` / `tests/test_program2_bootstrap_matrix.py`
- `tests/test_network_create.py` (expectation fix only, if needed for full suite)
- `prompts/cursor/WORKFLOW.md` (Test Execution Policy — negative fixtures + reference to Grok full run)
- `docs/manual-checks/2026-06-13-program2-post-program-gate.md` (Automated: lines only)
- `examples/networks/crm/README.md` or `.gitignore` (hygiene note only)

**Out of scope:**

- `TODO.md`
- Changing `./bin/ci-local` or `.github/workflows/ci.yml` to run `full` tests
- Production code changes unless a test reveals a real bug — then stop and document in `output.md`
- Program 3 / operator UI

---

## Verification

```bash
./bin/ci-local
LANGCHAIN_TRACING_V2=false uv run pytest -m full -q   # document pass/fail in output.md
```

---

## Governance (mandatory)

- **Do not edit `TODO.md`.**
- In `output.md`, **For Grok + Paul**: list new test names for gate table; note full-suite count.
- Do not commit or push.

## When finished (mandatory — see WORKFLOW.md §3)

1. `./bin/ci-local` green
2. `prompts/cursor/done/2026-06-14-0800-example-network-capstone-tests-gate-pairing/`
3. Remove claimed file from `in-progress/` and `next/`
4. Tell Paul **slice ready for review**

---

## Exit criteria

- Capstone smoke tests for `crm` refresh and `empty-crm` refresh+query
- Path matrix A–D in smoke CI
- WORKFLOW negative-fixture rule documented
- Gate doc required checks cite automated test names
- `./bin/ci-local` green
- `pytest -m full` result recorded in `output.md` (fix network_create test if needed)