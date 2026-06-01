# Output: Rename orchestrator to supervisor

## Files renamed or modified

| Path | Change |
|------|--------|
| `src/agents/orchestrator.py` | **Deleted** (replaced by `supervisor.py`) |
| `src/agents/supervisor.py` | `supervisor_agent`, Supervisor log prefixes |
| `src/agents/__init__.py` | Import/export `supervisor_agent` |
| `src/agents/enrich.py` | Import from `agents.supervisor` |
| `src/graphs/core.py` | Node `supervisor`, `_route_after_supervisor` |
| `TODO.md` | Rename item marked complete |

## Intentional remaining "orchestrator" mentions

- `prompts/done/**` — historical task artifacts (out of scope)
- Prior conversation summaries referencing old filenames

## Verification

- `rg -i orchestrator src tests` — no matches in application code
- `uv run pytest` — 4 passed
- `uv run ruff check src tests` — clean

## TODO.md

Item **Rename `orchestrator_agent` / related files to `supervisor`** marked `[x]` with reference to `2025-06-01-1730-rename-orchestrator-to-supervisor`.

## In-progress cleanup

Removed only `prompts/in-progress/2025-06-01-1730-rename-orchestrator-to-supervisor.md` (this task).
