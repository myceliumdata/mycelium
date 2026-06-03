# Task output — Ambiguous name lookups (Kevin Zhang)

## Claim

`prompts/cursor/next/2026-06-06-mcp-handle-ambiguous-names.md` → `in-progress/.../prompt.md` before implementation.

## Summary

Name-based `person_key` lookups now return **all** matching core records. Id lookups still return 0 or 1. No new Pydantic models — `PersonResponse.results` already supported lists.

**Storage:** `find_person` → `find_persons` → `list[Person]`; name query uses `fetchall()` ordered by `id`.

**Chain:** `CoreIdentity.find_by_key` → `list[Person]`; `response_found` / `response_non_core` accept `persons: list[Person]` with singular/plural messages and `num_matches` in `debug`.

**Graph state:** `MyceliumGraphState.persons` added; `person` set only when exactly one match (test compat).

**Routing (legacy/tests):** `SupervisorDecision.persons` added; same list semantics.

## Message examples

| Case | Message |
|------|---------|
| 1 match | `Found core record for Nichanan Kesonpat.` |
| 2+ matches | `Found 2 core records for 'Kevin Zhang'.` |
| Non-core, N matches | `We have 2 core records for 'Kevin Zhang', but we're still researching email.` |

## Verification

### `uv run ruff check` (scoped files)

```
All checks passed!
```

### `uv run pytest -m smoke -q`

```
13 passed, 9 deselected in 0.30s
```

### `uv run mycelium query --person-key "Kevin Zhang"`

```json
{
  "results": [
    {"id": "person-0058", "name": "Kevin Zhang", "employer": "Bain Capital Ventures"},
    {"id": "person-0438", "name": "Kevin Zhang", "employer": "Upfront Ventures"}
  ],
  "message": "Found 2 core records for 'Kevin Zhang'.",
  "debug": "... outcome='found'; num_matches='2'"
}
```

### Non-core attrs

```
message: "We have 2 core records for 'Kevin Zhang', but we're still researching email."
results: (both Kevin Zhang entries)
```

### Unique name (unchanged)

```
message: "Found core record for Nichanan Kesonpat."
results: length 1
```

## Follow-ups

- Optional dedicated smoke/full test with two-person stub for ambiguous names (Grok to classify if added).
- Future specialist disambiguation when callers need a single person from ambiguous names.

## Scope

Only files listed in the task prompt were modified.
