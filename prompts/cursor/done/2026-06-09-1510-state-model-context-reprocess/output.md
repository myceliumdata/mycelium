# Reprocess: Slice 1510 — state-model-context

**Claimed:** `prompts/cursor/in-progress/2026-06-09-1510-state-model-context-reprocess/prompt.md`

## Summary

Added seed-data-context internal state bags to `MyceliumGraphState` (backward compatible via defaults):

- `matched_persons` — enriched seed records with `person_id`
- `context` — supervisor-built union (`seed` + `specialists`)
- `current_person_id` — stable UUID for specialist invocation
- `target_fields` — owned attributes for the active specialist

Docstrings on the class and fields; TODO for future peer context retrieval.

## Verification

```text
$ uv run python -c "from models.state import MyceliumGraphState, PersonQuery; ..."
defaults ok

$ uv run pytest -m smoke -q
28 passed, 9 deselected in 0.47s

$ uv run pytest -m full -q -k "query_existing_person or query_missing_person or query_non_core_attributes"
3 passed, 34 deselected in 0.13s

$ uv run ruff check src/models/state.py
All checks passed!
```

## git diff --stat

```
 src/models/state.py | ~35 lines added (four fields + docstrings + TODO)
```

## Scope confirmation

State model only — no supervisor population, context builder, or graph routing (later reprocess slices).

**Ready for next slice:** `2026-06-09-1520-unify-responses-reprocess.md`
