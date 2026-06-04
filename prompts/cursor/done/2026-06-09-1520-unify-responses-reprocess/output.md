# Reprocess: Slice 1520 — unify-responses

**Claimed:** 2026-06-09 — moved to `prompts/cursor/in-progress/2026-06-09-1520-unify-responses-reprocess/prompt.md` before implementation.

## Summary

Unified `PersonResponse` builders for the seed-data-context redesign:

- **`_build_identity_results`** — accepts `base_records` (seed/specialist dicts) or `persons` list
- **`response_found` / `response_non_core`** — optional `base_records`; plural-aware messages
- **Messages** — no “core record” wording:
  - `Found record for {name}.` / `Found {n} records for …`
  - `No record found for … This lookup did not match anyone.`
  - `Found record for {name}. We're still researching {attrs} (via {specialist}).`
- **`core_data.py`** — unchanged call sites (still passes `matches` + `deferred`; compatible signatures)
- **Tests** — `test_core_graph.py`, `test_supervisor_routing.py`, `test_core_data_agent.py` assert new strings (and `core record` absent)

No `review.md` (per prompt — Grok reviews after delivery).

## Verification

```text
$ uv run pytest -m smoke -q
28 passed, 9 deselected in 0.90s

$ uv run pytest -m full -q -k "query_existing_person or query_missing_person or query_non_core_attributes"
3 passed, 34 deselected in 0.13s

$ uv run ruff check src/agents/responses.py src/agents/core_data.py tests/test_core_graph.py tests/test_supervisor_routing.py tests/test_core_data_agent.py
All checks passed!
```

## git diff --stat

```
 src/agents/responses.py           | unified builders + base_records
 tests/test_core_graph.py         | message asserts
 tests/test_supervisor_routing.py | message asserts
 tests/test_core_data_agent.py    | message asserts
```

## Scope confirmation

Responses + test string updates only. No supervisor/graph/eliminate-core changes.

**Ready for next slice:** `2026-06-09-1530-eliminate-core-reprocess.md`
