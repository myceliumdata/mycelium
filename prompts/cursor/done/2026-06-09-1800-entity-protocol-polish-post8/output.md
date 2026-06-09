# Output — Entity protocol polish post Slice 8 (`1800`)

## Summary

Addressed all non-blocking nits (P1–P14) from `entity-protocol-polish-post8.md`. No new protocol features — documentation, test assertions, context shape consistency, research gate defense-in-depth, and structured `researched_fields` for attribution.

## Changes

| Area | Fix |
|------|-----|
| **P1** | `1000` output.md — `entity_unknown` deferred to Slice 3 |
| **P2** | Stronger no-invoke tests via `supervisors_to_invoke == []` |
| **P4** | `policy.query.optional_fields` includes `binding` |
| **P5** | Smoke: name-only + 2 registry rows → `entity_unknown` |
| **P6** | `entity_validation.py` docstring — inline rules, Pattern C deferred |
| **P7** | Removed weak `or entity_validated not in outcome` assertion |
| **P10** | `invoke_specialists_node` research gate block |
| **P11** | `planner_context()` — supervisor/validate use `entity_id`/`bind` not `seed` |
| **P12** | `1700` output.md slice numbering |
| **P13** | Murphy re-query asserts `email` in `results` |
| **P14** | `researched_fields` on `specialist_contrib` + contribution row; attribution prefers structured field |

**Regenerated:** framework specialists + CRM `contact_specialist` (template `researched_fields`).

**Updated:** `docs/plans/entity-protocol-polish-post8.md` — backlog marked resolved.

## Tests

```bash
uv run pytest -m smoke -q   # 213 passed
```

## For Grok + Paul

- Mark entity protocol polish (`1800`) done in `TODO.md` when reviewed.
- Entity protocol program Slices 1–8 + polish complete; deferred items remain in `TODO.md` (Q8b–d, metering, etc.).

## Exit criteria

- [x] All backlog rows P1–P14 addressed (P3/P8/P9 were pre-fixed)
- [x] Smoke green (213)
