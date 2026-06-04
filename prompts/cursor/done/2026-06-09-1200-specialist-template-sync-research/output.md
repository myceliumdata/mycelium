# specialist-template-sync-research (slice 1200) — Output

## Claim

Moved `prompts/cursor/next/2026-06-04-1200-specialist-template-sync-research.md` → `prompts/cursor/in-progress/2026-06-09-1200-specialist-template-sync-research/prompt.md`.

**Depends on:** `prompts/cursor/done/2026-06-09-1100-specialist-research-runner/` (complete).

## Summary

Wired **synchronous** Phase 1 research into the specialist Jinja template and regenerated all six committed specialists.

### Template (`specialist_agent.py.j2`)

- Removed `threading` / daemon `_stub_background_research` / `_start_research_if_needed`.
- Added `_run_field_research(...)` → `tools.research.run_field_research` when `is_research_available()`; otherwise `_mark_fields_pending`.
- `_evaluate_owned_fields` batches cache misses, runs research once per invocation, reloads storage, then builds `values` from `found` / `na` / `pending`.
- Module docstring updated: Phase 1 sync research; async deferred.

### Factory (`agent_factory.py`)

- `render_specialist_py(...)` — render + write without registry registration.
- `regenerate_specialists_from_registry()` — re-render all `is_generated` agents from `data/agent_registry.json` + `data/categories.json` examples.
- `create_specialist` now delegates rendering to `render_specialist_py`.

### Regenerated modules

All six under `src/agents/specialists/`:

- `contact_specialist`, `social_specialist`, `relationships_specialist`, `demographic_specialist`, `professional_specialist`, `financial_specialist`

`AUTO-GENERATED` headers retained; `created_at` timestamps updated to regen time.

Regen command used:

```bash
uv run python -c "from agents.factory.agent_factory import get_agent_factory; get_agent_factory().regenerate_specialists_from_registry()"
```

## Tests

- `tests/test_specialist_sync_research.py` (new):
  - `test_contact_email_sync_research_persists_found_not_pending` — mocks `run_field_research`; proves **contact + email** → `found` contrib, not stuck `pending`.
  - `test_regenerated_contact_specialist_has_no_threading` — no threading/stub in generated source.

## Verification

### Smoke

```
$ uv run pytest -m smoke -q tests/test_research.py tests/test_agent_factory.py tests/test_specialist_sync_research.py
.............                                                            [100%]
13 passed in 0.45s
```

### Ruff

```
$ uv run ruff check src/agents/factory src/agents/specialists src/tools/research.py tests/...
All checks passed!
```

### Grep

- No `threading.Thread` in `src/agents/specialists/*_specialist.py`
- No `langchain_tavily` / `TavilySearch` in specialists

## Next queue item

`2026-06-04-1300-specialist-research-integration.md` (graph/MCP integration — out of scope for 1200).
