# Review — Example network capstone tests + gate pairing

**Verdict: Approved**

## CI

| Step | Result |
|------|--------|
| `./bin/ci-local` | Pass — ruff clean, admin-ui build ok, **390 smoke** passed, 26 deselected |
| `pytest -m full` | Pass — **18 full** passed, 398 deselected |

## Delivery

`output.md` matches on-disk changes. New files: `tests/test_example_network_capstones.py`, `tests/test_program2_bootstrap_matrix.py`. Docs/helpers/network_create updates present.

**Note:** `output.md` claims `.gitignore` adds `deliveries.json` under example networks — stale. Example-tree hygiene was committed separately (`dae582b`) with the **no-gitignore** policy Paul specified; capstone README line is correct.

## Diff reviewed

| File | Read |
|------|------|
| `tests/test_example_network_capstones.py` | Full |
| `tests/test_program2_bootstrap_matrix.py` | Full |
| `docs/manual-checks/2026-06-13-program2-post-program-gate.md` | Full diff |
| `prompts/cursor/WORKFLOW.md` | Full diff |
| `tests/network_helpers.py` | Full diff |
| `tests/test_network_create.py` | Full diff |

`/review` subagent: not used (diff size moderate; full read sufficient).

## Spec compliance

| Exit criterion | Result |
|----------------|--------|
| Capstone smoke tests for `crm` and `empty-crm` refresh+query | Pass |
| Path matrix A–D in smoke CI | Pass |
| WORKFLOW negative-fixture rule | Pass |
| Gate doc required checks cite automated test names | Pass |
| `./bin/ci-local` green | Pass |
| `pytest -m full` recorded / network_create fix if needed | Pass |

## Legacy / dual-path

Unchanged production behavior. `test_create_network_query_uses_custom_ontology_not_crm_fallback` correctly reflects Program 2 MVR merge on seed bootstrap (custom `telemetry`/`maintenance` preserved; `demographic`/`professional` merged).

## Tests

Strong regression guard:

- **crm capstone** — refresh only, no `ensure_categories_for_mvr_bind`; asserts 15 entities + `seed_bootstrap` specialist versions.
- **empty-crm capstone** — refresh → step 1/2 `run_query`; no pre-seeded MVR mappings; `actor.kind == bind`.
- **Matrix C/D** — Road Runner create-on-deliver and duplicate-bind guard align with manual gate checks 4 and 6.

**Overlap (acceptable):** matrix A duplicates crm capstone assertions; matrix B overlaps empty-crm capstone. Prompt asked for both capstones and matrix — intentional pairing with gate doc.

**Gap (non-blocking):** capstone tests do not assert `network status` CLI output (check 0b manual contrast is disk/query-level only). Adequate for smoke CI.

## Design critique

**Strong**

- Shared helpers (`apply_refreshed_root`, `run_create_on_deliver`, `assert_crm_seed_capstone`) keep matrix tests readable.
- Negative-fixture discipline matches `test_empty_crm_create_on_deliver.py`.
- Gate doc **Automated:** lines give Paul a clear manual ↔ CI map.

**Sub-optimal (non-blocking)**

- Matrix module imports helpers from `test_example_network_capstones` — works under pytest but helpers would be cleaner in `tests/network_helpers.py` long-term.
- `output.md` gitignore claim contradicts committed policy (doc-only nit).

## Nits

| # | Severity | Item |
|---|----------|------|
| 1 | Non-blocking | Move capstone helpers to `network_helpers.py` in a future polish slice if matrix/capstone files grow. |
| 2 | Non-blocking | Correct `output.md` gitignore bullet if that folder is ever re-opened (policy is tests-enforced, not gitignored). |

Program polish backlog: none required for MVR M10 from this slice.

## For Paul

- **Commit:** `test: add example network capstones and Program 2 gate pairing` (Grok committing now).
- **Related:** Example-tree policy already committed as `dae582b` (separate commit).
- **Manual gate:** Re-run [`docs/manual-checks/2026-06-13-program2-post-program-gate.md`](../../../../docs/manual-checks/2026-06-13-program2-post-program-gate.md) — especially **Check 0b** and empty-crm two-step after MVR bootstrap fix.
- **Push:** Local only until you ask; branch is ahead of `origin/main`.
- **Next:** Program 3 entity-protocol legacy cleanup per HOLD.md.