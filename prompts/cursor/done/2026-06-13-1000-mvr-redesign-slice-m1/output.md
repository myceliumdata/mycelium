# MVR redesign — Slice M1 (docs + schema notes)

## Summary

Documented the locked MVR redesign protocol (UUID identity, lookup vs MVR, two-step `delivery_id`) without changing runtime behavior. Legacy `entity_key` / `binding` flow remains until M2–M9.

## Changes

| Area | Change |
|------|--------|
| **`docs/architecture.md`** | New **MVR redesign (target protocol)** section; current flow relabeled **(current runtime)**; cross-links to program, best practices, examples; Program 2 blocked note |
| **`src/network/introspection.py`** | `policy.query.target_protocol` with description, step-1/2 JSON examples, target fields/outcomes; `protocol_status: legacy entity_key until M9`; MCP instructions mention target protocol |
| **`docs/plans/mvr-redesign-entity-query-examples.md`** | **New** — canonical step-1 / step-2 request/response examples |
| **`docs/plans/mvr-best-practices.md`** | Current runtime vs target preamble |
| **`docs/plans/README.md`** | Examples doc link; Program 2 explicitly blocked on MVR redesign |
| **`tests/test_mcp_onboarding.py`** | Assert `target_protocol` present in capabilities |

**Untouched:** `EntityQuery` models, graph, resolution, `entity_key` in code.

## Verification

```bash
./bin/ci-local
# uv sync OK · admin-ui build OK · ruff OK · 296 smoke passed, 26 deselected
```

## For Grok + Paul

- **M1 complete** — docs + `describe_network` target-protocol narrative; runtime unchanged.
- **M2 unblocked** — `DeliveryStore` + 5m TTL (`mvr-redesign-slice-m2` prompt to queue).
- **Program 2** (versioned bind) remains blocked until MVR redesign program completes.
- **TODO.md:** mark M1 done; queue M2 prompt if not already listed.
- **Not committed** — awaiting review.

Suggested commit message:

```
docs: MVR redesign M1 — target protocol, two-step delivery_id narrative

Architecture + describe_network target_protocol; entity-query examples;
legacy entity_key flow labeled current runtime until M2–M9.
```
