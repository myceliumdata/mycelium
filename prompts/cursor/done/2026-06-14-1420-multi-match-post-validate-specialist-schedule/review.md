# Review: 2026-06-14-1420-multi-match-post-validate-specialist-schedule

**Verdict: Approved**

## CI

| Step | Result |
|------|--------|
| `./bin/ci-local` (Grok, 2026-06-14) | **Pass** — 408 smoke passed, 26 deselected; ruff clean; admin-ui build ok |
| Cursor `output.md` claim | 408 passed — matches |

## Delivery

| Artifact | Present |
|----------|---------|
| Post-validate specialist schedule generalized beyond `len(matched) == 1` | ✅ |
| `planner_context` with all entity ids for multi-match | ✅ |
| `current_id` set only for single-match (batch uses `_meta.ids`) | ✅ |
| Extended `test_multi_match_step2_promotes_provisional_bind` | ✅ |
| `prompt.md` / `output.md` | ✅ |

## Diff reviewed

- `src/agents/dispatch.py`
- `tests/test_mvr_create_on_deliver.py`
- `prompt.md`, `output.md`

## Spec compliance

| Exit criterion | Pass |
|----------------|------|
| Multi-match promote + attrs research same turn when gate opens | ✅ |
| Gated multi-match (provisional remains) still skips invoke | ✅ (CI — `test_multi_match_research_gate_returns_all_identity_rows`) |
| M8 / single-match paths unchanged | ✅ (CI) |
| `./bin/ci-local` green | ✅ |

## Legacy / dual-path

| Check | Pass |
|-------|------|
| `validate_entity` early return when no provisional processed | ✅ (supervisor-only schedule unchanged) |
| `not any_failed` guard preserves gate-closed batches | ✅ |
| Single-match Q5b failure early return | ✅ |

## Tests

| Test | Coverage |
|------|----------|
| `test_multi_match_step2_promotes_provisional_bind` | Promote + `assembled` + `email` on all rows + `len(calls) >= 2` |
| Gap | None material |

## Design critique

**Strong:** Minimal, correct generalization — removed the `len(matched) == 1` guard, kept `not any_failed` + `research_gate_allows`, and aligned `planner_context` with supervisor’s multi-match shape (`matched` list + all `ids`). Early return when no provisional rows prevents double-scheduling when supervisor already planned specialists. Closes 1400 nit N1 cleanly.

## Nits

None.

## For Paul

**Commit message:**

```
fix(query): schedule specialists after multi-match batch validation

Re-invoke attribute specialists in the same turn when validate_entity
promotes the last provisional row and the research gate opens.
```

**Manual test:**

1. Demote Andrea @ Wrong Corp to `provisional` in `entities.json`
2. Step 1: `{"name":"Andrea Kalmans"}` + `--attributes email`
3. Step 2: deliver **once**
4. Expect: Wrong Corp `validated`, `assembled`, both rows have `email` in `results` (API keys in `.env`)

**Next:** Program 2 manual gate when ready.

**Git:** Local commit only — no push until you ask.