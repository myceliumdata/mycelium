# Review: MCP slice 2 — onboarding surface (`2026-06-08-1400`)

**Verdict: Approve — ready to commit and push**

Paul validated MCP end-to-end (`health_check` green, CRM network, full stack OK). Implementation matches the prompt; smoke tests pass. Safe to commit slice 2 and start slice 3.

---

## What looks good

| Area | Notes |
|------|--------|
| **Capabilities builder** | `build_network_capabilities()` and `format_mcp_instructions()` in `introspection.py`; single source for tool output + MCP instructions |
| **`describe_network`** | Returns `guide`, `ontology`, `policy`, `guide_present` / `guide_note`; refreshes runtime once |
| **`list_specialist_routing`** | Removed from MCP; `_routing_payload()` retained for `health_check` only |
| **`guide.md`** | CRM example committed; scaffolded on `network create`; copied by `refresh-example-network` |
| **Policy strings** | Extensibility, out-of-scope, multi-match aligned with design; instructions already point agents at `message` for per-attribute status (sets up slice 3) |
| **Tests** | `tests/test_mcp_onboarding.py` (7 smoke); runtime reload test repointed; create/example tests assert `guide.md` |
| **Docs** | README, architecture, walkthrough, CRM README updated |

**Smoke (review run):** `tests/test_mcp_onboarding.py` + `tests/test_mcp_runtime_reload.py` — 11 passed.

---

## Minor nits (non-blocking — slice 4 polish)

1. **`src/mycelium.egg-info/PKG-INFO`** — still lists `query_person` / `list_specialist_routing` (stale egg-info; regenerate on install or ignore).
2. **`examples/networks/crm/specialists/`** — untracked; decide in polish slice whether to commit reference copies.
3. **Slice 2 uncommitted** — working tree still has all slice 2 changes on `main`; commit before slice 3 claim.

---

## Intentional deferrals (slice 3)

- `QueryResponse.message` still uses `message_for_assembled` / `response_non_core` (“still researching”, “not currently available”, `(via specialist)`). Slice 3 replaces this with classification-aware buckets.
- `response_not_found` still appends “This lookup did not match any record.” — slice 3 spec shortens to `No record found for {entity_key!r}.`

---

## Unblocks slice 3

Commit slice 2, then claim `prompts/cursor/next/2026-06-08-1500-mcp-slice3-query-messages.md`.