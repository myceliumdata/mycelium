# Program 3 — Slice 1510: MVR helper legacy removal (item 5)

## Summary

Removed legacy MVR helpers that treated non-empty `entity_key` as satisfying `name`. **`missing_mvr_bind_fields(lookup)`** is now the single completeness rule.

## Removed from `MvrPolicy` / `mvr.py`

- `required_bind_fields(entity_key, binding)`
- `required_fields_for_entity_key(entity_key)`
- `allowed_binding_keys()`
- `normalize_binding()`

## Added

- **`legacy_entity_lookup_map(entity_key, binding)`** — builds target-style lookup from legacy `EntityQuery` fields until slice 1530 removes the legacy graph

## Caller updates

| File | Change |
|------|--------|
| `src/agents/entity_resolution.py` | `missing_mvr_bind_fields(legacy_entity_lookup_map(...))` |
| `src/agents/responses.py` | `response_entity_unknown` uses lookup map + `missing_mvr_bind_fields` |
| `tests/test_entity_unknown_mvr.py` | New MVR bind-field tests; removed deleted-method assertions |

## Verification

```bash
./bin/ci-local
# CI local: all steps passed.
# 424 passed, 26 deselected
```

## For Grok + Paul

- One MVR rule: **`missing_mvr_bind_fields(lookup)`** only — no entity_key-satisfies-name shortcut.
- Update [`docs/plans/entity-protocol-legacy-cleanup-program.md`](../../docs/plans/entity-protocol-legacy-cleanup-program.md) slice 1510 status after review.
- **Not committed** — awaiting review.

Suggested commit message:

```
refactor(mvr): drop entity_key satisfaction from bind field helpers
```
