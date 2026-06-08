# Output: MCP slice 2 — onboarding surface

## Summary

Implemented **connect-time MCP onboarding**: author `guide.md`, `build_network_capabilities()` / `describe_network` tool, dynamic MCP instructions, and removal of `list_specialist_routing`.

## Files changed

| File | Change |
|------|--------|
| `examples/networks/crm/guide.md` | New — committed CRM author guide |
| `src/network/introspection.py` | `build_network_capabilities()`, `format_mcp_instructions()` |
| `src/mycelium_mcp/server.py` | `describe_network` tool; dynamic instructions; removed `list_specialist_routing` |
| `src/network/create.py` | Scaffold `guide.md` on create (option B) |
| `src/network/__init__.py` | Export new introspection helpers |
| `src/main.py` | Dry-run note about `guide.md` scaffolding |
| `examples/networks/crm/README.md` | `guide.md` in layout + operator note |
| `tests/test_mcp_onboarding.py` | New — 7 smoke tests |
| `tests/test_mcp_runtime_reload.py` | `describe_network` refresh test (replaces routing test) |
| `tests/test_example_network.py` | Assert `guide.md` in example layout |
| `tests/test_network_create.py` | Assert `guide.md` on happy-path create |
| `README.md`, `docs/architecture.md`, `docs/full-code-walkthrough.md` | MCP tool list |
| `TODO.md` | `list_specialist_routing` done; slice 2 noted |

## MCP tools (public)

| Tool | Purpose |
|------|---------|
| `describe_network` | Author guide + ontology + policy (connect time) |
| `query_entity` | Entity lookup / attribute research |
| `health_check` | Server liveness + network binding |

`list_specialist_routing` removed. `_routing_payload()` retained internally for `health_check` only.

## Sample `describe_network` keys

```json
{
  "network_name": "crm",
  "display_name": "CRM example",
  "guide_present": true,
  "guide": "# CRM example\n...",
  "ontology": { "present": true, "message": null, "categories": [...] },
  "policy": { "extensibility": "...", "out_of_scope": "...", "multi_match": "...", "query": {...} }
}
```

## Verification

```text
uv run pytest -m smoke -q tests/test_mcp_onboarding.py  → 7 passed
uv run pytest -m smoke -q  → 139 passed (1 pre-existing langsmith env flake)
uv run ruff check src tests  → clean
```

`refresh-example-network crm` copies `guide.md` automatically (not in `_SKIP_NAMES`).

## Unblocks

MCP slice 3 (`1500` — query-time message partition).
