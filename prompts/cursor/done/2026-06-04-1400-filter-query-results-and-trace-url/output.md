# Slice 1400 — Filter query results; specialist-first merge

## Claim

Moved from `prompts/cursor/next/`; implemented after 1300 review.

## Summary

- `shape_results`, `merge_requested_record`, `message_for_assembled`, `response_assembled` in `responses.py`.
- `assemble_response_node` merges specialist values over seed, filters to requested attributes, honest messaging (provisional seed vs unavailable).
- Smoke tests in `tests/test_result_shape.py`; `test_core_graph` non-core assertion updated (no `name`/`employer` when not requested).
- `docs/architecture.md` and `PersonResponse` description updated.

## Before / after (Nichanan, `--attributes name`)

**Before:** `id`, `name`, `employer`, duplicate `person_id`; message said name unavailable while name present.

**After:**

```json
{
  "results": [{"id": "b08b24db-6231-5ad8-aca1-81a09d052460", "name": "Nichanan Kesonpat"}],
  "message": "Found record for Nichanan Kesonpat. name shown from seed; specialist verification in progress (via contact_specialist)."
}
```

## Verification

```text
uv run ruff check src tests  # pass
uv run pytest -m smoke -q    # 27 passed
uv run pytest -m full -q -k "query_existing_person or query_missing_person or query_non_core_attributes"  # 3 passed
```

LangSmith URL remains CLI-only (out of scope).