# Research prompts — mandatory bind disambiguation (employer in first search)

## Objective

Fix wrong-person research when `context.bind.employer` is present but the LLM runs name-only `web_search` queries anyway.

**Incident (Paul, June 2026):** Angela Murphy @ Talentcare, `spouse` researched by `relationships_specialist`. LangSmith shows correct prompt context:

```json
"bind": { "name": "Angela Murphy", "employer": "Talentcare" }
```

First tool call was still `web_search(query="Angela Murphy spouse")` (LangSmith may label the span `tavily_search`) → IMDB/Facebook hits for a different Angela Murphy (Mark Krigbaum). **Plumbing is correct; prompt compliance failed.**

This slice strengthens research prompts so employer disambiguation is **mandatory, prominent, and conditional** — not buried in JSON or soft category guidance.

**Read-only context:** `docs/architecture.md` (specialist research, bind identity), `TODO.md` (Research prompt context enrichment — cross-category work stays out of scope here).

## How to start (mandatory)

Follow `prompts/cursor/WORKFLOW.md`:

1. **Claim** this file: move it from `prompts/cursor/next/` to `prompts/cursor/in-progress/` before any implementation.
2. Deliver under `prompts/cursor/done/2026-06-09-2000-research-prompt-bind-disambiguation/`.
3. **Do not commit or push** until Grok + Paul review.

## Governance (mandatory)

- **Do not edit `TODO.md`.** Roadmap updates are for Grok + Paul after review.
- In `output.md`, add **"For Grok + Paul"**: what to check off, any roadmap notes, suggested commit message.
- Cursor delivers: code, tests, task-scoped docs, and `output.md` only.

## Scope boundaries (strict)

**You may only modify:**

- `src/agents/factory/templates/research/_system.j2`
- `src/agents/factory/templates/research/*.md.j2` (all six category fragments)
- `src/agents/factory/templates/research/_disambiguation.j2` (new partial — optional but preferred)
- `src/tools/research.py` (`build_research_prompts`, optionally `_append_research_audit` / `_execute_research`)
- `tests/test_research.py`

**Out of scope (do not touch):**

- `TODO.md`
- `src/agents/specialists/*` and Agent Factory regen (`*_specialist.py` are gitignored runtime copies; research templates load from `templates/research/` at runtime)
- Cross-category context (`context.specialists` / full `build_context` in `_research_context`)
- Operator force re-research, admin UI, post-search code validation loops
- Tavily API / tool implementation changes
- Changing `target_fields` write scoping or confidence thresholds

If you believe out-of-scope changes are required: **stop**, document in `output.md`, do not implement them.

## Background (current code)

- `build_research_prompts()` in `src/tools/research.py` renders `_system.j2` and a category fragment, then builds user message as: intro line → optional category guidance → JSON payload (`context` including `bind` is already in JSON).
- `_system.j2` line 11 is advisory: "using context.bind.name and context.bind.employer for disambiguation" — not enforced.
- `relationships.md.j2` has **no** employer guidance (incident category).
- `social.md.j2` mentions homonyms + employer corroboration but not first-query mandate.
- Bound tool name is **`web_search`** (`create_tavily_search_tool` in `src/tools/tavily.py`); prompts must say `web_search`, not `tavily_search`.
- `_research_context()` passes `bind` + own-category `storage` only (Slice 7). Do not widen context in this slice.

## Implementation

### 1. Conditional hard rules in system template

File: `src/agents/factory/templates/research/_system.j2`

Pass bind into `system_tpl.render()` from `build_research_prompts()` — e.g. `bind_name`, `bind_employer`, `bind_has_employer` (true when employer is non-empty after strip).

When `bind_has_employer` is true, system message must include **hard** rules (use Jinja `{% if bind_has_employer %}`):

- The **first** `web_search` query **must** include both the person name and employer string (or an unmistakable employer token).
- Do **not** run a name-only query when employer is known.
- If results describe a person at a **different** employer/industry than the bind employer, treat as a different person — return `na` with reason; do not return `found`.
- If no results corroborate the employer after reasonable attempts, return `na` — do not guess from entertainment/social profiles (IMDB, Facebook, etc.).

When employer is absent, keep name-only searches allowed; do not show employer-mandatory rules.

Keep existing schema, confidence, source, and `min_confidence` rules unchanged.

### 2. Prominent disambiguation block in user message (deterministic)

File: `src/tools/research.py` — `build_research_prompts()`

When `context.get("bind")` is a dict with non-empty `employer` (after `.strip()`), prepend a **plain-text** block as the **first** section of the user message (before intro, category guidance, and JSON). Example shape:

```
DISAMBIGUATION (mandatory):
- Person: Angela Murphy
- Employer: Talentcare
- Your FIRST web_search query MUST include "Talentcare" (or an equivalent employer token).
- Do NOT use name-only queries such as "Angela Murphy spouse".
- Reject sources that do not corroborate this employer.
```

Prefer rendering via new `research/_disambiguation.j2` partial (receives `bind_name`, `bind_employer`) over a long inline f-string.

When employer is absent or whitespace-only, omit the block entirely.

**Why first:** bind is already inside the JSON blob; the model ignored it. Top-of-message plain text is the compliance lever.

### 3. Category fragments (all six)

Update every file under `src/agents/factory/templates/research/*.md.j2`:

| File | Minimum change |
|------|----------------|
| `relationships.md.j2` | **Primary fix.** Warn against entertainment/social false positives when bind employer is a non-entertainment company. Include bad vs good query examples for relationship fields (e.g. spouse). |
| `contact.md.j2` | Require employer in first search when bind has employer (replace soft "cross-check"). |
| `professional.md.j2` | Align with mandatory first-query rule (already mentions employer). |
| `social.md.j2` | Strengthen homonym rule to match system template (first query includes employer). |
| `demographic.md.j2` | Short employer-in-first-search echo when researching bios/profiles. |
| `financial.md.j2` | Short employer/company token in first search when bind has employer. |

Keep fragments short; avoid duplicating the full system rules — echo the mandate only.

### 4. Optional: audit bind snapshot (small, in scope)

In `_execute_research` / `_append_research_audit`, add a `context_bind` field to each audit entry (name + employer only, no PII beyond what's already in bind). Helps operators verify what research saw without LangSmith. If trivial, include; if not, note skip in `output.md`.

### 5. Smoke tests

File: `tests/test_research.py`

Add `@pytest.mark.smoke` tests for `build_research_prompts` (import from `tools.research`):

1. **With employer** — `context={"bind": {"name": "Angela Murphy", "employer": "Talentcare"}, "entity_id": "…", "storage": {}}`, category `relationships` → user message starts with or contains `DISAMBIGUATION`; includes `Talentcare` and mandatory first-query language; system message includes employer hard rules (e.g. "first" + "web_search" + employer mandate).
2. **Without employer** — `bind: {"name": "Jane", "employer": null}` or `employer: ""` → no disambiguation block; system message does **not** require employer in first query.
3. **Whitespace employer** — `employer: "   "` → treated as absent (same as without employer).

No live Tavily/LLM calls.

## Verification

```bash
uv run pytest tests/test_research.py -m smoke -q
uv run ruff check src tests bin/
```

**Manual (Paul, after review):** Re-run Angela Murphy + Talentcare + `spouse`; LangSmith first `web_search` query should include `Talentcare` (not name-only).

## Deliverables

Under `prompts/cursor/done/2026-06-09-2000-research-prompt-bind-disambiguation/`:

- `prompt.md` (this file)
- `output.md` — summary, decisions, test category notes, **For Grok + Paul**:
  - Narrow **Research prompt context enrichment** in `TODO.md` to cross-category slice only; mark bind-disambiguation done after review
  - Suggested commit message (one line)

## Exit criteria

- [ ] System prompt conditionally mandates employer in first `web_search` when bind.employer is set
- [ ] User message prepends prominent disambiguation block when employer present
- [ ] All six category fragments aligned (relationships explicitly addresses incident)
- [ ] Smoke tests assert prompt text for with / without / whitespace employer
- [ ] Ruff clean; no specialist regen; no `TODO.md` edit by Cursor