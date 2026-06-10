# Review — Entity ID unification Slice 13

**Reviewer:** Grok (June 2026)  
**Verdict:** **Approve** — uuid4 unification shipped; persistence path correct; smoke green.

---

## Summary

Slice 13 replaces deterministic uuid5 seed IDs with opaque uuid4 allocated through `ensure_bound_entity`, persisted in `entities.json` `bind_index`. MCP `refresh_runtime_from_disk` resets the registry singleton before seed reload so per-query enrichment reuses on-disk ids. Runtime seed resolution remains for Slice 14.

---

## Checklist

| Item | Verdict | Notes |
|------|---------|-------|
| `ensure_bound_entity` | Pass | uuid4 on miss; bind_index reuse on hit; source preserved on duplicate |
| `bind_provisional` refactor | Pass | Delegates to helper |
| Seed loader | Pass | `_enrich_person` → `seed_bootstrap` validated rows |
| `storage/core.py` | Pass | Aligned with registry helper |
| MCP runtime refresh | Pass | `reset_entity_registry()` before seed reset |
| uuid5 removal | Pass | `rg uuid5 src/` clean |
| Tests | Pass | 32 entity + 266 smoke |
| Docs | Pass | architecture, walkthrough, program map |

---

## Behavior note

Seed queries now populate `entities.json`. Fixture tests no longer call `seed_from_file` where it pre-populated the registry; assertions target specific bind keys or result ids instead of `len(entities) == 1`.

---

## Tests

```
uv run ruff check src tests
uv run pytest tests/test_entity_registry_bind.py tests/test_entity_growth.py \
  tests/test_entity_validation.py tests/test_entity_unknown_mvr.py -q
→ 32 passed
uv run pytest -m smoke -q
→ 266 passed
```

---

## Nits (fixed post-review)

- Slice spec status → **Shipped**; exit criteria checked
- `MYCELIUM_ENTITIES_PATH` preserved in `refresh_runtime_from_disk`
- `test_refresh_runtime_preserves_seed_entity_ids` added

---

## Recommendation

Commit Slice 13. Mark done in `TODO.md`. Queue Slice 14 (remove runtime seed branch) when ready.
