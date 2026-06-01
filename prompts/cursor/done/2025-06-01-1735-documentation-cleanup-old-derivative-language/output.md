# Output: Documentation cleanup (derivative language)

## Files modified

| File | Change |
|------|--------|
| `README.md` | Supervisor architecture, specialist_required flow, updated MCP tool names |
| `src/mcp/server.py` | MCP instructions and `list_specialist_routing` docstring/message text |
| `src/agents/supervisor.py` | Docstring bullet (conceptual only) |
| `TODO.md` | Marked doc-cleanup item complete |

## Before / after examples

1. **README intro** — *Before:* "orchestrator routes … derivative dataset stubs." *After:* "supervisor coordinates … specialist handoff for non-core attributes."

2. **Quick start** — *Before:* "Request derivative attributes (stub dataset created)." *After:* "Request non-core attributes (supervisor returns specialist_required)."

3. **Mermaid** — *Before:* `Orchestrator` → `derivative_pending`. *After:* `Supervisor` → `specialist_required`.

4. **README section** — *Before:* "Derivative datasets (Phase 1 stub)" with `derivative_datasets` table steps. *After:* "Specialist routing (Phase 1)" with `specialist_required` / `deferred_attributes`.

5. **MCP** — *Before:* "No derivative dataset registry exists in Phase 1." *After:* "Phase 1 does not persist a specialist registry in core storage." (JSON shape unchanged: `datasets: []`.)

## Left as-is (intentional)

- `docs/phase-1-direction.md` — Section 4 discusses derivative data as a **rejected** pattern; that is current direction, not outdated marketing copy.
- `prompts/done/**` — historical records (out of scope).
- `TODO.md` catch-up bullets referencing removed types — they document completed migration work.

## TODO.md

Added and checked: remove outdated derivative-dataset language (`2025-06-01-1735-documentation-cleanup-old-derivative-language`).

## In-progress cleanup

Removed only `prompts/in-progress/2025-06-01-1735-documentation-cleanup-old-derivative-language.md`.
