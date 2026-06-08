# MCP slice 3 — query-time messages

## Summary

Refactored `QueryResponse.message` to be classification-aware with attribute buckets (**found**, **researching**, **unavailable**, **out_of_scope**). Visiting agents get per-attribute status using ontology category names (not specialist module names).

## Changes

| Area | What changed |
|------|----------------|
| `src/agents/responses.py` | Added `partition_attribute_buckets()`, `build_query_message()`; refactored `response_assembled`, `response_non_core`, `response_not_found` |
| `src/agents/dispatch.py` | Unified `assemble_response_node` through `response_assembled` + `build_query_message` (removed `response_non_core` branch) |
| `tests/test_query_messages.py` | New smoke tests: out-of-scope only, mixed, multi-match Kevin Zhang, not found |
| `tests/test_core_graph.py` | Updated message assertions |
| `tests/test_supervisor_routing.py` | Updated non-core routing assertion |
| `tests/test_specialist_research_integration.py` | Updated pending-email assertion |
| `docs/architecture.md` | Message contract note |
| `TODO.md` | MCP onboarding slices 1–3 marked done |

## Message examples

**Out of scope only** (`xyzzy_garbage`):

```
Found record for Test User. xyzzy_garbage could not be classified into this network's ontology — it does not appear related to this network.
```

**Mixed** (`email` + nonsense):

```
Found record for Test User. Classified email as contact — setting up a contact specialist to research it. xyzzy_garbage could not be classified into this network's ontology — it does not appear related to this network.
```

**Multi-match** (`Kevin Zhang` + `email`):

```
Found 2 records for 'Kevin Zhang'. Classified email as contact — setting up a contact specialist to research it.
```

**Not found**:

```
No record found for 'NoSuchEntity-xyz'.
```

**Found value** (mocked research): values appear in `results` only; message omits the email value.

## Debug buckets

`response.debug` now includes explicit lists, e.g.:

```
found=['email']; researching=[]; unavailable=[]; out_of_scope=['xyzzy_garbage']
```

## Verification

```bash
uv run pytest -m smoke -q tests/test_query_messages.py tests/test_core_graph.py
uv run ruff check src tests
```

Full smoke: **143 passed** (1 pre-existing flake: `test_langsmith_utils.py::test_custom_ui_base`).

Manual CLI (`mycelium query --entity-key "Nichanan Kesonpat" --attributes email`) requires a configured network root; use `refresh-example-network crm` first. MCP `query_entity` equivalent after MCP restart.

## Deferred (out of scope)

- Per-record multi-match messages
- Specialist-local `message` overrides on non-graph paths (template still uses legacy copy internally)
- `describe_network` / entity rename

## Next

MCP slice 4 polish (`TODO.md`); Paul MCP restart verify recommended.
