# Slice 1710 — Eliminate CORE_PERSON_FIELDS / non_core_attributes (reprocess)

## Claim

Moved `prompts/cursor/next/2026-06-09-1710-eliminate-core-person-fields-reprocess.md` → `prompts/cursor/in-progress/.../prompt.md`, then delivered here.

## Summary

Removed the legacy core vs. non-core attribute split. Any `requested_attributes` (including `name` and `employer`) now flows through specialist classification, invocation, and the assembled status message path. Identity `results` still return full seed records with `person_id`.

## Scoped changes

| File | Change |
|------|--------|
| `src/models/state.py` | Removed `CORE_PERSON_FIELDS`, `MINIMUM_VIABLE_FIELDS`, `non_core_attributes`; added `normalized_requested_attributes` |
| `src/models/__init__.py` | Updated exports |
| `src/agents/dispatch.py` | `assemble_response_node` uses all requested attrs (not core-filtered) |
| `src/agents/routing.py` | Legacy routing helper uses all requested attrs |
| `src/agents/validator.py` | Local `_MINIMUM_VIABLE_FIELDS` (unwired legacy) |
| `specialist_agent.py.j2` + six `*_specialist.py` | `_resolve_owned_fields` fallback uses `requested_attributes` directly |
| `docs/architecture.md` | Removed core-field privilege rules |
| `docs/plans/seed-data-context-architecture.md` | Mark 1710 done |

**Not in scope:** 1720 (seed transform / results `"id"` = UUID only).

## Verification

```text
$ uv run ruff check src/models/ src/agents/dispatch.py src/agents/routing.py src/agents/validator.py src/agents/specialists/ src/agents/factory/templates/specialist_agent.py.j2
All checks passed!

$ uv run pytest -m smoke -q
23 passed, 11 deselected in 0.89s

$ uv run pytest -m full -q -k "query_existing_person or query_missing_person or query_non_core_attributes"
3 passed, 31 deselected in 0.13s
```

### Manual CLI (`--attributes name`)

```text
$ uv run mycelium query --person-key "Nichanan Kesonpat" --attributes name
message: Found record for Nichanan Kesonpat. name not currently available but may be in the future (via contact_specialist).
results: full identity + person_id
debug: outcome='assembled'; contributions=1
```

## Scope confirmation

Eliminated core-person-field filtering only. Did not change seed JSON shape or public `"id"` semantics (1720).

**Ready for next slice:** `2026-06-09-1720-eliminate-id-from-seed-transform-reprocess.md`
