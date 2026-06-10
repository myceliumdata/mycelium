# Seed elimination — Polish (vocabulary + code nits)

## Summary

Closed review nit backlog from Slices 16–18: operator strings, registry API, context param rename, docs, and new **`empty-crm`** example. No Pydantic field renames (`SeedRecord`, `seed_records` state fields deferred per spec).

## Changes

| Area | Files |
|------|-------|
| **P1 CLI/MCP** | `src/main.py`, `src/mycelium_mcp/server.py`, `src/network/introspection.py` (policy strings) |
| **P2 docstrings** | `src/models/state.py`, `src/graphs/core.py`, `src/agents/dispatch.py`, `src/agents/supervisor.py` |
| **P3 registry API** | `src/agents/entity_registry.py` (`list_entities`), `src/agents/entity_resolution.py` |
| **P4 context param** | `src/agents/context.py` (`matched_records=`), `src/agents/dispatch.py`, `tests/test_entity_boundary.py` |
| **P5 docs** | `docs/full-code-walkthrough.md`, `docs/database-notes.md`, `prompts/system/CORE_PROMPT.md`, `prompts/system/PROJECT_BRIEF.md` |
| **P6/P7 examples** | `examples/networks/crm/README.md`, `examples/networks/crm-metering/guide.md`, new `examples/networks/empty-crm/` |
| **P7 test** | `tests/test_example_network.py::test_refresh_empty_crm_has_no_seed_or_entities` |
| **README** | Demo status line, how-it-works, empty-crm table row |

### Supervisor renames (internal)

- `_identity_records_from_seed` → `_identity_records_from_match`
- `_seed_records_from_match` (was `_seed_records_from_seed`)

State field names `seed_record` / `seed_records` unchanged (LangGraph compatibility).

### P8 — Admin dist + PKG-INFO

- `cd admin-ui && npm run build` — **success** (Entities-only `App.tsx` compiles; dist not committed per convention)
- `uv pip install -e .` — run; `PKG-INFO` has no `seed_people_count` (README long description may not mirror curl examples in metadata)

## Verification

```bash
uv run ruff check src tests                    # All checks passed
uv run pytest tests/test_example_network.py -m smoke -q   # 18 passed
uv run pytest -m smoke -q                        # 272 passed (prior run in batch)
LANGCHAIN_TRACING_V2=false uv run pytest -q      # 299 passed in 38.70s
```

Grep clean (no runtime-loader matches):

```bash
rg 'agents\.seed|get_seed_data|find_by_key|seed_people_count' \
  src/ tests/ admin-ui/src/ docs/full-code-walkthrough.md docs/database-notes.md prompts/system/
```

**Note:** One full-suite run without `LANGCHAIN_TRACING_V2=false` hit 2 environmental failures (OpenAI proxy / LangSmith); re-run of those tests passed. Recommend `LANGCHAIN_TRACING_V2=false` for local full pytest when LangSmith quota/proxy is constrained.

## Deferred (per spec)

- `SeedRecord` / `seed_records` / `seed_record` Pydantic field renames (breaking schema)
- `network create` without `--seed` (v2 track)
- Committing `admin-ui/dist/`

## For Grok + Paul

- Polish complete — safe to **batch commit** Slices 17 + 18 + polish together
- Check off on `TODO.md`: **Empty-seed network demo**, **Slices 14–18**, seed-elimination phase exit criteria in `entity-seed-elimination-phase.md`
- New example: `./bin/refresh-example-network empty-crm` — Paul Murphy bind arc via `queries/01-bind-paul-murphy.json`
- Rebuild admin SPA locally before `--demo` if using built dist (`admin-ui/dist/` gitignored)
- Suggested commit message:

```
Polish seed-elimination vocabulary, empty-crm, and review nits.

CLI/MCP/docstrings; list_entities; matched_records param;
empty-crm example; admin dist build verified.
```

- **Did not edit `TODO.md`** (per governance)
