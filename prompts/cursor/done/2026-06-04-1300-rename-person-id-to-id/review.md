# Review — 2026-06-04-1300-rename-person-id-to-id

**Reviewer:** Grok (on behalf of Paul)

**Overall:** Approved. Single canonical `id` across seed, graph state, specialists, storage compat, tests, and living docs. No `person_id` in `src/` or `tests/`.

## Strengths

- `seed.py`: `_assign_id`, enriched records use `id`, `SeedData.by_id`.
- `Person` model: removed duplicate `person_id`; `current_id` on graph state.
- Supervisor identity builders emit `id` only in public dicts.
- Specialist template + six agents: `_resolve_id`, `specialist_contrib["id"]`.
- Docs updated; historical table rows in plan doc retain slice numbers (acceptable).
- Verification: ruff clean, smoke 23→27 after 1400 (1300 was 23 at delivery), full query tests pass, `rg person_id` clean under `src/`/`tests/`.

## Minor notes

- Plan doc still mentions slice 1700 `person_id` in history table — intentional changelog, not runtime drift.
- Specialist `storage.json` keys are UUID strings (unchanged); only field names in code changed.

## Status

**Approved.** Ready for 1400 (attribute-scoped results), which was blocked on this rename.