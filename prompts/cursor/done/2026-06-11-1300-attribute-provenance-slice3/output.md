# Program 1 — Attribute provenance Slice 3

## Summary

When `EntityQuery.provenance=true`, `QueryResponse` now includes structured version history for requested extended attributes. Default flat `results[]` is unchanged. MCP schema and `describe_network` capabilities document the response shape.

## Changes

| Area | Change |
|------|--------|
| **Model** | `QueryResponse.provenance: dict[str, Any] \| None` in `src/models/state.py` |
| **Builder** | New `src/agents/query_provenance.py` — loads specialist storage via `attr_sources` / category map; copies `current_version_id` + `versions[]`; skips bind fields; uses `MYCELIUM_AGENT_DATA_DIR` at runtime |
| **Dispatch** | `assemble_response_node` attaches provenance on `assembled`, `found`, and research-gated paths when request flag is set |
| **MCP** | `_neutral_json_schema(QueryResponse)` documents `provenance` |
| **Introspection** | `build_network_capabilities` adds `policy.query.response_provenance` with example JSON; `format_mcp_instructions` mentions response provenance |
| **Tests** | New `tests/test_query_provenance.py` (6 smoke); schema/onboarding asserts updated |
| **Docs** | `docs/architecture.md` — `QueryResponse.provenance` block; request vs response flag clarified |

**Untouched:** operator write endpoints, MVR / Program 2, flat `results[]` default shape, metering gate logic (existing `query_provenance` meter tests pass).

## Verification

```bash
./bin/ci-local
# uv sync OK · admin-ui build OK · ruff OK · 292 smoke passed, 26 deselected

uv run pytest tests/test_query_provenance.py -q
# 6 passed

uv run pytest tests/test_entity_metering.py::test_provenance_meter_on_quote -q
# 1 passed
```

**Manual check (post-review):** CRM query Paul Murphy `linkedin` with CLI `--provenance` should show `provenance.entities[].attributes.linkedin.versions` in JSON output.

## For Grok + Paul

- **Slice 3 complete** — metering promise fulfilled: `provenance=true` on request populates `QueryResponse.provenance` with versioned specialist storage for extended attrs.
- **Polish slice P unblocked** (`2026-06-11-1400-attribute-provenance-program1-polish.md`).
- **Program 1 closeout** after polish review.
- **Not committed** — awaiting review.

Suggested commit message:

```
feat: QueryResponse provenance when EntityQuery.provenance=true (Program 1 slice 3)

Add query_provenance builder wired from assemble_response; document response
shape in MCP schema, describe_network, and architecture.md.
```
