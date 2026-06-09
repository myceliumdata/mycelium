# Task: Unknown entity + MVR policy — Phase 3

> **ON HOLD** — Batch 1 (slices 1–4). Do not start until batches 2–3 specs approved.

**Read these first (mandatory):**
- `prompts/cursor/WORKFLOW.md`
- [`docs/plans/entity-unknown-mvr-phase3.md`](../../docs/plans/entity-unknown-mvr-phase3.md) — **locked spec**
- Slices 1–2 specs

**Depends on:** Slices 1–2 implemented.

---

## Objective

`network.json` MVR policy; `entity_unknown` + `required_fields`; supervisor short-circuit (no classify/specialists). Add `mvr` to `examples/networks/crm/network.json`. **No persist, no `binding`.**

---

## Locked Paul decisions

- Zero match + no suggestions → `entity_unknown` (not `not_found` for person queries)
- `entity_under_specified` deferred to Slice 4
- Identity-only unknown still returns `required_fields`
- CRM example gets committed `mvr` block

---

## Governance (mandatory)

- **Do not edit `TODO.md`.**
- Admin UI deferred per `admin-ui-backlog.md`.

---

## Deliverables

`prompts/cursor/done/2026-06-09-1200-entity-unknown-mvr-phase3/` with `prompt.md`, `output.md`.