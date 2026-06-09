# Research prompts — context enrichment (MVR bind disambiguation + peer specialists)

## Objective

Complete **Research prompt context enrichment** in a **network-agnostic** way:

1. **MVR-driven bind disambiguation** — replace slice `2000`'s hardcoded `bind.employer` prompt logic with rules driven by `network.json` → `MvrPolicy.bind_fields`.
2. **Peer specialist context** — restore cross-category findings in research prompts (`context.specialists`).

**Why this supersedes `2000`:** Slice `2000` shipped employer-only conditionals in templates and `build_research_prompts()`. Paul flagged that as CRM-shaped. Grok reverted the hardcoded employer implementation on `main`; this slice implements the generalized pattern. CRM (default MVR `name` + `employer`) should still get employer-in-first-search behavior **as a consequence of MVR**, not a special case.

**Angela Murphy lesson:** Bind disambiguation fixes *search queries*; wrong *answer selection* (IMDB spouse despite Talentcare hit) needs peer context + generic “reject non-corroborating sources” guidance — not employer-in-snippet validation in Python.

**Read-only context:** `docs/architecture.md`, `TODO.md`, `src/network/mvr.py` (`load_mvr`, `MvrPolicy`), `src/agents/context.py` (`ContextBuilder.build_full_context`).

## How to start (mandatory)

Follow `prompts/cursor/WORKFLOW.md`:

1. **Claim** this file: move from `prompts/cursor/next/` to `prompts/cursor/in-progress/` before work.
2. Deliver under `prompts/cursor/done/2026-06-09-2010-research-prompt-context-enrichment/`.
3. **Do not commit or push** until Grok + Paul review.

## Governance (mandatory)

- **Do not edit `TODO.md`.**
- In `output.md`, add **"For Grok + Paul"**: roadmap updates, suggested commit message.
- Cursor delivers: code, tests, `output.md` only.

## Scope boundaries (strict)

**You may modify:**

- `src/tools/research.py` — `build_research_prompts`, bind-disambiguation helpers, optional `research_audit` bind snapshot, peer-context formatting
- `src/agents/factory/templates/research/_system.j2`
- `src/agents/factory/templates/research/_disambiguation.j2` (new — **MVR-generic**, not employer-only)
- `src/agents/factory/templates/research/*.md.j2` (minimal — prefer shared partials over per-category employer branches)
- `src/agents/factory/templates/specialist_agent.py.j2` — `_research_context()`
- `src/agents/specialists/*_specialist.py` — **regen all four framework fallback specialists**
- `tests/test_research.py` and/or `tests/test_specialist_sync_research.py`

**Out of scope:**

- `TODO.md`
- CRM-specific persistence validation (e.g. “employer must appear in source snippet”)
- Operator force re-research, admin UI
- Changing `target_fields` write scoping
- Re-reading all specialist stores inside `_research_context` when `ctx["specialists"]` is already populated

## Starting state

Slice `2000` employer hardcoding has been **reverted** on `main` after commit `9c88adb`:
- Research templates back to soft advisory `_system.j2`
- No `_disambiguation.j2`, no `bind_has_employer` Jinja vars
- `build_research_prompts()` does not load MVR

Implement the full design below from this baseline.

---

## Part A — MVR-driven bind disambiguation

### A1. Bind disambiguator extraction (Python)

In `src/tools/research.py`, add testable helpers:

```python
def bind_disambiguators(context: dict, mvr: MvrPolicy) -> dict[str, str]:
    """Non-empty bind values for fields declared in MVR bind_fields."""

def has_extra_bind_disambiguators(disambiguators: dict[str, str]) -> bool:
    """True when any non-name bind field has a value (triggers mandatory search rules)."""
```

Rules:

- Load MVR via `network.mvr.load_mvr()` inside `build_research_prompts()`.
- For each `field` in `mvr.bind_fields`, if `context["bind"][field]` is non-empty after strip, include in `bind_disambiguators`.
- `has_extra_bind_disambiguators` = any key other than `"name"` present. **Name-only bind → no mandatory disambiguation block** (same as pre-2000).
- Whitespace-only values → treat as absent.

Pass to Jinja: `bind_disambiguators` (dict), `has_extra_bind_disambiguators` (bool), `mvr_bind_fields` (list).

**Do not** hardcode `employer`, `bind_employer`, or `bind_has_employer`.

### A2. System template (`_system.j2`)

When `has_extra_bind_disambiguators`:

- FIRST `web_search` query MUST include tokens for **all non-name** bind disambiguators (field labels optional; values required).
- Do NOT run queries that omit those tokens when they are known.
- If results describe a person inconsistent with bind disambiguators, return `na` with reason.
- If no results corroborate bind disambiguators after reasonable attempts, return `na` — do not guess from weak homonym sources.

When only `name` (or no extra disambiguators): name-only search allowed.

Use generic language (“bind disambiguators”, “non-name bind fields”) — **never** “employer” unless iterating a field literally named employer in the dict.

### A3. User message disambiguation block (`_disambiguation.j2`)

When `has_extra_bind_disambiguators`, prepend **first** in user message:

```
DISAMBIGUATION (mandatory):
{% for field, value in bind_disambiguators.items() %}
- {{ field }}: {{ value }}
{% endfor %}
- Your FIRST web_search query MUST include all non-name bind values listed above.
- Reject sources that do not corroborate these bind values.
```

Loop over dict — works for CRM `employer`, future `account_id`, etc.

### A4. Category fragments

Avoid re-adding `{% if bind_has_employer %}` to all six files. Prefer **one** shared partial `research/_bind_search_hint.j2` included from `_system.j2` or a single line in disambiguation block.

Optional: `relationships.md.j2` may add **category-specific** homonym guidance (entertainment/genealogy weak for relationship claims) — that is category-scoped, not CRM-scoped.

### A5. Research audit

Add `context_bind` to `research_audit` entries: full `bind_disambiguators` dict (MVR-filtered), not hardcoded name+employer.

---

## Part B — Peer specialist context

### B1. Widen `_research_context()` in `specialist_agent.py.j2`

Specialist nodes receive full `ctx` from `build_full_context`. Include peer slices:

```python
{
  "entity_id": "...",
  "bind": {...},
  "storage": { ... own category extended attrs ... },
  "specialists": {
    "professional": { ... },
    "social": { ... }
  }
}
```

- Peers = categories other than `{{ category }}` with data for `entity_id`.
- Use `strip_bind_fields` on peer records.
- Omit empty `specialists` key.

### B2. Regen framework specialists

Regen all four `src/agents/specialists/*_specialist.py` from template (slice `1605` process).

### B3. Present peers in `build_research_prompts()`

When `context.get("specialists")` non-empty, ensure peers are visible (plain-text header before JSON and/or prominent JSON placement). Optional: omit `pending` peer fields; cap size — document in `output.md`.

### B4. System template peer hint

When peers present: use read-only peer findings to disambiguate the person and inform searches; do not write peer fields unless in `target_fields`.

---

## Part C — Smoke tests

`@pytest.mark.smoke` only; no live Tavily/LLM.

### Bind / MVR

1. **CRM default MVR + employer in bind** — disambiguation block lists `employer: Talentcare`; system mandates non-name tokens; user message starts with `DISAMBIGUATION`.
2. **Name-only bind** — `bind: {name: Jane}`, no employer → no disambiguation block; no mandatory non-name rules.
3. **Custom MVR** — monkeypatch `load_mvr` to return `bind_fields: ["name", "account_id"]` with `account_id` in bind → disambiguation mentions `account_id`, not employer.
4. **Whitespace bind value** — treated absent.

### Peer context

5. **`_research_context` / regen specialists** — peers included, own category excluded from `specialists`.
6. **`build_research_prompts`** — peer categories appear in user message when present.
7. **Empty peers** — no regression on existing tests.

### Audit

8. **`context_bind`** on audit entry matches `bind_disambiguators`.

---

## Verification

```bash
uv run pytest tests/test_research.py tests/test_specialist_sync_research.py -m smoke -q
uv run ruff check src tests bin/
```

**Manual (Paul):** After deploy + storage clear, Angela Murphy @ Talentcare + `spouse` — first query should include `Talentcare` via MVR, not employer special case. LangSmith user message: `DISAMBIGUATION` lists `employer: Talentcare`.

## Deliverables

`prompts/cursor/done/2026-06-09-2010-research-prompt-context-enrichment/`:

- `prompt.md`, `output.md` with **For Grok + Paul**:
  - Mark **Research prompt context enrichment** done (replaces split bind/peer TODO rows)
  - Note slice `2000` superseded by MVR-generalized approach
  - Regen command used

## Exit criteria

- [ ] Bind disambiguation driven by `MvrPolicy.bind_fields` — no hardcoded `employer` branches
- [ ] Peer `context.specialists` in research context and prompts
- [ ] Framework specialists regen'd
- [ ] Smoke tests: MVR CRM case, name-only, custom MVR, peers, audit
- [ ] Ruff clean; no `TODO.md` edit by Cursor