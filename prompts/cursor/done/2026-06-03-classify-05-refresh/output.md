# Task output — classify-05-refresh

## Claim

`prompts/cursor/next/2026-06-03-classify-05-refresh.md` → `in-progress/.../prompt.md`

## Summary

Implemented `refresh_from_llm` per approved plan — the **only** LLM path for classification.

| Piece | Detail |
|-------|--------|
| `engine.py` | Full refresh body: early return when attrs already known (before any LLM init), lazy `ChatOpenAI`, structured `CategoryProposal` list, conf ≥ 0.7, additive merge, `last_updated` / `model_used`, `_save` + `_load` |
| Tests | `test_refresh_from_llm_early_return_when_all_known` (no API key), `test_refresh_from_llm_merge_with_mock_llm` (fake LLM, no network) |

**Fix during implementation:** Moved `attrs_to_consider` check **before** `ChatOpenAI()` so the early-return path never touches credentials.

## Scope

- `src/agents/classification/engine.py`
- `tests/test_supervisor_routing.py`

## Verification

### `uv run pytest -m smoke -q`

```
17 passed, 9 deselected in 0.07s
```

### Hot-path grep (no hits outside classification)

```bash
git grep -n "ChatOpenAI\|refresh_from_llm" -- \
  src/agents/supervisor.py src/agents/core_data.py src/graphs/ \
  src/mycelium_mcp/ src/main.py src/models/
```

(empty — correct)

Hits only in `src/agents/classification/engine.py`.

### `uv run ruff check` (scoped)

```
All checks passed!
```

## Ready for slice 06

Final polish + full verification matrix + small `architecture.md` note.
