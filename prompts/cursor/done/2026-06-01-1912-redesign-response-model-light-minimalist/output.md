# Output: Redesign PersonResponse (light minimalist)

## Summary

Delivered the minimal three-field `PersonResponse` (`results`, `message`, `debug`) and aligned supervisor, CLI, and MCP with the revised task scope. **Ingestion paths are stubbed** — no routing to enrich/validator when `provided_data` is present.

This task was queued twice; commit `7e9f4b6` implemented the model shape; this pass adds ingestion stubs and TODO follow-ups per the stricter prompt revision.

## New model

```python
class PersonResponse(BaseModel):
    results: list[dict[str, Any]]  # plain dicts only (id, name, employer)
    message: str
    debug: str
```

## Files modified

| File | Change |
|------|--------|
| `src/models/state.py` | Minimal `PersonResponse` (prior commit) |
| `src/agents/supervisor.py` | Lookup + non-core messages; **ingestion stub** |
| `src/mcp/server.py` | Instructions + `submit_person_data` docstring |
| `src/graphs/core.py` | Fallback uses new shape (prior commit) |
| `src/main.py` | Exit `0` when `results` non-empty (prior commit) |
| `tests/test_core_graph.py` | Lookup tests; `test_ingest_stubbed` |
| `TODO.md` | Marked 1912 complete; added ingestion follow-ups |

## Ingestion stub behavior

| Path | Behavior |
|------|----------|
| `query.provided_data` set | `results=[]`, message = "Ingestion flow is not yet implemented." |
| `validation_passed` set (legacy graph path) | Same stub |
| Missing person (no `provided_data`) | `results=[]`, not-found message + ingestion stub text |

Enrich/validator nodes remain in the graph but are not reached from the supervisor for new ingest requests.

## Message patterns (lookup)

| Scenario | `results` | `message` |
|----------|-----------|-----------|
| Found | 1 core dict | "Found core record for {name}." |
| Non-core requested | 1 core dict | "We have a core record for {name}, but we're still researching {attrs}." |
| Missing | `[]` | "No core record found… Ingestion flow is not yet implemented." |

Query context lives in `debug` (`person_key`, `requested_attributes`, `outcome`, etc.).

## Verification

- `uv run pytest` — **5 passed**
- `uv run ruff check src tests` — clean
- CLI: existing person, non-core (`still researching`), unknown person (ingestion stub)

## Prior pass note

`DataRequest` was removed in `7e9f4b6` before this revision asked to leave dead code in place. Restoring it was not done; follow-up TODO item covers cleanup/redesign.

## TODO.md

- Marked minimal `PersonResponse` complete (`2026-06-01-1912-redesign-response-model-light-minimalist`)
- Added follow-ups: ingestion handshake, dead-code cleanup, optional future `status` field

## In-progress cleanup

Removed only `prompts/cursor/in-progress/2026-06-01-1912-redesign-response-model-light-minimalist.md`.
