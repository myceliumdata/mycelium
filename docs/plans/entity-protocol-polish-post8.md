# Entity protocol — polish backlog (post Slice 8)

**Status:** Addressed in polish pass `1800` (June 2026)  
**Cursor prompt:** `prompts/cursor/done/2026-06-09-1800-entity-protocol-polish-post8/`

---

## Purpose

Non-blocking nits from Grok review of Slices 1–8 accumulated here. One polish pass after Slice 8 ships — do not insert these into the main slice sequence.

**Blocking nits** do **not** go here. They become **fix slices** queued immediately after the reviewed slice (see program doc → Review nit triage).

---

## Backlog (resolved in `1800`)

| # | Source slice | Nit | Status |
|---|--------------|-----|--------|
| P1 | 1 | `1000` output.md slice reference for `entity_unknown` | Fixed → Slice 3 |
| P2 | 1, 4 | Weak no-invoke assertion | Fixed — `supervisors_to_invoke == []` |
| ~~P3~~ | 1 | Clear `entity_suggestions` | Fixed in `1005` |
| P4 | 4 | `optional_fields` omits `binding` | Fixed |
| P5 | 4 | Q4c smoke: 2+ registry rows name-only | Fixed |
| P6 | 5 | Validation mode docs | Fixed — module docstring |
| P7 | 5 | Weak assembled+validate assertion | Fixed |
| ~~P8~~ | 5 | Dead code | Fixed in `1500` |
| ~~P9~~ | 5 | Duplicate-bind message | Fixed in `1500` |
| P10 | 6 | `invoke_specialists_node` gate defense | Fixed |
| P11 | 7 | `context["seed"]` pre–`build_context` | Fixed — `planner_context` |
| P12 | 8 | `1700` output slice numbering | Fixed |
| P13 | 8 | Murphy re-query email assert | Fixed |
| P14 | 8 | Attribution coupled to audit log | Fixed — `researched_fields` on contrib |

---

## Exit criteria

- [x] All rows addressed
- [x] Smoke suite green
