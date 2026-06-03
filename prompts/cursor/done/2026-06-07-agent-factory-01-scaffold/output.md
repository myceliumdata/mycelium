# agent-factory-01-scaffold — Output

## Claim

Moved `prompts/cursor/next/2026-06-07-agent-factory-01-scaffold.md` → `in-progress/2026-06-07-agent-factory-01-scaffold/prompt.md` before any edits (2026-05-31).

## Summary

Step 1 of Agent Factory Phase 2: pure scaffold with zero behavior change to existing runtime paths.

- Added `jinja2` via `uv add jinja2` (pyproject.toml + uv.lock).
- Created committed `data/agent_registry.json` with exact seed (version 1.0, single `core_data` entry).
- Scaffolded stubs: `registry.py`, `dispatch.py`, `factory/` (agent_factory + placeholder `.j2`), `specialists/` (base + `SpecialistStorage` stub).
- No wiring to supervisor/graph; `dispatch` stub delegates to `core_data_agent` only if imported (not used by graph yet).
- Removed unused `Path` imports in stubs for clean ruff (prompt stubs listed Path for slice-02 TODO context).

## Files created/modified (slice scope only)

| Path | Action |
|------|--------|
| `pyproject.toml`, `uv.lock` | `uv add jinja2` |
| `data/agent_registry.json` | New seed |
| `src/agents/registry.py` | Stub registry |
| `src/agents/dispatch.py` | Stub dispatcher |
| `src/agents/factory/__init__.py` | Package marker |
| `src/agents/factory/agent_factory.py` | Stub factory |
| `src/agents/factory/templates/specialist_agent.py.j2` | Placeholder template |
| `src/agents/specialists/__init__.py` | Package export |
| `src/agents/specialists/base.py` | `SpecialistStorage` stub |

## Verification

### Smoke

```
$ uv run pytest -m smoke -q
....................                                                     [100%]
20 passed, 9 deselected in 0.25s
```

### Ruff (new modules)

```
All checks passed!
```

### Import matrix

```
jinja2 version: 3.1.6
['core_data']
registry seed ok
has core_data: True
list: [{'name': 'core_data', 'category': 'core'}]
core_data fn callable: True
factory stub: {'created': False, 'reason': 'stub - implemented in slice 04'}
dispatch stub ok
base stub ok
```

### Structure

- `src/agents/factory/templates/specialist_agent.py.j2` present
- `data/agents/` absent (expected — no real creation yet)

### Dependency diff

```
 pyproject.toml |  1 +
 uv.lock        | 77 ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
 2 files changed, 78 insertions(+)
```

## Scope confirmation

- No changes to supervisor, graphs, core_data, classification, tests, docs, or existing behavior.
- No `data/agents/` directories or generated specialist `.py` files.
- No registry persistence logic, jinja rendering, git commit, or graph wiring.

## Ready for slice 02

`2026-06-07-agent-factory-02-registry-impl.md` — full `AgentRegistry` with `_SEED_REGISTRY`, atomic load/save, `MYCELIUM_AGENT_REGISTRY_PATH`, singletons.
