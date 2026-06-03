# Task output — classify-01-scaffold

## Claim

Moved `prompts/cursor/next/2026-06-03-classify-01-scaffold.md` → `in-progress/2026-06-03-classify-01-scaffold/prompt.md` before any edits.

## Summary

Pure addition only — no existing source files changed.

| File | Purpose |
|------|---------|
| `data/categories.json` | Committed seed: 5 categories, 18 attributes (exact content from approved plan) |
| `src/agents/classification/models.py` | Four Pydantic models: `Category`, `CategoryTreeData`, `ClassificationResult`, `CategoryProposal` |
| `src/agents/classification/engine.py` | Stubs: `_SEED_CATEGORIES`, `CategoryTree` with `_load`/`_save` (plain `write_text`), `classify()` returns safe `unknown`, `refresh_from_llm` raises `NotImplementedError` |
| `src/agents/classification/__init__.py` | Exports `get_category_tree`, `CategoryTree`, `reset_category_tree` |

**Decisions:** Followed lightweight priority — no atomic save, no real `classify()` lookup (slice 02). `_load` reads committed JSON when present. Stub `classify()` always returns `unknown` so imports and `get_category_tree()` work without slice 02.

**Discovery:** Two Kevin Zhang entries confirmed in `data/seed_crm.json` (regression anchor for later slices). No pre-existing `classification/` dir or `categories.json`.

## Scope confirmation

Only the four paths listed in the task prompt were created. No supervisor, state, tests, or docs edits.

## Verification

### `uv run ruff check src/agents/classification`

```
All checks passed!
```

### `uv run pytest -m smoke -q`

```
13 passed, 9 deselected in 0.06s
```

### `git status --porcelain` (new files)

```
?? data/categories.json
?? src/agents/classification/
```

(Paul/Grok can `git add` on commit; staging attempted in sandbox.)

### Seed + import smoke

```
18 attribute keys listed (email … investments)
seed ok
import ok
get ok
attribute='email' category='unknown' ... confidence=0.0   # expected stub until slice 02
```

### Attribute count

`len(attribute_map) == 18`, `len(categories) == 5`.

## Ready for slice 02

Implement real `classify()` fast lookup in `engine.py` per `docs/plans/classification-engine-phase1.md` Step 2.

## Open questions

None — scaffold matches approved plan.
