# Output — Research prompt context enrichment (`2010`)

## Summary

Replaced slice `2000`'s hardcoded employer logic with **MVR-driven** bind disambiguation (`MvrPolicy.bind_fields`) and restored **peer specialist context** in research prompts. CRM still gets employer-in-first-search behavior as a consequence of default MVR (`name` + `employer`), not a special case.

## Changes

| Area | Change |
|------|--------|
| `src/tools/research.py` | `bind_disambiguators()`, `has_extra_bind_disambiguators()`, `peer_specialists_for_entity()`; MVR-aware `build_research_prompts()`; `context_bind` audit |
| `research/_system.j2` | Conditional bind disambiguation + peer hint via shared partials |
| `research/_disambiguation.j2` | MVR-generic mandatory block (loops bind fields) |
| `research/_peer_context.j2` | Plain-text peer findings header (pending fields omitted) |
| `research/_bind_search_hint.j2` | Shared first-query mandate echo |
| `research/relationships.md.j2` | Category homonym guidance (entertainment/genealogy) |
| `specialist_agent.py.j2` | `_research_context()` includes peer `specialists` slices |
| `src/agents/specialists/*_specialist.py` | Regenerated (4 framework fallbacks) |

**Peer context policy:** Uses `ctx["specialists"]` when populated; omits `pending` peer fields; own category excluded. No re-read of all specialist stores.

**Regen command:**
```bash
uv run python -c "
from pathlib import Path
from agents.factory.agent_factory import AgentFactory
from agents.classification import get_category_tree
factory = AgentFactory(specialists_dir=Path('src/agents/specialists'))
tree = get_category_tree()
for category, agent_name in [
    ('contact', 'contact_specialist'),
    ('demographic', 'demographic_specialist'),
    ('professional', 'professional_specialist'),
    ('social', 'social_specialist'),
]:
    cat = tree._data.categories[category]
    factory.render_specialist_py(category=category, agent_name=agent_name,
        description=cat.description, examples=list(cat.examples))
"
```

## Tests

```bash
uv run pytest tests/test_research.py tests/test_specialist_sync_research.py -m smoke -q   # 23 passed
```

New coverage: CRM MVR + employer, name-only bind, custom MVR `account_id`, whitespace bind, peer specialists in prompts, `_research_context` peers, audit `context_bind`.

## For Grok + Paul

- **Manual verify:** Angela Murphy @ Talentcare + `spouse` — first `web_search` should include `Talentcare` via MVR (not employer special-case).
- **TODO.md:** Mark **Research prompt context enrichment** done; note slice `2000` superseded by this MVR-generalized approach.
- **Suggested commit message:** `feat(research): MVR bind disambiguation and peer specialist context in prompts`

## Exit criteria

- [x] Bind disambiguation driven by `MvrPolicy.bind_fields` — no hardcoded employer branches
- [x] Peer `context.specialists` in research context and prompts
- [x] Framework specialists regen'd
- [x] Smoke tests: MVR CRM case, name-only, custom MVR, peers, audit
- [x] Ruff clean; no `TODO.md` edit
