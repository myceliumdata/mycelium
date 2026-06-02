# Output: Update Documentation for trace_id and thread_id

## Summary

Documented `PersonResponse` correlation fields in architecture and README so developers know how to pass `thread_id` and interpret `trace_id` from CLI/MCP JSON.

## Changes

### `docs/architecture.md`

- Expanded **Response fields** under Core Ingestion Handshake to list `trace_id` and `thread_id` with purpose (LangSmith observability, session/checkpoint correlation).
- Noted fields are applied in `run_query` after graph completion.
- Minor **Technical Foundation** observability bullet update.
- Included pending **CoreIdentity** naming clarification (from rename task).

### `README.md`

- Quick start: `--thread-id` example on `query`.
- New **Response shape** subsection with sample JSON and field explanations.

## Verification

- Markdown only; no code changes required for this task.
- Manual review of formatting — no broken links introduced.

## Open questions

None.
