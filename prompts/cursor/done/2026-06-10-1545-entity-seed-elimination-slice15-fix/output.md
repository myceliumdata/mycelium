# Slice 15 fix — Supervisor routing smoke

## Summary

Repaired full-smoke failures in `tests/test_supervisor_routing.py` after Slice 15 registry-only resolution. Supervisor integration tests now bootstrap `any-key` into `entities.json` via `import_seed_for_test` and assert **`resolved via registry`**.

## Changes

| File | Change |
|------|--------|
| `tests/test_supervisor_routing.py` | Added `_configure_any_key_registry` helper; wired into three supervisor integration tests; updated docstring and audit assertion |

## Tests

**15 passed** — `test_supervisor_routing.py` smoke  
**270 passed** — full smoke (`-m smoke`)

```bash
uv run pytest tests/test_supervisor_routing.py -m smoke -q
uv run pytest -m smoke -q
```

## For Grok + Paul

- Slice 15 + this fix ready to commit together (stacked commits OK)
- Mark **Slice 15 fix (`1545`)** done in `TODO.md` alongside Slice 15
- Review folder: `prompts/cursor/done/2026-06-10-1545-entity-seed-elimination-slice15-fix/`
- Suggested commit message (after review):

```
Fix supervisor routing tests for registry-only resolution (Slice 15 fix).

Import seed into entities.json in supervisor integration tests;
assert resolved via registry. Full smoke green.
```

- **Did not edit `TODO.md`** (per governance)
