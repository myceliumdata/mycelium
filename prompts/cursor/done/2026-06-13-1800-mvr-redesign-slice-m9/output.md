# MVR redesign — Slice M9 (CLI, MCP, admin, examples, README migration)

## Summary

Public surfaces now use the **target two-step protocol** (`id` or `lookup` → `delivery_id` → deliver). Legacy `entity_key` / `binding` / `--employer` are rejected at CLI, MCP, and admin entry points. Example query JSON, guides, READMEs, and introspection reflect the target runtime. Internal `EntityQuery(entity_key=…)` graph path remains for legacy-focused smoke tests only.

## Changes

| Area | Change |
|------|--------|
| **`src/main.py`** | CLI `query`: `--id`, `--lookup-json`, `--delivery-id`, `--attributes`, `--quote-id`, `--provenance`; legacy flags error with migration hint |
| **`src/mycelium_mcp/server.py`** | Target tool docs; `_parse_query_payload` rejects `entity_key`/`binding` without target fields; health ping uses two-step lookup |
| **`src/mycelium_admin/server.py`** | `AdminQueryRequest`: `id`, `lookup`, `delivery_id` (no `entity_key`/`binding`) |
| **`src/network/introspection.py`** | `protocol_status` → `"target two-step (id/lookup → delivery_id)"`; `key_field` → `lookup` |
| **`src/models/state.py`** | JSON schema examples + field descriptions for target protocol |
| **`examples/networks/*/queries/`** | Two-step fixtures: `crm` batch, `crm-metering` metering arc, `empty-crm` create-on-deliver |
| **`examples/networks/crm/guide.md`**, **`README.md`**, **`empty-crm/guide.md`**, **`empty-crm/README.md`**, **`crm-metering/README.md`** | Two-step walkthrough; `lookup_unresolved` wording |
| **`bin/demo-metering-negotiation`** | Resolve → quote → deliver |
| **`README.md`**, **`docs/architecture.md`**, **`docs/plans/mvr-best-practices.md`**, **`docs/plans/mvr-redesign-entity-query-examples.md`** | Target protocol docs |
| **`tests/test_mvr_target_public.py`** | **New** — CLI roundtrip, MCP legacy rejection, example JSON roundtrip |
| **Test migrations** | `test_cli_metering_query`, `test_admin_daemon`, `test_network_integration`, `test_mcp_onboarding`, `test_entity_rename`, `test_entity_payment` |

**Untouched:** polish backlog (M10), Program 2 versioned bind storage, `TODO.md`.

## Public gate behavior

| Entry | Legacy `entity_key` / `binding` | Target protocol |
|-------|--------------------------------|-----------------|
| CLI `query` | Error with migration message | `--lookup-json` / `--id` → `--delivery-id` |
| MCP `query_entity` | Rejected by `_parse_query_payload` | `lookup` / `id` → `delivery_id` (+ `quote_id` when metered) |
| Admin query API | Not accepted on request model | `lookup` / `id` → `delivery_id` |
| Internal graph smoke | `EntityQuery(entity_key=…)` still works | Used only where tests target legacy graph paths |

## Verification

```bash
./bin/ci-local
# uv sync OK · admin-ui build OK · ruff OK · 346 passed, 26 deselected
```

## For Grok + Paul

- **M9 complete** — CLI, MCP, admin, example JSON, README/guide migration (R10–R12 public surfaces).
- **M10 unblocked** — polish backlog (`mvr-redesign-polish-m10.md`).
- **TODO.md:** mark M9 done; queue M10.
- **Not committed** — awaiting review.

Suggested commit message:

```
feat: migrate CLI, MCP, and admin to target two-step MVR protocol (M9)

Replace entity_key/binding on public entry points with lookup/id and
delivery_id; migrate example fixtures and docs; gate legacy at CLI/MCP/admin.
```
