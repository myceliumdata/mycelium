# Entity outcome infrastructure — Phase 2 spec (draft)

**Status:** Locked (Paul, June 2026) — backend only; admin deferred to [`admin-ui-backlog.md`](admin-ui-backlog.md)  
**Program:** [`entity-protocol-and-registry-program.md`](entity-protocol-and-registry-program.md)  
**Depends on:** Slice 1 (`entity-key-suggestions-phase1.md`)  
**Cursor slice:** TBD after Paul approves batch 1

---

## Problem

Slice 1 adds `outcome` and `suggestions` on `QueryResponse`. Other response paths may omit or mismatch public `outcome` vs `debug`. MCP exposes JSON Schema via `mycelium://schema/query-response` — must reflect new fields. Visiting agents rely on stable machine-readable outcomes across all query results.

---

## Objective

Harden **outcome consistency** across every query exit path. No new negotiation logic.

---

## Scope

### In scope

| Area | Work |
|------|------|
| `src/agents/responses.py` | Every `response_*` builder sets public `outcome` matching `debug` |
| `src/models/state.py` | Field descriptions; ensure `EntityKeySuggestion` / `suggestions` documented |
| `src/mycelium_mcp/server.py` | Schema resources pick up new fields automatically via pydantic — verify + document |
| `src/network/introspection.py` | `policy` mentions `outcome` field on all responses |
| `tests/` | Snapshot or table-driven tests: each outcome type produces valid JSON with `outcome` set |
| `README.md` | One paragraph: `outcome` + `suggestions` on CLI/MCP JSON |

### Out of scope

- `entity_unknown`, registry, `binding`, admin UI (see [`admin-ui-backlog.md`](admin-ui-backlog.md))
- Changing message text except where `outcome` was missing

---

## Outcome coverage checklist

After Slice 1 + 2, every `QueryResponse` from `run_query` must set `outcome`:

| Builder / path | `outcome` |
|----------------|-----------|
| `response_found` | `found` |
| `response_assembled` | `assembled` |
| `response_not_found` | `not_found` |
| `response_entity_unresolved` (Slice 1) | `entity_key_unresolved` |
| `response_non_core` | `assembled` or `found` (document chosen rule) |
| Graph empty-response fallback | `not_found` or explicit error outcome |

**Proposal for `response_non_core`:** use `assembled` when attrs requested (same as post-specialist shape) — confirm with Paul if needed.

---

## Tests

- `tests/test_query_response_outcomes.py` (smoke): matrix of scenarios → assert `outcome` present and matches expected
- MCP schema smoke: `QueryResponse.model_json_schema()` includes `outcome`, `suggestions`
- Regression: existing smoke tests still pass (no behavior change beyond `outcome` population)

---

## Exit criteria

- `uv run pytest -m smoke -q` green
- Every documented response path sets non-null `outcome`
- MCP `mycelium://schema/query-response` includes new fields

---

## Paul decisions (locked)

- **Admin UI:** deferred — backlog items #1–2 in [`admin-ui-backlog.md`](admin-ui-backlog.md)