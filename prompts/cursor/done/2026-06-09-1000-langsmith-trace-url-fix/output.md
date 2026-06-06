# langsmith-trace-url-fix (slice 1000) — Output

## Claim

Moved `prompts/cursor/next/2026-06-09-1000-langsmith-trace-url-fix.md` → `prompts/cursor/in-progress/2026-06-09-1000-langsmith-trace-url-fix/prompt.md`.

## Approach

Enhanced `get_langsmith_trace_url()` in `src/utils/langsmith.py`:

1. **`_resolve_langsmith_scope()`** — returns `(org_id, project_id)` or `None`
2. **Precedence:** `LANGSMITH_ORG_ID` + `LANGSMITH_PROJECT_ID` env → cached `Client().read_project(LANGCHAIN_PROJECT)` using `LANGCHAIN_API_KEY` or `LANGSMITH_API_KEY` → fallback short `/r/{trace_id}` URL (may 404 in UI)
3. **Process cache** — successful resolution cached in `_cached_scope`; `reset_langsmith_scope_cache()` for tests

`src/main.py` unchanged (already calls `get_langsmith_trace_url` after JSON).

## Files changed

| File | Change |
|------|--------|
| `src/utils/langsmith.py` | API auto-resolve + cache |
| `tests/test_langsmith_utils.py` | API mock, env precedence, fallback tests |
| `README.md` | LangSmith URL expectations |
| `.env.example` | Auto-resolve comment |
| `docs/architecture.md` | Observability bullet |

## Verification

```
$ uv run pytest -m smoke -q tests/test_langsmith_utils.py
7 passed

$ uv run ruff check src/utils/langsmith.py tests/test_langsmith_utils.py
All checks passed!
```

## Manual (Paul / with live credentials)

With `LANGSMITH_ORG_ID` / `LANGSMITH_PROJECT_ID` **unset**, `LANGCHAIN_API_KEY` + `LANGCHAIN_PROJECT=mycelium` set:

```bash
uv run mycelium query --person-key "Nichanan Kesonpat" --attributes email
```

Printed URL after JSON should use `/o/{tenant_id}/projects/p/{project_id}/r/{trace_id}` and open in LangSmith while logged in.

(Not run in automated sandbox — requires live LangSmith API + project.)

## Tradeoffs

- One API `read_project` per MCP/CLI process on first trace URL (cached thereafter).
- API failure does not cache negative result — subsequent calls may retry (unlikely in practice after first miss).
