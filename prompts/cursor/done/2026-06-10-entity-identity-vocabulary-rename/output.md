# Identity vocabulary rename (breaking)

## Summary

Renamed seed-era graph/MCP vocabulary to registry identity terms: `SeedRecord` → `IdentityRecord`, state fields `seed_record(s)` → `identity_record(s)`, MCP schema URI `mycelium://schema/identity-record`. No backward-compat aliases.

## State consolidation (Option A)

**Canonical:** `matched_records` (dict rows from registry resolution).

**Supervisor:** Stopped populating typed `identity_records` / `identity_record` on the happy path — dispatch and specialists read `matched_records` and `context.entity_id` / `context.bind` only.

**Specialist template:** Still sets `identity_record` (typed) when a single match is resolved, for LangGraph Studio visibility.

**Short-circuit context:** Replaced legacy `{"seed": []}` with `planner_context(matched=[], ...)` — no stale context keys.

**State fields retained:** `identity_record` / `identity_records` on `MyceliumGraphState` (renamed, not removed) for specialist/Studio typing; graph flow does not depend on them.

## Changes

| Area | Files |
|------|-------|
| **Models** | `src/models/state.py`, `src/models/__init__.py` |
| **Graph agents** | `src/agents/supervisor.py`, `routing.py`, `responses.py` |
| **Storage / legacy** | `src/storage/core.py`, `src/agents/person_prep.py` |
| **MCP** | `src/mycelium_mcp/server.py` (`identity_record_schema`, URI break) |
| **Graph export** | `src/graphs/core.py` |
| **Specialists** | `src/agents/factory/templates/specialist_agent.py.j2`, `examples/networks/crm/specialists/contact_specialist.py` |
| **Tests** | `tests/test_entity_rename.py`, `tests/test_query_response_outcomes.py` |
| **Docs** | `docs/architecture.md`, `docs/full-code-walkthrough.md` |

**Unchanged per spec:** `seed.json`, `--seed`, `import_seed_file`, introspection `source == "seed"` (bootstrap fixture semantics).

## Verification

```bash
uv run ruff check src tests                    # All checks passed
rg 'SeedRecord|seed_records|seed_record|schema/seed-record' src/ tests/   # no matches
LANGCHAIN_TRACING_V2=false uv run pytest -q   # 300 passed in 50.01s
```

LangSmith multipart ingest logged 429 after tests (quota); exit code 0, all tests green.

## For Grok + Paul

- **Breaking MCP URI:** clients using `mycelium://schema/seed-record` must switch to `mycelium://schema/identity-record`.
- **Breaking graph checkpoints:** old LangGraph threads may deserialize with missing `identity_record` / `identity_records` keys — use fresh `thread_id` for Studio sessions after upgrade.
- **Next in queue:** `prompts/cursor/next/2026-06-10-network-create-optional-seed.md` (depends on this slice).
- Suggested commit message in `prompt.md`.
