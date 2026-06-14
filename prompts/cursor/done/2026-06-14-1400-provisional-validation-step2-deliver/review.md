# Review: 2026-06-14-1400-provisional-validation-step2-deliver

**Verdict: Approved + polish nits**

## CI

| Step | Result |
|------|--------|
| `./bin/ci-local` (Grok, 2026-06-14) | **Pass** — 407 smoke passed, 26 deselected; ruff clean; admin-ui build ok |
| Cursor `output.md` claim | 407 passed — matches |

## Delivery

| Artifact | Present |
|----------|---------|
| Identity-only step-2 routes through validation when any provisional | ✅ |
| Multi-match per-row validation loop | ✅ |
| Q5b single-match failure preserved | ✅ |
| `test_full_mvr_zero_matches_without_attrs_create_on_deliver` asserts `validated` | ✅ |
| `test_multi_match_step2_promotes_provisional_bind` | ✅ |
| CRM README step-2 validation note | ✅ |
| `prompt.md` / `output.md` | ✅ |

## Diff reviewed

- `src/agents/dispatch.py`
- `tests/test_mvr_create_on_deliver.py`
- `examples/networks/crm/README.md`
- `prompt.md`, `output.md`

## Spec compliance

| Exit criterion | Pass |
|----------------|------|
| Identity-only step-2 create-on-deliver promotes valid MVR | ✅ |
| Multi-match step-2 promotes each valid provisional row | ✅ |
| Q5b failure path unchanged | ✅ |
| `./bin/ci-local` green | ✅ |
| Slice `1410` out of scope | ✅ |

## Legacy / dual-path

| Check | Pass |
|-------|------|
| `test_batch_step2_identity_only_found` (all-validated preset `found`) | ✅ |
| `test_absurd_employer_fails_validation_stays_provisional` | ✅ (CI) |
| Delivery step-2 skips `entity_validated` outcome | ✅ (`entity_query_is_delivery_step` guard) |

## Tests

| Test | Coverage |
|------|----------|
| `test_multi_match_step2_promotes_provisional_bind` | Wrong Corp repro — core slice proof |
| Gap | No test for multi-match batch where **one** row fails validation and another promotes (batch policy documented in `output.md` only) |

## Design critique

**Strong:** Targeted Q5a fix — identity-only deliver with provisional rows no longer presets `response`; `validate_entity_node` loops all matches with independent promote/fail; single-match Q5b failure path unchanged; delivery step avoids misleading `entity_validated` on step 2.

**Nit (non-blocking):** Graph order is still `supervisor` → `validate_entity`. On multi-match deliver with attrs, supervisor may leave `specialists_to_invoke` empty when any row is still provisional **before** validation runs. After promotion in the same turn, `invoke_specialists` sees an open gate but an empty invoke list — attrs may not research until a follow-up query. Slice test asserts `validation_state` and `assembled` outcome, not per-row email population for both Andreas. Acceptable for this slice; consider re-scheduling specialists post-batch-validate if same-turn multi-match research matters.

## Nits

| # | Nit | Severity |
|---|-----|----------|
| N1 | Multi-match same-turn specialist scheduling after batch validate | Polish |
| N2 | `test_mvr_create_on_deliver` uses `Path(__import__("os").environ[...])` — slightly awkward | Polish |

## For Paul

**Commit message:**

```
fix(query): run validate_entity on step-2 deliver for provisional rows

Route identity-only deliver through validation; validate each provisional
match in multi-match scopes (Q5a). Identity-only create-on-deliver promotes.
```

**Manual test (before `1410`):**

1. On live CRM, confirm Andrea @ Wrong Corp is `provisional` in `entities.json` (or create via `confirm_new_entity` + identity-only step 2 on old build).
2. After deploy/restart MCP with this commit: single-match `{"name":"Andrea Kalmans","employer":"Wrong Corp"}` + attrs step 1 → step 2 deliver, **or** identity-only create path.
3. Confirm `validation_state: validated` for Wrong Corp; MCP single-row fetch should not show research-gate message.

**Next:** Queue active → slice **`1410`** multi-match truncation (after your manual OK).

**Git:** Local commit only — no push until you ask.