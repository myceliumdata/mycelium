# Output: Redesign PersonResponse (light minimalist)

## Summary

Replaced the heavy `PersonResponse` (status, person, data, data_request, deferred_attributes, errors) with a three-field contract: `results`, `message`, and `debug`. Removed unused `DataRequest`. Updated supervisor, graph fallback, CLI exit logic, and tests.

## New model

```python
class PersonResponse(BaseModel):
    results: list[dict[str, Any]]  # plain dicts only
    message: str
    debug: str
```

## Files modified

| File | Change |
|------|--------|
| `src/models/state.py` | New `PersonResponse`; removed `DataRequest` |
| `src/models/__init__.py` | Dropped `DataRequest` export |
| `src/agents/supervisor.py` | All response paths use results/message/debug |
| `src/graphs/core.py` | Fallback response shape |
| `src/main.py` | Exit code: `0` when `results` non-empty |
| `tests/test_core_graph.py` | Assertions on new shape; added plain-dict test |

**Out of scope (unchanged):** `PersonQuery`, `Person`, storage, MCP (returns `model_dump_json` automatically).

## Message patterns by scenario

| Scenario | `results` | `message` (example) |
|----------|-----------|---------------------|
| Found | 1 core dict | "Found core record for {name}." |
| Non-core requested | 1 core dict | "We have a core record for {name}, but we're still researching {attrs}." |
| Missing | `[]` | "No core record found… Supply minimum viable fields (name, employer)…" |
| Ingested | 1 core dict | "Successfully ingested and validated {name}." |
| Validation failed | `[]` | "Validation failed for the person record: …" |

`debug` always includes `person_key` and `requested_attributes`; adds `outcome` and context-specific keys.

## Verification

- `uv run pytest` — **5 passed**
- `uv run ruff check src tests` — clean
- CLI smoke (fresh temp DB + seed):
  - Nichanan Kesonpat — `results` with core dict, found message
  - Same + `--attributes email` — core dict + "still researching email"
  - Unknown person — empty `results`, ingest guidance in `message`

## Example response (non-core)

```json
{
  "results": [{"id": "person-0001", "name": "Nichanan Kesonpat", "employer": "1k(x)"}],
  "message": "We have a core record for Nichanan Kesonpat, but we're still researching email.",
  "debug": "person_key='Nichanan Kesonpat'; requested_attributes=['email']; outcome='non_core_requested'; deferred_attributes='email'"
}
```

## Follow-ups

- README / architecture docs still describe `specialist_required` status — update in a doc-only task.
- MCP consumers should read `message` + `results` instead of `status`.
- Consider whether `debug` should be stripped from MCP responses in production.

## In-progress cleanup

Removed only `prompts/cursor/in-progress/2026-06-01-1912-redesign-response-model-light-minimalist.md`.
