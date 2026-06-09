# Task: Research gate — Phase 6

> **READY** — Slice 5 approved. Move to `in-progress/` to start.

**Read these first (mandatory):**
- `prompts/cursor/WORKFLOW.md`
- [`docs/plans/entity-research-gate-phase6.md`](../../docs/plans/entity-research-gate-phase6.md) — **locked spec**
- Slices 1–5 specs

**Depends on:** Slices 1–5 implemented.

---

## Objective

Single research gate: invoke specialists/Tavily only when `current_id` set AND (seed pre-validated OR registry `validation_state == validated`).

Provisional + attrs → no specialists; `found` + gate message; identity-only in `results`.

**Same turn:** after Slice 5 validation in one graph run, allow research immediately when validation just completed. Graph order: validate before gate check.

**No `research_gated` outcome.**

---

## Locked Paul decisions

- Q6a: `found` + clear message when gated (no `research_gated`)
- Q6b: Same turn — research after validation in one graph run
- Bootstrap seed trusted for gating (no validation loop)

---

## Governance (mandatory)

- **Do not edit `TODO.md`.**
- Admin UI deferred per `admin-ui-backlog.md`.

---

## Deliverables

`prompts/cursor/done/2026-06-09-1500-entity-research-gate-phase6/` with `prompt.md`, `output.md`.