# Research prompts — full peer specialist context

## Objective

Restore **cross-category context** in research prompts: when a specialist researches a field, the LLM should see findings from **all** peer specialist stores for that entity, not only `bind` + own-category `storage`.

**Background:** Phase 1 plan (`docs/plans/specialist-research-phase1.md`) specified full `build_context` in the research user prompt. Slice 7 (`entity-boundary-cleanup-phase7`) intentionally narrowed `_research_context()` to bind + own-category extended attrs only. The Angela Murphy incident was primarily **prompt compliance** (employer ignored in search) — addressed in slice `2026-06-09-2000-research-prompt-bind-disambiguation`. This slice addresses the **remaining** part of `TODO.md` **Research prompt context enrichment**: peer specialist visibility.

**Read-only context:** `docs/architecture.md`, `TODO.md`, `src/agents/context.py` (`ContextBuilder.build_full_context`).

## How to start (mandatory)

Follow `prompts/cursor/WORKFLOW.md`:

1. **Claim** this file: move from `prompts/cursor/next/` to `prompts/cursor/in-progress/` before work.
2. Deliver under `prompts/cursor/done/2026-06-09-2010-research-prompt-full-peer-context/`.
3. **Do not commit or push** until Grok + Paul review.

**Ordering:** May run after or in parallel with `2026-06-09-2000-research-prompt-bind-disambiguation`. If both touch `src/tools/research.py`, merge carefully (bind slice owns disambiguation block; this slice owns context shape + peer guidance).

## Governance (mandatory)

- **Do not edit `TODO.md`.**
- In `output.md`, add **"For Grok + Paul"**: roadmap updates, suggested commit message.
- Cursor delivers: code, tests, `output.md` only.

## Scope boundaries (strict)

**You may modify:**

- `src/agents/factory/templates/specialist_agent.py.j2` — `_research_context()`
- `src/agents/specialists/*_specialist.py` — **regen all four framework fallback specialists** from the updated template (required; these are the checked-in fallbacks per slice `1605`)
- `src/tools/research.py` — only if needed to serialize/format peer context in `build_research_prompts` (e.g. separate JSON section, size limits)
- `src/agents/factory/templates/research/_system.j2` — short guidance on using `context.specialists` peer findings (do not duplicate bind-disambiguation rules from slice 2000)
- `tests/test_research.py` and/or `tests/test_specialist_sync_research.py`

**Out of scope:**

- `TODO.md`
- Cross-network / MCP changes
- Operator force re-research
- Changing which fields specialists may **write** (`target_fields` scoping unchanged)
- Loading peer data by re-reading all stores inside `_research_context` if `ctx["specialists"]` already carries peer slices from `build_full_context` — prefer using passed-in `ctx`

## Current behavior

`ContextBuilder.build_full_context()` already assembles:

```python
{
  "entity_id": "...",
  "bind": {"name": "...", "employer": "..."},
  "specialists": {
    "contact": {"<id>": {...}},
    "professional": {"<id>": {...}},
    ...
  }
}
```

Specialist nodes receive this full `ctx`, but `_research_context()` **drops** peer categories:

```python
return {
    "entity_id": entity_id,
    "bind": ctx.get("bind") ...,
    "storage": strip_bind_fields(own_category_record),
}
```

Research LLM never sees professional/social findings when relationships researches `spouse`.

## Implementation

### 1. Widen `_research_context()` in specialist template

File: `src/agents/factory/templates/specialist_agent.py.j2`

Include peer specialist slices for the same `entity_id`:

- Read `ctx.get("specialists")` (dict keyed by category).
- For each category **other than** `{{ category }}`, if `specialists[cat].get(entity_id)` exists, include stripped extended attrs (no bind fields) under a `specialists` key in the research context.
- Keep own-category data in `storage` as today (or document if you unify — prefer minimal change: `storage` = own, `specialists` = peers only).
- Empty/missing peers → omit key or `{}`; do not fail.

Example target shape:

```python
{
  "entity_id": "...",
  "bind": {"name": "...", "employer": "..."},
  "storage": { ... own category extended attrs ... },
  "specialists": {
    "professional": { "title": {...}, "linkedin": {...} },
    "social": { "linkedin_url": {...} }
  }
}
```

Use `strip_bind_fields` on peer records too. Only include categories with at least one field for this entity.

### 2. Regen framework specialists

After template change, regen all four files under `src/agents/specialists/` from `specialist_agent.py.j2` (same process as slice `2026-06-09-1605-entity-boundary-regen-framework-specialists`). CRM example specialists under `examples/networks/crm/specialists/` if they share the template — check project conventions; regen only what the prompt and factory docs require.

### 3. Research prompt presentation

File: `src/tools/research.py` — `build_research_prompts()`

Ensure peer `specialists` context is visible to the model:

- If `context.get("specialists")` is non-empty, add a brief plain-text header before JSON, e.g. `Peer specialist findings (read-only, use for disambiguation):` — or structure JSON so peers are not buried. Keep payload JSON for machine readability; a one-line human summary is enough if peers are in JSON.
- Optional: cap serialized peer context size (e.g. omit `pending` entries, truncate long values) to avoid blowing token budget — document policy in `output.md`.

### 4. System template hint

File: `src/agents/factory/templates/research/_system.j2`

Add 1–2 lines: when `context.specialists` contains peer findings, use them to disambiguate the person and inform search queries; peer data is read-only input, not fields to write unless in `target_fields`.

Do not re-implement bind-employer mandatory rules (slice 2000).

### 5. Smoke tests

Add `@pytest.mark.smoke` tests:

1. **`_research_context` shape** — unit-test the logic (extract to testable helper in template code path, or test via rendered specialist module / direct function import from a framework specialist after regen). Context with `specialists.professional[id]` and `specialists.social[id]` → research context includes both under `specialists`, excludes own category from peers, includes `storage` for own.
2. **`build_research_prompts` includes peers** — when context has non-empty `specialists`, user message JSON (or header) contains peer category keys.
3. **No peers** — empty `ctx["specialists"]` → research context has no `specialists` key or empty dict; existing tests still pass.

No live LLM/Tavily.

## Verification

```bash
uv run pytest tests/test_research.py tests/test_specialist_sync_research.py -m smoke -q
uv run ruff check src tests bin/
```

## Deliverables

Under `prompts/cursor/done/2026-06-09-2010-research-prompt-full-peer-context/`:

- `prompt.md`, `output.md` with **For Grok + Paul**:
  - Mark **Research prompt context enrichment** done in `TODO.md` (if bind slice 2000 also merged)
  - Note regen command used for framework specialists

## Exit criteria

- [ ] `_research_context` passes peer specialist slices into research `context`
- [ ] Framework `*_specialist.py` files regen'd from template
- [ ] `build_research_prompts` surfaces peer context to the LLM
- [ ] Smoke tests for peer inclusion / empty peers
- [ ] Ruff clean; no `TODO.md` edit by Cursor