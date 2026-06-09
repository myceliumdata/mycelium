# Review — Research peer context prominence (`2110`)

**Verdict: Approved**

Reviewed 2026-06-09 (Grok). Smoke tests: 18 passed; ruff clean on Python files.

## What landed

| Requirement | Status |
|-------------|--------|
| Dual-shape `peer_specialists_for_entity()` (flattened + nested) | ✅ `_peer_category_row`, `_looks_like_field_record_map` |
| `PEER SPECIALIST FINDINGS` for production `_research_context` shape | ✅ Angela-shaped flattened test |
| Human-readable peer block via `peer_display_for_prompt` | ✅ No `tojson` blob |
| Omit `pending` / `na` from prominent block | ✅ `_trim_peer_fields` + tests |
| Message order: DISAMBIGUATION → PEERS → intro | ✅ `insert_at = 1 if extra_disamb else 0` |
| Nested graph shape regression | ✅ |

Root cause fixed correctly at the consumer (`peer_specialists_for_entity`) without changing `_research_context` producer shape.

## Nits (non-blocking)

None.

## Manual sign-off (Paul)

Clear `spouse` (if cached), re-run Angela Murphy @ TalentCare. LangSmith user message should show:

```
DISAMBIGUATION (mandatory):
...
PEER SPECIALIST FINDINGS (read-only):
contact:
  - email: ... (sources: ...)
demographic:
  - city: Austin, TX
```

before the JSON block.

## Commit

Suggested: `fix(research): render peer findings for flattened specialist context shape`