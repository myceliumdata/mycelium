# Task 1110 output — Final cleanup and verification

## Statement

**Project is now query-only public interface with core data managed by the CoreDataAgent.**

Active graph: `START → supervisor (route="core_data") → core_data_agent (lookup + PersonResponse) → END`.

## Final cleanups

| Area | Action |
|------|--------|
| `tmp/` | Removed misleading ingest artifacts (`ingest-example.json`, `studio-correct-input.json`, `studio-add-person-guide.md`). Rewrote `studio-inputs.md`, `studio-input-guide.md`; added `tmp/README.md`. |
| `src/agents/enrich.py`, `validator.py`, `person_prep.py` | Marked as **unwired legacy** in module docstrings (files retained for future internal addition). |
| `TODO.md` | Marked graph wiring (`1070`, `1100`) complete; updated last-updated date. |
| `prompts/resets/2026-06-02b_mvp_reset.md` | Success criteria checked; next objective points to new `next/` work. |
| `src/`, `tests/`, `README.md`, `docs/` | No stray public ingest wiring; docs already query-only from 1090. Tests keep negative `ingest`/`provided_data` asserts in not-found test only. |

## Grep summary (active code)

- `src/`: ingest language only in unwired legacy modules (`enrich.py` still references old `provided_data` internally — not on public path).
- `tests/`: intentional regression guards in `test_supervisor_routing.py`.
- `docs/`: historical/negative references only (appropriate).

## Verification

### `uv run ruff check src tests`

```
All checks passed!
```

### `uv run pytest -q`

```
22 passed in 0.36s
```

### CLI smoke

```bash
uv run mycelium query --person-key "Nichanan Kesonpat"
```

Result: found `person-0001`, message `Found core record for Nichanan Kesonpat.`, `outcome='found'`. (LangSmith upload warnings in sandbox — query succeeded.)

### MCP

- Source: `mycelium_mcp/server.py` defines `query_person` and imports `run_query` from `graphs.core` (query-only instructions).
- Full `from mycelium_mcp.server import query_person` triggers eager `get_core_graph()` and can block >60s when checkpoint DB is contended (parallel dev/CLI processes). Graph path is covered by `test_graph_invokes_supervisor_then_core_data` and CLI smoke above.

### Graph path

- `tests/test_core_graph.py::test_graph_invokes_supervisor_then_core_data`
- `tests/test_supervisor_routing.py::test_supervisor_agent_routes_to_core_data`

## Migration state (1000–1110)

| Task range | Outcome |
|------------|---------|
| 1000–1050 | Public `PersonQuery`, CLI, MCP, routing, supervisor — query-only |
| 1060 | `core_data_agent` module |
| 1070, 1100 | Graph wired; `agents.__init__` exports supervisor + core_data only |
| 1080 | Tests aligned |
| 1090 | Docs aligned |
| 1110 | Final sweep + verification |

## Future work (internal data addition)

Per `docs/architecture.md` and `TODO.md` § Re-adding data addition:

- Design internal coordination (no `provided_data` on public `PersonQuery`).
- Persist path on `core_data_agent` or successor specialist.
- Re-wire or replace legacy enrich/validator/person_prep when design is approved.
- Stronger validation and specialist/enrichment triggers TBD.

Legacy files on disk, not imported: `enrich.py`, `validator.py`, `person_prep.py`.
