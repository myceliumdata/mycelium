# Review — Research prompt bind disambiguation (`2000`)

**Verdict: Approved** (later **superseded** — employer hardcoding reverted; MVR-generalized approach in slice `2010`)

Reviewed 2026-06-09 (Grok). Smoke tests and ruff re-run locally: 14 passed, all checks clean.

## What landed

- Conditional employer hard rules in `_system.j2` (`bind_has_employer` via Jinja).
- `_disambiguation.j2` prepended first in user message when employer is set.
- `build_research_prompts()` wires bind vars through system + category fragments.
- All six category fragments updated; `relationships.md.j2` has incident-specific bad/good examples.
- `context_bind` snapshot on `research_audit` entries — useful for operator debug.
- Three new smoke tests (with / without / whitespace employer) + audit assertion.

Matches prompt exit criteria. No specialist regen required (templates load at runtime).

## Nits (non-blocking)

1. **`_disambiguation.j2` bad-example** uses `"{name} spouse"` for every category — correct for relationships, slightly odd for contact/email. Category fragments already carry field-specific examples; acceptable as-is.
2. **`TODO.md` edited by Cursor** — violates governance; reverted/split by Grok + Paul in same commit batch (see below).
3. **Untracked** `_disambiguation.j2` and `done/` folder must be included in commit.

## Manual sign-off (Paul)

Re-run **Angela Murphy + Talentcare + `spouse`** after deploy; LangSmith first `web_search` query should include `Talentcare`. Prompt compliance is LLM-dependent — if it still fails, consider post-search validation or force re-research slice.

## Commit

Suggested message (from output): `fix(research): mandate employer in first web_search when bind.employer is set`

Include: research templates, `research.py`, `test_research.py`, `_disambiguation.j2`, `prompts/cursor/done/2026-06-09-2000-research-prompt-bind-disambiguation/`. Do **not** mix unrelated admin-checkpointer changes unless intentionally batched.

## Next

- Cursor slice **`2010`** (full peer specialist context) — remaining half of research context enrichment.
- Paul manual Angela test after restart / fresh research run (clears cached wrong spouse if present).