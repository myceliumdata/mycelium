# Review: Entity protocol polish — post Slice 8

**Reviewer:** Grok  
**Date:** 2026-06-09  
**Verdict:** **Approved**

---

## Backlog coverage (P1–P14)

| # | Nit | Status | Evidence |
|---|-----|--------|----------|
| P1 | `1000` output.md `entity_unknown` slice ref | Pass | Deferred to Slice 3 in `1000` output |
| P2 | Weak no-invoke assertion | Pass | `specialists_to_invoke == []` in key-suggestions + registry-bind tests |
| P3 | `entity_suggestions` clear | Pre-fixed (`1005`) | — |
| P4 | `optional_fields` omits `binding` | Pass | `introspection.py`; `test_mcp_onboarding.py` |
| P5 | Q4c: 2+ registry rows name-only | Pass | `test_name_only_two_registry_rows_requires_employer` |
| P6 | Validation mode docs | Pass | `entity_validation.py` module docstring |
| P7 | Weak assembled+validate assertion | Pass | Removed weak `or entity_validated not in outcome` |
| P8 | Dead code | Pre-fixed (`1500`) | — |
| P9 | Duplicate-bind message | Pre-fixed (`1500`) | — |
| P10 | `invoke_specialists_node` gate defense | Pass | `research_gate_allows` guard + audit line in `dispatch.py` |
| P11 | `context["seed"]` pre–`build_context` | Pass | `planner_context()` — `entity_id`/`bind` in supervisor + validate |
| P12 | `1700` output slice numbering | Pass | Phase 8 / `1700`; polish is **P** not Slice 9 |
| P13 | Murphy re-query email assert | Pass | `requery.results[0].get("email") == "paul.murphy@acme.example"` |
| P14 | Attribution coupled to audit log | Pass | `researched_fields` on contrib + template; audit fallback retained |

## Tests

- Full smoke: **213 passed**
- New/updated: `test_entity_growth.py` (structured attribution unit), registry-bind P5, key-suggestions P2, validation P7, MCP P4

## Notes (non-blocking, no fix slice)

- `1800` `output.md` says `supervisors_to_invoke`; implementation correctly uses `specialists_to_invoke`.
- P10 gate block in `invoke_specialists_node` is not covered by a dedicated unit test; supervisor/gate smokes still exercise the path indirectly.

---

## Gate

**Entity protocol program Slices 1–8 + polish complete.** Slices 9–10 (metering) remain deferred per program doc.