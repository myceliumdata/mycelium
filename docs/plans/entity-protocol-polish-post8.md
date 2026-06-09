# Entity protocol — polish backlog (post Slice 8)

**Status:** Living backlog — Grok maintains during slice reviews  
**Cursor prompt:** `prompts/cursor/next/2026-06-09-1800-entity-protocol-polish-post8.md` (run **after** Slice 8, before deferred Slices 9–10)

---

## Purpose

Non-blocking nits from Grok review of Slices 1–8 accumulate here. One polish pass after Slice 8 ships — do not insert these into the main slice sequence.

**Blocking nits** do **not** go here. They become **fix slices** queued immediately after the reviewed slice (see program doc → Review nit triage).

---

## Backlog

| # | Source slice | Nit | Files / area |
|---|--------------|-----|--------------|
| P1 | 1 | `output.md` says `entity_unknown` deferred to "slice 2" — should be Slice 3 | `1000` done/output.md |
| P2 | 1 | Weak no-invoke assertion (`invoke_specialists` not in debug); prefer audit_log / empty `specialists_to_invoke` | `tests/test_entity_key_suggestions.py` |
| P3 | 1 | Clear `entity_suggestions` on supervisor non-suggest returns (checkpoint hygiene) | `src/agents/supervisor.py` |

---

## Exit criteria

- All rows addressed or explicitly waived by Paul in `review.md`
- Smoke suite green; no new blocking issues introduced