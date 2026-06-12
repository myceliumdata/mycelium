# Program 1 — Attribute provenance Slice 2

## Summary

All read paths now use `specialist_fields` helpers. Framework specialists regenerated from the updated Jinja template. Introspection and admin UI expose full `versions[]` per extended field on entity drill-down. Flat v1 field blobs fail loud on introspection read.

## Changes

| Area | Change |
|------|--------|
| **Template** | `src/agents/factory/templates/specialist_agent.py.j2` — `specialist_fields` imports; versioned pending mark |
| **Specialists** | Regenerated `contact`, `demographic`, `professional`, `social` under `src/agents/specialists/` |
| **Introspection** | `EntityFieldStatus.versions`; `_entity_field_statuses` + `_analyze_storage` use versioned helpers |
| **Admin UI** | `types.ts` + `App.tsx` — expandable version history per extended field |
| **Tests** | Versioned fixtures in `test_network_status.py`, `test_admin_daemon.py`; versioned pending asserts elsewhere |
| **Docs** | `docs/architecture.md` — admin/status version history note |

**Untouched:** `QueryResponse.provenance`, `research.py` write path, `entities.json` / MVR / `bind_index`.

## Specialist regen command

```bash
cd /path/to/mycelium
uv run python -c "
import json
from pathlib import Path
from agents.factory.agent_factory import AgentFactory

root = Path('.')
cats_path = root / 'docs/examples/sample-categories.json'
cat_doc = json.loads(cats_path.read_text(encoding='utf-8'))
categories = cat_doc.get('categories', {})
specs = [
    ('contact', 'contact_specialist'),
    ('demographic', 'demographic_specialist'),
    ('professional', 'professional_specialist'),
    ('social', 'social_specialist'),
]
factory = AgentFactory(registry=object(), specialists_dir=root / 'src/agents/specialists')
for category, agent_name in specs:
    meta = categories.get(category, {})
    factory.render_specialist_py(
        category=category,
        agent_name=agent_name,
        description=meta.get('description', ''),
        examples=meta.get('examples') or [],
    )
"
```

## Verification

```bash
./bin/ci-local
# uv sync OK · admin-ui build OK · ruff OK · 286 smoke passed, 26 deselected

LANGCHAIN_TRACING_V2=false uv run pytest -q
# 312 passed in 36.93s
```

## For Grok + Paul

- **Slice 2 complete** — read path + admin version history; framework specialists canonical from jinja (replaces Slice 1 hand-bridge).
- **Operator:** flat v1 storage on entity drill-down raises clear error — refresh network or delete `agents/<category>/storage.json`.
- **Slice 3 unblocked** — `QueryResponse.provenance` + MCP schema (`2026-06-11-1300-attribute-provenance-slice3.md` already queued).
- **Not committed** — awaiting review.

Suggested commit message:

```
feat: versioned provenance read path and admin version history (Program 1 slice 2)

Regen framework specialists from jinja; introspection exposes versions[];
admin UI expandable field history.
```
