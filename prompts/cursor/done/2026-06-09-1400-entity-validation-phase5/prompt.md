# Task: Core validation orchestration — Phase 5

> **READY** — Slice 4 approved. Move to `in-progress/` to start.

**Read these first (mandatory):**
- `prompts/cursor/WORKFLOW.md`
- [`docs/plans/entity-validation-phase5.md`](../../docs/plans/entity-validation-phase5.md) — **locked spec**
- Slices 1–4 specs

**Depends on:** Slices 1–4 implemented.

---

## Objective

Validation mode on demographic + professional specialists (rule-based, no Tavily, no LLM). Registry arbiter promotes `validation_state` and field states. Outcome `entity_validated` when validation completes without attr research in same turn.

**Same graph turn:** bind (if needed) → validate → research when validated (Slice 6 gate). When attrs requested and validation passes, final outcome is `assembled` / `found` with attrs — not `entity_validated`.

**No email research on provisional entities.** Bootstrap seed skips validation.

---

## Locked Paul decisions

- Q5a: Validate on every query once MVR complete (even identity-only)
- Q5b: Validator failure → stay provisional, `found` + message; no `validation_rejected`
- Q5c: Same turn: bind → validate → research when validated
- Q5d: Rule-based validation only (name ≥2 chars not all digits; employer ≥2 chars)

---

## Governance (mandatory)

- **Do not edit `TODO.md`.**
- Admin UI deferred per `admin-ui-backlog.md`.

---

## Deliverables

`prompts/cursor/done/2026-06-09-1400-entity-validation-phase5/` with `prompt.md`, `output.md`.