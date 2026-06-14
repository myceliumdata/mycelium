# Review: 2026-06-14-0715-empty-crm-mvr-bootstrap-create-on-deliver

**Verdict: Approved**

## CI

| Step | Result |
|------|--------|
| `./bin/ci-local` (Grok, 2026-06-14) | **Fail** — `test_example_crm_layout`: `examples/networks/crm/entities.json` exists on disk (local junk, not in slice diff). **382 smoke passed** otherwise. |
| Cursor `output.md` claim | 383 passed (reviewer tree likely clean) |
| ruff | Pass |
| admin-ui build | Pass |

**Before commit:** delete untracked runtime junk under `examples/networks/crm/` (`entities.json`, `deliveries.json`) so `test_example_crm_layout` passes. Do not commit those files.

## Full integration (Grok, post-review)

```bash
LANGCHAIN_TRACING_V2=false uv run pytest -m full -q
```

**17 passed, 1 failed** — `test_create_network_query_uses_custom_ontology_not_crm_fallback` (extra `demographic`/`professional` categories after seed + MVR merge). Pre-existing / Program 2 interaction; not introduced by this slice. Track in capstone-tests slice.

## Delivery

| Artifact | Present |
|----------|---------|
| `src/agents/target_deliver.py` | ✅ |
| `tests/test_empty_crm_create_on_deliver.py` | ✅ |
| `examples/networks/empty-crm/README.md` | ✅ one-line note |
| `output.md` / `prompt.md` | ✅ |

Slice did not edit gate doc or `WORKFLOW.md` (those are separate uncommitted local edits).

## Diff reviewed

- `src/agents/target_deliver.py`
- `tests/test_empty_crm_create_on_deliver.py`
- `examples/networks/empty-crm/README.md`
- `prompt.md`, `output.md`

## Spec compliance

| Exit criterion | Pass |
|----------------|------|
| Step 2 create-on-deliver writes bind storage on no-seed network | ✅ |
| Idempotent / seeded CRM tests unchanged | ✅ (smoke) |
| Smoke test: categories without MVR → step 2 success | ✅ excellent negative fixture |
| `./bin/ci-local` green | ⚠️ blocked on local junk file only |
| README note | ✅ |

## Legacy / dual-path

Seeded path still uses `seed_import` MVR bootstrap; create-on-deliver now calls same helper at bind time. No duplicate merge logic.

## Tests

New test correctly uses `_SEED_CATEGORIES` **without** upfront `ensure_categories_for_mvr_bind` — reproduces the production gap this slice fixes.

## Design critique

**Strong:** Minimal fix at the right locus (`bind_provisional_from_scope`); reuses `ensure_categories_for_mvr_bind`; test mirrors Paul's failure mode.

**Sub-optimal (non-blocking):** Step-2 error still says "No valid delivery" when bind fails for other reasons (optional item skipped — fine).

## Nits

- None blocking. Optional follow-up: surface bind `ValueError` in `debug` on step 2 (deferred).

## For Paul

**Commit message:**

```
fix: bootstrap MVR category mappings on empty-crm create-on-deliver

Call ensure_categories_for_mvr_bind before provisional bind write so
no-seed networks merge name/employer into categories.json; add smoke
test and empty-crm README note.
```

**Before commit:** `rm examples/networks/crm/entities.json examples/networks/crm/deliveries.json` (if present).

**Next:** Capstone-tests slice queued (`2026-06-14-0800-example-network-capstone-tests-gate-pairing.md`). Re-run empty-crm two-step manually to confirm gate unblocked.

**Push:** Local only until program gate CLEAR.