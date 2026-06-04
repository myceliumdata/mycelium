# Slice 1550 — supervisor-context-graph (reprocess)

## Claim

Moved `prompts/cursor/next/2026-06-09-1550-supervisor-context-graph-reprocess.md` → `prompts/cursor/in-progress/.../prompt.md`, then delivered here.

## Summary

Multi-node graph for seed-data-context: supervisor plans all required specialists; `build_context` pulls union storage; `invoke_specialists` runs each with full context; `assemble_response` merges contributions.

### New: `src/agents/context.py`
- `ContextBuilder.build_full_context(person_ids)` — seed + all generated specialist stores by `person_id`
- TODO for future peer retrieval

### `supervisor.py`
- Plans **all** specialists via `_collect_specialists_to_invoke`
- Stores plan in `context._meta.specialists_to_invoke`; always `route=None`
- No final `PersonResponse` here

### `dispatch.py`
- `build_context_node`, `invoke_specialists_node`, `assemble_response_node`
- `specialist_dispatcher` alias → `invoke_specialists_node`

### `graphs/core.py`
```
START → supervisor → build_context → invoke_specialists → assemble_response → END
              └──────────── assemble_response (name-only / not found)
```

## Verification

```text
$ uv run ruff check src/agents/context.py src/agents/supervisor.py src/agents/dispatch.py src/graphs/core.py tests/...
All checks passed!

$ uv run pytest -m smoke -q
25 passed, 9 deselected in 0.68s

$ uv run pytest -m full -q -k "query_existing_person or query_missing_person or query_non_core_attributes"
3 passed, 31 deselected in 0.45s

$ uv run pytest -m full -q tests/test_core_graph.py
7 passed in 0.16s
```

## Scope confirmation

Graph orchestration + context builder only. Did not re-gen committed specialists or run 1600 integration/docs capstone.

**Ready for next slice:** `2026-06-09-1600-integration-tests-reset-docs-regen-reprocess.md`
