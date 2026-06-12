# Review — Program 1 Attribute provenance polish

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

Extra: `LANGCHAIN_TRACING_V2=false uv run pytest -q` → **322 passed**

---

## Backlog (P1–P12)

| # | Status | Evidence |
|---|--------|----------|
| P1 | Pass | `ensure_versioned_for_write` docstring + architecture note; `test_ensure_versioned_for_write_wraps_flat_pending` |
| P2 | Pass | `entity_growth` versioned-only; no flat `researched_at` branch |
| P3 | Pass | Single pending branch in `_persist_field_version` |
| P4 | Pass | `test_write_pending_in_place_retry_preserves_started_at` |
| P5 | Pass | `specialist_fields` read helpers versioned-only; tests updated |
| P7 | Pass | `_analyze_storage` validates + counts versioned fields only |
| P8 | Pass | `test_status_flat_v1_field_fails_loud_on_drill_down` |
| P9 | Pass | Dead empty-status branch removed |
| P10 | Pass | `.version-history` styles in `admin-ui/src/styles.css` |
| P11 | Pass | `CategoryTree.mapped_category()`; `query_provenance` uses it |
| P12 | Pass | `test_build_query_provenance_multi_match_entities` |

---

## Program 1 closeout

Slices 1–3 + polish complete. Delivered:

- Versioned specialist storage (write + read)
- Admin version history on entity drill-down
- `QueryResponse.provenance` when `EntityQuery.provenance=true`
- Hard cutover enforced at introspection / provenance boundaries

**Operator correction** and **force re-research** remain deferred (Program 3); **MVR/bind unified write** remains Program 2.

---

## For Paul

- **Safe to commit** full Program 1 implementation (slices 1–3 + polish) — working tree if not yet committed.
- **Refresh networks** before hands-on (`./bin/refresh-example-network crm`).
- **Manual:** `--provenance` on linkedin query; admin version `<details>`.
- **TODO:** Mark Program 1 complete; Program 2 design may start.

Suggested commit message:

```
feat: extended attribute provenance Program 1

Versioned specialist storage, admin history, QueryResponse.provenance,
hard-cutover hygiene polish (P1–P12).
```