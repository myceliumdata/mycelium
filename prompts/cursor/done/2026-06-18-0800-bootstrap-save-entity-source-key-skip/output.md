# Output — bootstrap perf: skip source-key rebuild on bind-only `save_entity`

## Summary

Lahman bootstrap calls `save_entity` (~24k×) before `set_source_keys`. Each bind-only save was running a full `_rebuild_source_key_index()` scan even though `source_keys` are empty until the follow-up `set_source_keys` call (already incremental per `c96c5e2`). `save_entity` now skips source-key rebuild; field-index rebuild unchanged. `add_field_alias` parity: skip source-key rebuild only.

**Recovery note:** Prior delivery claimed completion without saving code (Grok review Not Approved). Re-implemented on clean `main` with 0900 work stashed (`0900-polish-wip`).

## Changes (0800 scope only)

| File | Change |
|------|--------|
| `src/agents/entity_registry.py` | `save_entity` → `_save(rebuild_source_key_index=False)` + docstring; `add_field_alias` same skip |
| `tests/test_entity_store_evolution.py` | `test_save_entity_skips_source_key_index_rebuild` |
| `docs/manual-checks/2026-06-17-storage-evolution-timing-gates.md` | Test **8c** stub row (*pending Paul re-run*) |

## Correctness notes (O3/O4)

- **Deferred bootstrap:** `set_source_keys` still updates `source_key_index` incrementally after each bind save; `commit_deferred_save` still runs one full rebuild at grain flush.
- **Non-deferred `write_bind_fields`:** bind-only `save_entity` does not change `entity.source_keys`; existing index entries remain valid on disk.

## Exit criteria

| # | Status |
|---|--------|
| E1 | `save_entity` skips source-key rebuild; field-index rebuild unchanged |
| E2 | `test_save_entity_skips_source_key_index_rebuild` |
| E3 | `./bin/ci-local` green — see verification below |
| E4 | Test 8c row stubbed in timing-gates doc |
| E5 | Paul manual gate command below |

## Verification

```bash
git diff --stat  # only entity_registry.py, test_entity_store_evolution.py, timing-gates doc
./bin/ci-local   # green
```

## Paul manual gate (Test 8c)

```bash
/usr/bin/time -p ./bin/refresh-example-network baseball \
  --root /tmp/mycelium-baseball-benchmark --yes --no-default
```

Expect **~555 s real** (test 7 ballpark). Record results in timing-gates doc Test 8c row.

## For Grok + Paul

- **0900 polish** stashed separately — do not commit with this slice.
- Duplicate `prompts/cursor/next/2026-06-18-0800-…` removed.
- No commit (per workflow).

**Suggested commit message:**

```
perf(bootstrap): skip source-key rebuild on bind-only save_entity

Lahman bootstrap calls save_entity before set_source_keys; each call
was scanning all entities for source_key_index. Mirrors c96c5e2 fast
path; expect test 7 ballpark (~9 min) on Test 8c.
```
