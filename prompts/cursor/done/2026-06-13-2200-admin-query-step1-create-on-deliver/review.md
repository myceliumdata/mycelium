# Review: Admin query UX + step-1 `create_on_deliver`

**Reviewer:** Grok  
**Date:** 2026-06-13  
**Verdict:** **Approved**

---

## CI

```bash
./bin/ci-local
# 360 passed, 26 deselected · ruff OK · admin-ui build OK
```

---

## Spec compliance

| Requirement | Status |
|-------------|--------|
| `delivery.create_on_deliver: true` only when step 2 creates | ✅ `DeliveryPayload.from_scope` |
| Omit field (not `false`) for existing matches | ✅ `exclude_none` via `public_dict` / `public_json` |
| Locked step-1 `message` strings | ✅ `response_lookup_resolved` |
| Admin `(full MVR)` when `create_on_deliver === true` | ✅ |
| Admin deliver copy without “pre-filled” | ✅ |
| No auto-deliver | ✅ unchanged in `runQueryRequest` |
| Baseline from `b6a2a2b` / `8c735a0` preserved | ✅ verified in diff |
| Introspection policy updated | ✅ |
| Tests for create vs existing JSON shape | ✅ daemon + target_resolve + create_on_deliver |
| No `TODO.md` edit | ✅ |
| Not committed (awaiting Grok) | ✅ left in working tree |

---

## Implementation notes

**Good:**
- `QueryResponse.public_dict()` / `public_json()` centralizes public serialization — cleaner than scattering `exclude_none` at three call sites.
- `from_scope` reused in `issue_target_delivery` and `delivery_payload_from_scope` — single seam.
- Admin checks `create_on_deliver === true` strictly (not inferring from `total_matches === 0`).

**Minor (non-blocking):**
- `if delivery.create_on_deliver:` in `response_lookup_resolved` is fine (`None` is falsy); `is True` would be marginally more explicit.
- `public_dict(exclude_none=True)` drops null optional top-level fields (e.g. `quote`, `total_matches` on step 2) from CLI/MCP/admin JSON — desirable for this slice; note if external clients relied on explicit `null` (none found in tests).

---

## Files reviewed (full diff)

- `admin-ui/src/App.tsx`, `admin-ui/src/types.ts`
- `src/models/state.py`
- `src/agents/responses.py`, `target_resolve.py`, `target_metering.py`
- `src/mycelium_admin/server.py`, `mycelium_mcp/server.py`, `main.py`
- `src/network/introspection.py`
- `tests/test_admin_daemon.py`, `test_mvr_create_on_deliver.py`, `test_mvr_entity_query_models.py`, `test_mvr_target_resolve.py`

---

## Suggested commit message

```
feat: expose delivery.create_on_deliver on step-1 and polish admin query UX

Add create_on_deliver to DeliveryPayload (true only); update lookup_resolved
messages; public JSON via QueryResponse.public_dict; admin (full MVR) copy.
```