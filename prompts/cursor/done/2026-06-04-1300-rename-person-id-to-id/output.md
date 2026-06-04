# Slice 1300 — Rename `person_id` → `id` (canonical UUID)

## Claim

Moved `prompts/cursor/next/2026-06-04-1300-rename-person-id-to-id.md` → `prompts/cursor/in-progress/2026-06-04-1300-rename-person-id-to-id/prompt.md`, then delivered here.

## Summary

Single canonical identifier: **`id`** is the stable UUID everywhere (seed enrichment, graph state, specialist contribs, public `results`, `Person` model). Removed the parallel `person_id` field and renamed `current_person_id` → `current_id`, `SeedData.by_person_id` → `by_id`, `_assign_person_id` → `_assign_id`, `_resolve_person_id` → `_resolve_id`, context meta `person_ids` → `ids`. Updated Jinja template and all six committed specialists. UUID generation (`uuid5` from name|employer) unchanged.

## Scoped changes

| Area | Change |
|------|--------|
| `src/agents/seed.py` | `id` on enriched records; `by_id`; `_assign_id` |
| `src/models/state.py` | Removed `Person.person_id`; `current_id` on graph state |
| `supervisor.py`, `dispatch.py`, `context.py` | Identity/results use `id` only; meta `ids` |
| Specialist template + 6 `*_specialist.py` | `_resolve_id`, `specialist_contrib["id"]`, `current_id` |
| `storage/core.py`, `person_prep.py` (`ensure_id`) | Test/legacy compat |
| `tests/` | Assertions on `id` only |
| `docs/architecture.md`, plan doc | `id` as stable UUID |

## git diff --stat

```text
 docs/architecture.md                               | 17 +++----
 docs/plans/seed-data-context-architecture.md       |  5 +-
 src/agents/context.py                              | 10 ++--
 src/agents/dispatch.py                             | 14 +++---
 ... (template + 6 specialists, seed, state, tests)
 21 files changed, 261 insertions(+), 278 deletions(-)
```

## Verification

```text
$ uv run ruff check src tests
All checks passed!

$ uv run pytest -m smoke -q
23 passed, 11 deselected in 0.73s

$ uv run pytest -m full -q -k "query_existing_person or query_missing_person or query_non_core_attributes"
3 passed, 31 deselected in 0.14s

$ rg 'person_id' src tests docs/architecture.md docs/plans/seed-data-context-architecture.md
docs/architecture.md:209:- Canonical rename: `person_id` → `id` everywhere (slice 1300, June 2026)
docs/plans/seed-data-context-architecture.md:20:| 1700 | Expose `person_id` (UUID) in public `results` ...
docs/plans/seed-data-context-architecture.md:23:| 1300 | Rename `person_id` → `id` everywhere ...
(no matches under src/ or tests/)
```

### Manual CLI

```text
$ uv run mycelium query --person-key "Nichanan Kesonpat"
results[0]: {"id": "<uuid>", "name": "...", "employer": "..."}  # no person_id key
```

## Scope confirmation

Rename only; no attribute filtering (1400) or trace_url work.

**Ready for next slice:** `2026-06-04-1400-filter-query-results-and-trace-url.md`
