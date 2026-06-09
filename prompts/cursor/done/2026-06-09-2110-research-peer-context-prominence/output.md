# Output — Research peer context prominence fix (`2110`)

## Summary

Fixed missing `PEER SPECIALIST FINDINGS` header when research context uses the **flattened** `_research_context()` shape (`specialists[category] → field records`). `peer_specialists_for_entity()` now supports both flattened (production) and nested (graph) shapes. Peer block is human-readable; `pending` and `na` fields omitted from the prominent section.

## Changes

| File | Change |
|------|--------|
| `src/tools/research.py` | `_looks_like_field_record_map`, `_peer_category_row`, `_trim_peer_fields`, `peer_display_for_prompt`; dual-shape `peer_specialists_for_entity()`; disambiguation-first insert order |
| `research/_peer_context.j2` | Category-grouped lines (`field: value (sources: …)`) via `peer_display` |
| `tests/test_research.py` | Flattened production-path test, nested regression, `na` omission test |

**User message order (when both present):** DISAMBIGUATION → PEER SPECIALIST FINDINGS → intro → category guidance → JSON.

## Tests

```bash
uv run pytest tests/test_research.py -m smoke -q   # 18 passed
```

## For Grok + Paul

- **Manual verify:** Re-run Angela Murphy @ TalentCare + `spouse`; LangSmith user message should show `PEER SPECIALIST FINDINGS` with `contact` / `demographic` lines before JSON.
- **Suggested commit message:** `fix(research): render peer findings for flattened specialist context shape`

## Exit criteria

- [x] `peer_specialists_for_entity()` handles flattened `_research_context` shape
- [x] `PEER SPECIALIST FINDINGS` renders for production-shaped context
- [x] Peer block human-readable (not JSON blob)
- [x] `pending` and `na` omitted from prominent block
- [x] Nested graph shape regression test
- [x] Ruff clean; no `TODO.md` edit
