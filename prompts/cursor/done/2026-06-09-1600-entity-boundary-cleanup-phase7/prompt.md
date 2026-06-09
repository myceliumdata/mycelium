# Task: Seed vs specialists boundary cleanup — Phase 7

> **READY** — Slice 6 approved. Move to `in-progress/` to start.

**Read these first (mandatory):**
- `prompts/cursor/WORKFLOW.md`
- [`docs/plans/entity-boundary-cleanup-phase7.md`](../../docs/plans/entity-boundary-cleanup-phase7.md) — **locked spec**
- Slices 1–6 specs

**Depends on:** Slices 1–6 implemented.

---

## Objective

Registry/supervisor owns bind fields. Specialists receive `entity_id`, read-only `bind` (`name`, `employer`), and extended-attrs-only `storage`. Update Jinja factory template, `context.py`, `build_context`, and regen committed reference specialists.

**Delete `src/agents/core_identity.py`.** Remove imports/resets from `routing.py`, `tests/conftest.py`, and other tests. No runtime `core_identity` references.

**Clean slate:** ignore legacy `name`/`employer` in specialist storage; no migration. Operator wipe / refresh for demos.

**Do not delete `seed.json`.**

---

## Locked Paul decisions

- Q7a: Ignore legacy name/employer in specialist storage
- Q7b: Clean slate — factory template + regen reference specialists
- Q7c: Delete `core_identity.py` + clean routing.py / conftest resets

---

## Governance (mandatory)

- **Do not edit `TODO.md`.**
- Admin UI deferred per `admin-ui-backlog.md` (add backlog item #8 per spec).

---

## Deliverables

`prompts/cursor/done/2026-06-09-1600-entity-boundary-cleanup-phase7/` with `prompt.md`, `output.md`.