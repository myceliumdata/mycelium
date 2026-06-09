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
| P2 | 1, 4 | Weak no-invoke assertion (`invoke_specialists` not in debug); prefer audit_log / empty `specialists_to_invoke` | `tests/test_entity_key_suggestions.py`, `tests/test_entity_registry_bind.py` |
| ~~P3~~ | 1 | ~~Clear `entity_suggestions`~~ — fixed in `1005` | — |
| P4 | 4 | `describe_network` `policy.query.optional_fields` omits `binding` | `src/network/introspection.py` |
| P5 | 4 | No smoke for Q4c: name-only key with 2+ registry rows → require employer | `tests/test_entity_registry_bind.py` |
| P6 | 5 | Validation rules in `entity_validation.py`; specialists not invoked in validation mode (Pattern C deferred for Q5d v1) | `src/agents/entity_validation.py`, `validate_entity_node` |
| P7 | 5 | Weak assembled+validate assertion (`or "entity_validated" not in outcome`) | `tests/test_entity_validation.py` |
| ~~P8~~ | 5 | ~~Dead code: `registry_provisional_only`, `response_registry_provisional_identity`~~ — fixed in `1500` | — |
| ~~P9~~ | 5 | ~~Duplicate-bind message still says “provisional” after validation~~ — fixed in `1500` | — |
| P10 | 6 | `output.md` claims `invoke_specialists_node` gate defense; only supervisor + `validate_entity` enforce | `src/agents/dispatch.py` |
| P11 | 7 | Supervisor/validate still set `context["seed"]` pre–`build_context` (confusing vs `entity_id`/`bind` shape) | `supervisor.py`, `dispatch.py` |

---

## Exit criteria

- All rows addressed or explicitly waived by Paul in `review.md`
- Smoke suite green; no new blocking issues introduced