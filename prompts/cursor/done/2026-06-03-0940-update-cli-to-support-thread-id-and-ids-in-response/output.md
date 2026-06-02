# Output: Update CLI for thread_id and response IDs

## Summary

Confirmed and polished CLI integration for `thread_id` and the new `PersonResponse` correlation fields. Wiring was largely in place; changes clarify behavior and centralize output.

## Prior state

- `--thread-id` existed on `query` and `ingest`
- `run_query(..., thread_id=...)` was already called
- `model_dump_json` already emitted `trace_id` and `thread_id` (null when unset)

## Changes (`src/main.py`)

| Change | Purpose |
|--------|---------|
| `_THREAD_ID_HELP` | Document flag on both subcommands |
| `_resolve_thread_id()` | Explicit default UUID when flag omitted |
| `_print_response()` | Single path for JSON including `trace_id` / `thread_id` |
| `args.thread_id` | Direct access (no `getattr`) |

## Manual verification

```bash
uv run mycelium query --person-key "Nichanan Kesonpat" --thread-id "cli-thread-42"
```

Output includes:

```json
"trace_id": null,
"thread_id": "cli-thread-42"
```

(`trace_id` populated when `LANGCHAIN_TRACING_V2` is enabled — see task 0910.)

## Verification

- `uv run ruff check src` — clean
- `uv run pytest` — **11 passed**

## Follow-up

- **0950** — MCP server (JSON already includes fields via `model_dump_json`)
- **0980** — optional `--trace-url` helper

## In-progress cleanup

Removed only `prompts/cursor/in-progress/2026-06-03-0940-update-cli-to-support-thread-id-and-ids-in-response.md`.
