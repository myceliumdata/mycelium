# Review — 2026-06-09-1710-eliminate-core-person-fields-reprocess

**Reviewer:** Grok (on behalf of Paul + Grok)

**Overall:** Excellent. Cursor removed the legacy CORE_PERSON_FIELDS / non_core_attributes split entirely. Name/employer (and any attr) now correctly route through specialist classification/invocation and get proper "via ..." status messages while still returning full identity records with person_id. Matches the spec and 1700 sibling perfectly.

## Strengths
- state.py: CORE_PERSON_FIELDS, MINIMUM_VIABLE_FIELDS, non_core_attributes fully removed; normalized_requested_attributes added.
- dispatch.py (assemble_response_node): now uses all requested attrs via normalized_requested_attributes; no core filtering.
- routing.py, validator.py: updated to use all requested (local legacy MINIMUM_VIABLE still present but unwired).
- specialist_agent.py.j2 + all 6 *_specialist.py: _resolve_owned_fields fallback now uses query.requested_attributes directly (no non_core).
- docs/architecture.md and plans/seed-data-context-architecture.md: cleaned of core-field privilege language; 1710 marked done.
- Verifs: smoke 23p, full 3p, ruff clean (py files), manual CLI `--attributes name` produces exactly "name not currently available but may be in the future (via contact_specialist)", results have full identity + person_id, debug shows assembled + contributions=1.
- Scope: strictly 1710 (sibling to 1700); did not touch 1720 seed transform or UUID id.

## Minor Notes / Observations
- Smoke count at 23 (consistent post-core removal; 11 deselected).
- The specialists were already updated in 1600; 1710 further refined the template fallback and re-applied.
- routing.py still references core_identity (legacy from pre-1530); harmless for this scope.
- validator.py has local _MINIMUM_VIABLE_FIELDS (noted as unwired legacy in output).

## Follow-up Recommendations (for next Grok/Paul planning)
1. 1720 next: eliminate id from seed transform, make results "id" = UUID, update seed.py, supervisor, tests, docs.
2. After 17xx, full end-to-end test matrix for name/employer queries behaving as any other specialist attr.
3. Consider cleaning up remaining legacy core_identity references in routing.py etc. in a polish pass.

**Status:** Approved. No changes requested. Ready to move forward.

**Next suggested objective for the reset prompt / TODO:** 1720-eliminate-id-from-seed-transform-reprocess (remove legacy "id" from seed.json, make results "id" the UUID, update all builders/tests/docs). See user issues with --attributes name returning old person-0001 + unrequested employer.