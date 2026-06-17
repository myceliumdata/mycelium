# Output — closed identity grains and lazy field aliases

## Summary

Added per-grain `identity_mode` (`open` / `closed`), wired closed-grain step-1 resolve to skip `create_pending`, run lazy field alias expansion, and retry lookup. New `bind_alias_expansion` module uses structured LLM output when `OPENAI_API_KEY` is set; tests inject a deterministic expander. Baseball manifest and guide updated. `./bin/ci-local` green at **485** smoke tests.

## Files changed (high level)

| Area | Change |
|------|--------|
| `network/mvr.py` | `GrainMvrPolicy.identity_mode`; `is_closed_identity_grain()` |
| `agents/bind_alias_expansion.py` | **New** — `expand_field_aliases`, LLM prompt, injectable `AliasExpander` |
| `agents/target_resolve.py` | Optional `grain` + `alias_expander`; closed 0-hit path |
| `examples/networks/baseball/network.json` | `identity_mode: closed` on team + player |
| `examples/networks/baseball/guide.md` | Closed identity + lazy aliases |
| `docs/seed-bootstrap.md`, `baseball-example-program.md` | Open vs closed identity |
| `tests/test_closed_identity_lazy_aliases.py` | **New** — Bronx Bombers, Dodgers multi-match, XYZZY, CRM create_pending |

## LLM prompt shape

When no injectable expander and `OPENAI_API_KEY` is set:

- Model: `MYCELIUM_ALIAS_EXPANSION_MODEL` (default `gpt-4o-mini`)
- Structured output: `{ "entity_ids": ["uuid", ...] }`
- Prompt includes: grain + description, bind field, query value, `guide.md` text, capped canonical list (`id` + field value, max 500 rows)
- Returned ids must exist in the canonical list; aliases written via `add_field_alias` (`source` unchanged on entity; field index only)

**Mock injection:** pass `alias_expander: Callable[[grain, field, value, registry, guide_text], list[str]]` to `resolve_target_step1` or `expand_field_aliases(expander=...)`.

**Env vars:** `OPENAI_API_KEY` (required for production LLM path); optional `MYCELIUM_ALIAS_EXPANSION_MODEL`.

## Exit criteria

| # | Status |
|---|--------|
| E1 | Baseball team + player declare `identity_mode: closed` |
| E2 | Closed grain 0-hit never returns `create_pending` |
| E3 | Mock: Bronx Bombers → resolved; Dodgers → 2 ids |
| E4 | CRM open grain still `create_pending` |
| E5 | `./bin/ci-local` green — **485** smoke tests |
| E6 | LLM shape, mock injection, slice-3 notes below |

## For Grok + Paul

- **Slice 3 follow-ups:** `EntityQuery` has no `grain` yet — `resolve_target_step1(grain=…)` added for tests; supervisor/router must pass active grain when baseball queries land.
- **Fuzzy suggestions** on closed grains still use default-grain registry in `_lookup_suggestions_for_full_mvr` — acceptable until grain-aware routing; closed path tries alias expansion before fuzzy.
- **Provenance:** field aliases written at query time via `add_field_alias`; no separate `source=alias_expansion` actor kind yet (entity `source` unchanged).

**Suggested commit message:**

```
feat(resolve): closed identity grains and lazy field aliases

Baseball team/player never create_pending on miss; LLM alias expansion
writes field_aliases and retries lookup for multi-match or resolve.
```
