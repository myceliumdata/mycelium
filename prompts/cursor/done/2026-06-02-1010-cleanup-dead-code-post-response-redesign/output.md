# Output: Clean up dead code post–PersonResponse redesign

## Audit summary

| Item | Status |
|------|--------|
| `DataRequest` model | Already removed (1912); confirmed absent from `src/` |
| Old `PersonResponse` fields (`status`, `person`, `data`, etc.) | Already removed from `src/` |
| Old status string literals in production code | None found |
| Enrich/validator graph nodes | **Kept** — active for ingest (post-1000); not dead |
| `route: "validator"` / `"finish"` in `MyceliumGraphState` | **Removed** — never used for conditional routing |

## Cleanup performed

### `src/models/state.py`
- `MyceliumGraphState.route` narrowed to `Literal["enrich"] | None` (dropped unused `"validator"` and `"finish"`).

### `src/agents/supervisor.py`
- Terminal returns use `route: None` instead of `route: "finish"` (clears stale `"enrich"` after validator).
- Debug key `deferred_attributes` → `non_core_requested` (avoids old response-field naming).

### `src/agents/enrich.py` / `validator.py`
- Error/audit wording: avoid “ingest” where agent only prepares; validator local `status` → `outcome`.

### `README.md`
- Quick-start examples use real seed name (`Nichanan Kesonpat`).
- Mermaid diagram updated for `results` / `message` model (no `data_request` / `specialist_required` status).
- Specialist section describes minimalist response fields.

### `src/mcp/server.py`
- Example `query_person` JSON uses current seed name.

### `docs/database-notes.md`
- Example query updated to match seed.

### `tests/test_core_graph.py`
- Assertion updated for `non_core_requested` debug key.

### `TODO.md`
- Marked dead-code cleanup complete.

## Intentionally not changed

- `prompts/cursor/done/**` — historical artifacts (out of scope).
- Graph structure (enrich → validator edges) — required for ingest.
- `list_specialist_routing` MCP tool name — still accurate.

## Verification

- `uv run pytest` — **6 passed**
- `uv run ruff check src tests` — clean
- `rg` on `src/` for `DataRequest`, `specialist_required`, `data_request`, `finish` route — no matches

## In-progress cleanup

Removed only `prompts/cursor/in-progress/2026-06-02-1010-cleanup-dead-code-post-response-redesign.md`.
