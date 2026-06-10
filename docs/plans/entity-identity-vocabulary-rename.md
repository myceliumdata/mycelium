# Identity vocabulary rename (breaking)

**Status:** Queued for Cursor (June 2026)  
**Trigger:** Post seed-elimination; Paul: “now is the time for breaking changes.”

## Goal

Remove seed-era **public and graph-state names** that still say `SeedRecord` / `seed_record(s)` while data is registry identity. Align with `matched_records` (already dict-shaped on state).

## Rename map

| Old | New |
|-----|-----|
| `SeedRecord` | `IdentityRecord` |
| `seed_record` (state field) | `identity_record` |
| `seed_records` (state field) | `identity_records` |
| `mycelium://schema/seed-record` | `mycelium://schema/identity-record` (drop old URI or document break) |
| `_seed_records_from_match` | `_identity_records_from_match` (supervisor; may already be partial) |
| `context` sub-key `'seed'` | `'identity'` |
| Docstrings / comments “seed match” | “registry match” |

**Keep:** `seed.json` filename, `--seed` on `network create`, `import_seed_file`, bootstrap “seed fixture” in operator docs.

**Do not confuse with:** `RegistryEntity` in `entity_registry.py` (persistence model).

## Consolidation note

`MyceliumGraphState` today has **both** `matched_records: list[dict]` and `seed_records: list[IdentityRecord]`. Prefer **one canonical representation**:

- **Option A (recommended):** Keep `matched_records` as canonical; drop `seed_records` / `identity_records` typed duplicates from state updates if nothing in graph reads them after specialist template migration.
- **Option B:** Keep typed `identity_records` for Studio typing; ensure supervisor sets one source of truth.

Cursor: audit readers; pick A unless typed fields required in Studio exports.

## Breaking surfaces

- LangGraph state JSON / checkpoints (old threads may deserialize with missing keys; acceptable in prototype)
- MCP schema resource URI
- `routing.py` `SupervisorDecision` fields
- Specialist Jinja template (`specialist_agent.py.j2`) and regenned specialists under examples if any reference old names
- Tests asserting `seed_records` in state

## Verify

```bash
uv run ruff check src tests
rg 'SeedRecord|seed_records|seed_record|schema/seed-record' src/ tests/ admin-ui/
LANGCHAIN_TRACING_V2=false uv run pytest -q
```

## Out of scope

- `network create` without `--seed` (separate slice)
- Renaming `seed.json` file or `--seed` flag