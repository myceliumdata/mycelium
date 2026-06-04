# Slice 1700 — Expose person_id UUID in results (reprocess)

## Claim

Moved `prompts/cursor/next/2026-06-09-1700-expose-uuid-in-results-reprocess.md` → `prompts/cursor/in-progress/2026-06-09-1700-expose-uuid-in-results-reprocess/prompt.md`, then delivered here.

## Summary

Restored slice **1700-expose-uuid-in-results**: stable `person_id` (uuid5 from seed loader) is now on the `Person` model and in every public `results` dict alongside the legacy seed `"id"`. Identity builders in the supervisor and all six committed specialists (plus the Jinja template) propagate `person_id`. Tests and docs updated. Manual single-key and ambiguous-name queries return distinct UUIDs per match.

## Code changes (1700 scope)

| Area | Change |
|------|--------|
| `src/models/state.py` | `Person.person_id`; `PersonResponse.results` docstring |
| `src/agents/supervisor.py` | `_identity_records_from_seed` / `_persons_from_seed` include `person_id` |
| `src/agents/factory/templates/specialist_agent.py.j2` | `_identity_from_context` + `Person(...)` |
| `src/agents/specialists/*_specialist.py` | Same `person_id` in identity builders (synced with template) |
| `tests/test_core_graph.py` | Assert UUID on lookup; `test_results_are_plain_dicts` allows `person_id` |
| `docs/architecture.md` | Results section documents `person_id` |
| `docs/plans/seed-data-context-architecture.md` | Mark slice 1700 done |

**Not in scope:** 1710 (`CORE_PERSON_FIELDS` / `non_core_attributes`), 1720 (seed transform / results `"id"` = UUID only).

## git diff --stat (slice-touched paths)

```text
 docs/architecture.md                               |  69 +++--
 .../factory/templates/specialist_agent.py.j2       | 318 +++++++++++++++++---
 src/agents/specialists/contact_specialist.py       | 322 ++++++++++++++++++---
 ... (5 more specialists, same pattern)
 src/agents/supervisor.py                           | 146 ++++++++--
 src/models/state.py                                |  47 ++-
 tests/test_core_graph.py                           |  46 ++-
```

(Working tree may include uncommitted changes from earlier redesign slices; 1700 edits are limited to identity/`person_id` exposure and related tests/docs.)

## Verification

```text
$ uv run ruff check src/models/state.py src/agents/supervisor.py src/agents/specialists/ tests/test_core_graph.py docs/architecture.md
All checks passed!

$ uv run pytest -m smoke -q
23 passed, 11 deselected in 0.61s

$ uv run pytest -m full -q -k "query_existing_person or query_missing_person or query_non_core_attributes or test_results_are_plain_dicts"
4 passed, 30 deselected in 0.19s
```

### Manual CLI

```text
$ uv run mycelium query --person-key "person-0001"
results[0].person_id = "81e2ab33-be6c-5d72-bbbd-fac267d738fb"
results[0].id = "person-0001"  (legacy seed id preserved)

$ uv run mycelium query --person-key "Kevin Zhang"
2 results; distinct person_ids:
  person-0058 / Bain → 996c0133-2613-51d5-b5af-17b94e181fc3
  person-0438 / Upfront → 7bfdc1be-15c2-5f68-bdf7-115726a0ec76
message: Found 2 records for 'Kevin Zhang'.
```

## Scope confirmation

Expose `person_id` in public results and `Person` only. No elimination of core-person-field filtering (1710) or seed `"id"` transform (1720).

**Ready for next slice:** `2026-06-09-1710-eliminate-core-person-fields-reprocess.md`
