# MCP slice 4 — onboarding polish

## Summary

Closed non-blocking nits from MCP onboarding slices 1–3. No new MCP tools or message-bucket logic changes.

## Changes

| Area | What changed |
|------|----------------|
| `tests/test_langsmith_utils.py` | `test_custom_ui_base` clears LangSmith API env so scoped URL resolve does not override custom UI base |
| `tests/test_specialist_research_integration.py` | Positive asserts: `found=['email']`, `unavailable=['email']`, `not found for this record` |
| `src/agents/factory/templates/specialist_agent.py.j2` | Removed `model_copy` message overrides; specialists use `response_found` / `response_non_core` only |
| `examples/networks/crm/specialists/contact_specialist.py` | Aligned reference copy with template |
| `tests/test_agent_factory.py`, `tests/test_specialist_sync_research.py` | Updated for classification-aware specialist messages |
| `tests/test_specialist_entity_vocab.py` | Added CRM reference specialist vocab smoke test |
| `src/agents/seed.py`, `src/storage/core.py` | `find_by_key` / `find_persons` param renamed to `entity_key` (internal) |
| `src/mycelium_mcp/server.py` | `_neutral_json_schema` model descriptions for MCP schema resources |
| `TODO.md`, `prompts/system/PROJECT_BRIEF.md`, `docs/plans/networks-terminology.md` | Stale `PersonQuery` / `query_person` vocabulary sweep |
| `examples/networks/crm/README.md` | Documents reference `specialists/contact_specialist.py` decision |

## Decisions

### CRM `specialists/` directory

**Committed** `examples/networks/crm/specialists/contact_specialist.py` as a **reference copy** of factory output (inspection / docs). `refresh-example-network` does **not** copy `specialists/`; live networks generate specialists on first query. `__pycache__` remains gitignored globally.

### Framework `src/agents/specialists/*_specialist.py`

Still gitignored (runtime-generated). Regenerate locally after template changes:

```bash
MYCELIUM_SPECIALISTS_DIR=src/agents/specialists \
MYCELIUM_AGENT_REGISTRY_PATH=~/mycelium-networks/crm/agent_registry.json \
MYCELIUM_CATEGORIES_PATH=~/mycelium-networks/crm/categories.json \
uv run python -c "from agents.factory.agent_factory import get_agent_factory; get_agent_factory().regenerate_specialists_from_registry()"
```

Also render `demographic_specialist` / `professional_specialist` from `docs/examples/sample-categories.json` if not yet in registry. CRM example reference + factory template are canonical sources.

### `src/mycelium.egg-info/PKG-INFO`

Already in `.gitignore`; regenerated on `uv sync` / editable install. No action required.

### Specialist-isolated `message` vs graph `assemble_response`

Specialist nodes no longer override messages with legacy `(via …)` copy. **Graph `assemble_response` remains authoritative** for CLI/MCP; specialist-isolated responses may show generic `researching` until merge (by design).

## Verification

```bash
uv run pytest -m smoke -q   # 146 passed
uv run ruff check src tests # clean
```

`test_custom_ui_base` passes without LangSmith UI env vars.

## MCP onboarding status

Slices 1–4 complete. `TODO.md` marks **MCP onboarding for visiting agents** fully closed.

## Deferred (unchanged)

- Fuzzy entity_key matching
- Per-record multi-match messages
- Admin daemon / demo UI slices
