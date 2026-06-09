# Task: Entity registry + provisional bind — Phase 4

> **ON HOLD** — Batch 1 (slices 1–4). Do not start until batches 2–3 specs approved.

**Read these first (mandatory):**
- `prompts/cursor/WORKFLOW.md`
- [`docs/plans/entity-registry-bind-phase4.md`](../../docs/plans/entity-registry-bind-phase4.md) — **locked spec**
- Slices 1–3 specs

**Depends on:** Slices 1–3 implemented.

---

## Objective

`<network_root>/entities.json`, `EntityRegistry`, `resolve_entity`, `EntityQuery.binding`, provisional bind, `entity_bound_provisional` / `entity_under_specified`. Idempotent duplicate bind → **`found`**. **No validation loop, no email research.**

Add `MYCELIUM_ENTITIES_PATH` to `runtime_path()` map.

---

## Locked Paul decisions

- `results` include `id`, `name`, `employer` on bind
- Uuid `entity_key` preferred for follow-ups
- Name-only key requires `binding.employer` or uuid when 0 or 2+ matches
- Ignore unknown `binding` keys
- Duplicate bind → `found` (Q4e option A)

---

## Governance (mandatory)

- **Do not edit `TODO.md`.**
- Admin UI deferred per `admin-ui-backlog.md`.

---

## Deliverables

`prompts/cursor/done/2026-06-09-1300-entity-registry-bind-phase4/` with `prompt.md`, `output.md`.