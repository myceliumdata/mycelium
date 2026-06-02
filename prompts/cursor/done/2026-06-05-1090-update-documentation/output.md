# Output: Update documentation (1090)

## Summary

Revised user-facing docs for **query-only public interface**, **`core_data_agent`**, and removal of public ingest. No source code changes.

## Files updated

| File | Changes |
|------|---------|
| `docs/architecture.md` | New "Public interface: query-only"; rewrote handshake → "Public query flow" + "Future work: re-adding data addition"; updated supervisor/core_data notes |
| `README.md` | Opening line, removed ingest example, Studio text, mermaid diagram, agents/MCP table, status |
| `docs/full-code-walkthrough.md` | Refreshed for June 2026 query-only state; historical ingest section; core_data_agent section |
| `TODO.md` | Ingest items → "Re-adding data addition"; marked 09xx/1000–1060 progress |

## Key statements (architecture.md)

> Public interface is query-only; core data lookups are owned by the **CoreDataAgent** specialist (`src/agents/core_data.py`), with graph wiring in progress.

## Verification

```bash
rg -i 'submit_person_data|provided_data' README.md docs/architecture.md docs/full-code-walkthrough.md TODO.md
# No matches in these primary docs (grep clean)
```

Legacy ingest references remain only in `prompts/cursor/done/` historical task artifacts (intentionally untouched).

## Follow-up

Tasks 1070/1100/1110 may require another doc pass once graph wiring lands.
