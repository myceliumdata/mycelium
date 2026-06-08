# Review: MCP slice 4 — onboarding polish (`2026-06-08-1600`)

**Verdict: Approve — ready to commit and push**

Polish slice closes the nits from slices 1–3 without scope creep. Smoke suite fully green (including former `test_langsmith_utils` flake). MCP onboarding can be marked complete.

---

## What looks good

| Area | Notes |
|------|--------|
| **LangSmith flake** | `test_custom_ui_base` clears org/project/API env so custom UI base is not overridden |
| **Slice 3 test nits** | `found=['email']`, `unavailable=['email']`, `not found for this record` positive asserts |
| **Specialist template** | `model_copy` legacy overrides removed; uses `response_found` / `response_non_core` only |
| **CRM reference specialist** | `examples/networks/crm/specialists/contact_specialist.py` committed; README documents decision |
| **Entity vocab test** | `test_crm_reference_contact_specialist_uses_entity_vocab` guards reference copy |
| **Internal rename** | `find_by_key(entity_key)`, `find_persons(entity_key)` |
| **MCP schemas** | `_neutral_json_schema` descriptions on `EntityQuery`, `QueryResponse`, `SeedRecord` |
| **Vocab sweep** | `TODO.md`, `PROJECT_BRIEF.md`, `networks-terminology.md` — no stale public `PersonQuery` / `query_person` |
| **TODO closure** | MCP onboarding slices 1–4 marked complete; deferred items (fuzzy, per-record messages) left open |
| **CRM example dir** | No committed runtime artifacts (`categories.json`, `agents/`, etc.) — copy-source only |

**Smoke (review run):** 146 passed, 20 deselected. **Ruff:** clean.

---

## Prompt checklist

| Item | Status |
|------|--------|
| Stale vocab in live docs / TODO | Done |
| `test_langsmith_utils` flake | Done |
| Slice 3 test hardening | Done |
| Specialist template alignment | Done (template + CRM reference; framework `src/agents/specialists/` remains gitignored by design) |
| CRM `specialists/` decision | Done — reference copy committed |
| Scrub CRM runtime artifacts | Done — example dir clean |
| `find_by_key` param rename | Done |
| MCP schema descriptions | Done |
| egg-info | Documented no-op (gitignored) |

---

## Post-review nits (resolved in follow-up commit)

1. **`__pycache__`** — removed from `examples/networks/crm/specialists/`; not committed.
2. **Framework specialists** — regenerated on disk from updated template (gitignored); regen commands documented in `output.md`.
3. **`docs/plans/*`** — historical notes added to phase 1/2 plans; live references updated in specialist-research + seed-data-context plans.

---

## MCP onboarding — closed

Slices 1–4 + live MCP verify + thread checkpoint fix (`2d397b8`) complete the visiting-agent onboarding track. **Next backlog:** fuzzy matching, admin daemon (demo slice 3), or other `TODO.md` items — not more MCP polish unless new nits emerge.