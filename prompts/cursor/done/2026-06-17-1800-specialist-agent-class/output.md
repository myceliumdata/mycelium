# SpecialistAgent class — route all I/O through instances

## Summary

Introduced **`SpecialistAgent`** (`src/agents/specialists/agent.py`) as the OO base for specialist autonomy. All four committed CRM specialists expose `AGENT = …Specialist()`; graph entrypoints delegate to `AGENT.run(state)`. Protocol dispatch resolves instances via `AgentRegistry.get_agent_instance()` and routes multi-bind writes through per-agent `write_fields` with rollback — not `handlers` directly.

## Key changes

| Area | Change |
|------|--------|
| `src/agents/specialists/agent.py` | `SpecialistAgent` with `write_fields`, `read_fields`, `bootstrap_entity`, `run`, `optimize_storage`, `analyze_storage`, `record_count`; `write_bind_fields_multi` via `_resolve_agent_for_write` |
| `src/agents/specialists/handlers.py` | Thin wrappers around `SpecialistAgent` (internal package only) |
| `src/agents/specialists/protocol.py` | `_call_handler` prefers agent methods; multi-bind imports `agent.write_bind_fields_multi`; analyze/read/status/ensure route through instances |
| `src/agents/registry.py` | `get_agent_instance(name)` — `AGENT` singleton, `get_agent()`, or default wrapper |
| CRM specialists + factory template | `class XSpecialist(SpecialistAgent)`, `AGENT`, module-level handler aliases |
| `tests/test_specialist_agent_class.py` | Subclass override, `optimize_storage` hook, handlers not used for multi-bind |
| `docs/architecture.md` | Short addendum on class-based specialists |

## Design notes

- **Storage rebinding:** `AGENT` singletons re-resolve `SpecialistStorage` when `MYCELIUM_AGENT_DATA_DIR` changes (test isolation).
- **Bootstrap:** `write_bind_fields_multi` imports committed specialist modules directly before touching `AgentRegistry` so seed bootstrap does not create `agent_registry.json` prematurely.

## Verification

```bash
./bin/ci-local
# CI local: all steps passed.
# 444 passed, 94 deselected
```

## For Grok + Paul

- **Enables next slice:** `2026-06-17-1900-specialist-minisql-v1` — `migrate_to("minisql_v1")` + `optimize_storage()` thresholds.
- Baseball bootstrap perf still needs entity batch save (separate from this slice).
- Suggested commit:

```
refactor(specialists): SpecialistAgent class; route all I/O through instances
```

- Do not commit from Cursor unless Paul asks.
