# Output: Remove ingest from CLI

## Summary

Removed `ingest` subcommand, `_load_person_data`, and ingest dispatch from `src/main.py`. CLI exposes `query` and `seed` only.

## Verification

```bash
uv run mycelium --help   # {query,seed}
```

Query path unchanged.
