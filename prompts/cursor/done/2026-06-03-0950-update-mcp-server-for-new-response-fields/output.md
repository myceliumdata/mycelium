# Output: Update MCP Server for trace_id and thread_id

## Summary

Updated `src/mcp/server.py` so MCP clients can pass an optional top-level `thread_id` in query JSON, have it forwarded to `run_query`, and receive `trace_id` and `thread_id` in serialized `PersonResponse` JSON.

## Changes (`src/mcp/server.py`)

| Change | Purpose |
|--------|---------|
| `_parse_query_payload()` | Strips optional `thread_id` before `PersonQuery` validation; defaults to new UUID when omitted |
| `_serialize_response()` | Central `model_dump_json(indent=2)` so correlation fields are always emitted |
| `_run_mcp_query()` | Shared path for `query_person` |
| `submit_person_data` | Uses same parse/serialize path as queries |
| FastMCP `instructions` + tool docstrings | Document request/response fields |
| `mycelium://schema/person-response` resource | Exposes `PersonResponse` JSON schema for clients |

## Behavior

- Request: `PersonQuery` fields plus optional `"thread_id": "..."`.
- Response: full `PersonResponse` including `trace_id` (LangSmith when tracing enabled) and echoed `thread_id`.
- Error path for missing `provided_data` on ingest unchanged (plain error JSON, not `PersonResponse`).

## Verification

- `uv run ruff check src/mcp/server.py` — clean
- `uv run pytest` — **11 passed**

Note: direct `from mcp.server import ...` in a one-off script resolves the installed `mcp` package, not `src/mcp/server.py`. Use `uv run mycelium-mcp` or the project’s `mcp.server` entry point for runtime checks.

## Open questions

None.
