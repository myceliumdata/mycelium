# Output: LangSmith trace URL helper

## Summary

Added `get_langsmith_trace_url()` in `src/utils/langsmith.py` to turn a `PersonResponse.trace_id` into a LangSmith UI link, with optional org/project-scoped URLs via environment variables.

## Implementation

| Piece | Detail |
|-------|--------|
| `get_langsmith_trace_url(trace_id)` | Default: `https://smith.langchain.com/r/{trace_id}` (redirect-friendly) |
| `LANGSMITH_ORG_ID` + `LANGSMITH_PROJECT_ID` | Full path: `/o/{org}/projects/p/{project}/r/{trace_id}` |
| `LANGSMITH_UI_BASE_URL` | Override UI host (default `https://smith.langchain.com`) |
| `utils` package | Re-export from `src/utils/__init__.py` |
| `.env.example` | Commented optional vars |

No changes to `PersonResponse`, CLI, or MCP output.

## Tests

`tests/test_langsmith_utils.py` — short URL, scoped URL, custom base, empty id error.

## Verification

- `uv run pytest` — **19 passed**
- `uv run ruff check src/utils tests/test_langsmith_utils.py` — clean

## Usage

```python
from utils.langsmith import get_langsmith_trace_url

if response.trace_id:
    print(get_langsmith_trace_url(response.trace_id))
```

## Open questions

None.
