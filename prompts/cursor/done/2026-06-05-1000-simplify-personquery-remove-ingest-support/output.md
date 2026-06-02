# Output: Simplify PersonQuery (query-only)

## Summary

Removed `provided_data` from `PersonQuery` in `src/models/state.py`. Public model is now `person_key` + `requested_attributes` only.

## Verification

```bash
uv run python -c "from models.state import PersonQuery; s=PersonQuery.model_json_schema(); assert 'provided_data' not in s['properties']"
PersonQuery(person_key="Nichanan Kesonpat")  # validates
```

Schema description is query-only; ingest example removed from `json_schema_extra`.

## Follow-up

CLI (1010), MCP (1020), agents (1030–1050) updated in same batch.
