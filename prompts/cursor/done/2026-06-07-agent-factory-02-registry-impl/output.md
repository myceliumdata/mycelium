# agent-factory-02-registry-impl — Output

## Claim

Moved `prompts/cursor/next/2026-06-07-agent-factory-02-registry-impl.md` → `in-progress/.../prompt.md` before implementation.

## Summary

Implemented full `AgentRegistry` per `docs/plans/agent-factory-phase2.md`:

- Pydantic models: `RegisteredAgent`, `AgentRegistryData`
- `_SEED_REGISTRY` matching committed `data/agent_registry.json`
- Atomic `_save` (tempfile + `os.replace`, same pattern as classification engine)
- `MYCELIUM_AGENT_REGISTRY_PATH` for registry path
- `has_agent`, `get_agent_fn`, `register_agent`, `list_agents`, `reload`
- `_load_agent_fn`: core_data special-case; generated agents via `MYCELIUM_SPECIALISTS_DIR` file spec + import fallback
- Singletons `get_agent_registry` / `reset_agent_registry`
- `tests/conftest.py`: `reset_agent_registry` in session cleanup
- Two smoke tests: seed + load fn; register persists to tmp
- Minor ruff fix: removed unused `CategoryProposals` imports in `test_supervisor_routing.py` (file already in scope)

No factory, dispatch wiring, supervisor, or graph changes.

## Verification

### Smoke

```
$ uv run pytest -m smoke -q
......................                                                   [100%]
22 passed, 9 deselected in 0.26s
```

### Ruff

```
All checks passed!
```

### Manual (MYCELIUM_AGENT_REGISTRY_PATH)

```
True
[{'name': 'core_data', 'category': 'core', ...}]
<function core_data_agent at 0x...>
```

### Scope

Only modified:
- `src/agents/registry.py`
- `tests/conftest.py`
- `tests/test_supervisor_routing.py`

## Ready for slice 03

`2026-06-07-agent-factory-03-base-specialist.md` — full `SpecialistStorage` implementation.
