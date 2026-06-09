# Task: Entity boundary fixup — regenerate framework specialists

> **READY** — Slice 7 review blocking nit (Q7b). Run **before** Slice 8 (`1700`).

**Read these first (mandatory):**
- `prompts/cursor/WORKFLOW.md`
- [`docs/plans/entity-boundary-cleanup-phase7.md`](../../docs/plans/entity-boundary-cleanup-phase7.md) — Q7b
- `prompts/cursor/done/2026-06-09-1600-entity-boundary-cleanup-phase7/review.md`
- `src/agents/factory/templates/specialist_agent.py.j2` (canonical)
- `examples/networks/crm/specialists/contact_specialist.py` (reference)

**Depends on:** Slice 7 (`1600`) implemented locally.

---

## Problem

Slice 7 updated the factory template to `entity_id` / `bind` / extended-only `storage`, but the four **framework fallback** modules on disk under `src/agents/specialists/` still use `context.seed`. CRM in-network only ships `contact_specialist.py`; demographic, professional, and social load via `import_module("agents.specialists.<name>")` and will break identity/research on attribute queries.

Files are **gitignored** (`src/agents/specialists/*_specialist.py`) but must exist on disk after clone/reset (same pattern as fixup `1350`).

---

## Objective

Regenerate all four framework specialist modules from the current template:

- `src/agents/specialists/contact_specialist.py`
- `src/agents/specialists/demographic_specialist.py`
- `src/agents/specialists/professional_specialist.py`
- `src/agents/specialists/social_specialist.py`

No `context.seed` references. `_research_context` uses `bind` + stripped storage.

---

## Tests (add or extend)

- Smoke: invoke `agents.specialists.demographic_specialist` (import_module path) with `context={"entity_id", "bind", "specialists"}` — identity resolves, no `seed` key required.
- `rg 'context\.get\("seed"\)' src/agents/specialists/*_specialist.py` → no matches.
- Full smoke green.

---

## Governance (mandatory)

- **Do not edit `TODO.md`.**
- **Do not commit Slice 7** — Grok commits `1600` + `1605` together after this fix is approved.

---

## Deliverables

`prompts/cursor/done/2026-06-09-1605-entity-boundary-regen-framework-specialists/` with `prompt.md`, `output.md`.