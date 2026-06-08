# Output: MCP slice 1 — public Entity vocabulary rename

## Summary

Renamed the **public query vocabulary** from person-centric to entity-neutral across CLI, MCP, models, graph state, responses, introspection, tests, and docs. No backward-compat aliases (`person_key`, `query_person`, `PersonQuery`, etc.) remain in `src/`, CLI, or MCP.

## Rename map (applied)

| Old | New |
|-----|-----|
| `Person` | `SeedRecord` |
| `PersonQuery` | `EntityQuery` |
| `person_key` | `entity_key` |
| `PersonResponse` | `QueryResponse` |
| `query_person` | `query_entity` |
| Graph: `person` / `persons` / `matched_persons` | `seed_record` / `seed_records` / `matched_records` |
| CLI: `--person-key` / `status --person` | `--entity-key` / `--entity` |
| MCP schemas | `seed-record`, `entity-query`, `query-response` |
| Introspection | `EntityFieldStatus`, `entity_key`, `entity_matches`, `entity_fields` |

## Files changed (primary)

| Area | Files |
|------|-------|
| Models | `src/models/state.py`, `src/models/__init__.py` |
| Graph / agents | `src/graphs/core.py`, `src/agents/{supervisor,dispatch,responses,routing,core_identity}.py`, `src/agents/factory/templates/specialist_agent.py.j2` |
| MCP | `src/mycelium_mcp/server.py` |
| CLI | `src/main.py` |
| Introspection | `src/network/introspection.py` |
| Storage (import fix) | `src/storage/core.py` |
| Tests | All `tests/*.py` + new `tests/test_entity_rename.py` |
| Docs | `README.md`, `docs/architecture.md`, `docs/full-code-walkthrough.md`, `examples/networks/crm/README.md` |
| Tracking | `TODO.md` (slice 1 note; MCP onboarding not marked complete) |

## Manual verification

```bash
uv run mycelium query --entity-key "Nichanan Kesonpat" --network-dir examples/networks/crm
# → QueryResponse JSON; debug contains entity_key='Nichanan Kesonpat'

uv run mycelium network status --entity "Andrea Kalmans" --network-dir examples/networks/crm
# → demo layout + "Entity lookup: 'Andrea Kalmans' (1 match(es))"
```

## Automated verification

```text
uv run pytest -m smoke -q tests/test_entity_rename.py  → 5 passed
uv run pytest -m smoke -q  → 129 passed (1 pre-existing langsmith env flake unrelated)
uv run ruff check src tests  → clean
```

## Unblocks

MCP slice 2 (`describe_network`, onboarding surface) and slice 3 (query-time message partition).
