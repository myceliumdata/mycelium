# Review — MVR redesign Slice M1 (docs + schema notes)

**Verdict:** **Approved**

**Reviewer:** Grok (Paul requested review, June 2026)

---

## CI (mandatory)

```bash
./bin/ci-local
```

| Step | Result |
|------|--------|
| `uv sync --all-extras` | OK |
| `admin-ui` build | OK |
| `ruff` | All checks passed |
| smoke pytest | **296 passed**, 26 deselected |

---

## Spec compliance (M1)

| Requirement | Status |
|-------------|--------|
| Architecture: target protocol section | Pass — identity / lookup / MVR; two-step `delivery_id`; outcomes |
| Current runtime labeled legacy | Pass — `Public query flow (current runtime)` + migration note |
| Program 2 blocked note | Pass |
| `mvr-best-practices.md` current vs target | Pass |
| `mvr-redesign-entity-query-examples.md` | Pass — step 1/2, create, removed fields |
| `describe_network` / capabilities `target_protocol` | Pass — description, examples, `protocol_status` |
| MCP instructions mention target | Pass |
| `test_mcp_onboarding` | Pass — `target_protocol` asserted; `response_provenance` retained |
| No runtime behavior change | Pass — `EntityQuery`, graph, resolution untouched |

---

## Non-blocking nits

None.

---

## For Paul

- **Safe to commit** M1 docs + introspection policy narrative + test assertion.
- **M2 unblocked** — `DeliveryStore` + 5m TTL for delivery + quotes.
- Runtime still legacy `entity_key` until M9; visiting agents should read `policy.query.target_protocol`.

Suggested commit message:

```
docs: MVR redesign M1 — target protocol, two-step delivery_id narrative

Architecture + describe_network target_protocol; entity-query examples;
legacy entity_key flow labeled current runtime until M2–M9.
```