# Output — Research prompt bind disambiguation (`2000`)

## Summary

Strengthened research prompts so when `context.bind.employer` is set, the LLM must include the employer in its **first** `web_search` query. Addresses the Angela Murphy @ Talentcare incident where plumbing was correct but the model ran name-only `"Angela Murphy spouse"` anyway.

## Changes

| Area | Change |
|------|--------|
| `_system.j2` | Conditional hard rules when `bind_has_employer`: first query must include name + employer; reject wrong-employer hits; no IMDB/Facebook guessing |
| `_disambiguation.j2` | New partial — plain-text mandatory block prepended to user message |
| `build_research_prompts()` | Passes `bind_name` / `bind_employer` / `bind_has_employer` to templates; disambiguation block first in user message |
| All six `*.md.j2` fragments | Employer-in-first-query echo; `relationships` has bad/good spouse query examples + entertainment false-positive warning |
| `_append_research_audit` | Adds `context_bind` (name + employer) to audit entries |

No specialist regen required — templates load at runtime from `templates/research/`.

## Tests

```bash
uv run pytest tests/test_research.py -m smoke -q   # 14 passed
```

New tests: with employer, without employer, whitespace employer; existing mock test asserts `context_bind` in audit.

## For Grok + Paul

- **Manual verify:** Re-run Angela Murphy + Talentcare + `spouse`; LangSmith first `web_search` should include `Talentcare`.
- **TODO.md:** Narrow **Research prompt context enrichment** to cross-category slice only; mark bind-disambiguation done after review.
- **Suggested commit message:** `fix(research): mandate employer in first web_search when bind.employer is set`

## Exit criteria

- [x] System prompt conditionally mandates employer in first `web_search`
- [x] User message prepends disambiguation block when employer present
- [x] All six category fragments aligned (relationships addresses incident)
- [x] Smoke tests for with / without / whitespace employer
- [x] Ruff clean; no specialist regen; no `TODO.md` edit
