# Review — 2026-06-09-1600-integration-tests-reset-docs-regen-reprocess

**Reviewer:** Grok (on behalf of Paul + Grok)

**Overall:** Capstoned the redesign cleanly. Cursor reset-mycelium (no core/seed.json handling), re-generated all 6 specialists from the updated 1540 template (correct headers, 3-scenario logic, TODO, specialist_contrib, person_id/context/target_fields, no core_identity), updated MCP/main/CLI/tests/docs, and passed the full verification matrix including manual CLI paths.

## Strengths
- reset-mycelium: no CORE_AGENT_NAME, --base uses agents.seed/seed.json correctly, dry-run works, no seed.json touching.
- Re-gen: 6 specialists (contact, social, relationships, demographic, professional, financial) via factory after --specialists reset; each has new header, 3 scenarios + TODO on pending, specialist_contrib, context/person_id/owned fields handling.
- Docs: architecture.md (seed origin, graph, no core), plans/seed-data-context-architecture.md (implemented banner + table to 1600), TODO.md (redesign landed).
- MCP/main/CLI: updated for seed.json default, specialist status messages, legacy notes.
- Tests: trace_capture isolation (clears env, resets singletons, mocks graph invoke), full matrix (smoke 23p, full 9p), manual CLI examples (name-only "Found record...", multi-attr "not currently available... (via contact_specialist)", contributions in debug, ambiguous/missing handled).
- Ruff clean, grep no core_data in runtime (only legacy comments), seed.json confirmed 457 source, traces work.
- Scope: only capstone integration/re-gen/docs; no post-1600 (UUID, seed transform).

## Minor Notes / Observations
- Smoke count 23 (down from prior; some tests now deselected post-core removal, as expected).
- Specialist headers show re-gen timestamp (June 4); committed files updated in place.
- Manual CLI in output.md uses python -m main (works); full matrix covers name/+1cat/+multicat/ambiguous/missing/post-reset re-create.
- Seed still has legacy "id" (person-0001 etc.) — correct, as 1720 not yet.

## Follow-up Recommendations (for next Grok/Paul planning)
1. Proceed to 1700 (expose UUID in results) + 1710/1720 siblings as next.
2. After 17xx, consider a final doc pass or commit of all reprocess artifacts + code.
3. The redesign is now end-to-end: seed as origin, supervisor plans context, specialists contribute via 3 scenarios, no core.

**Status:** Approved. No changes requested. Ready to move forward.

**Next suggested objective for the reset prompt / TODO:** 1700-expose-uuid-in-results-reprocess (and 1710/1720) to make results "id" the stable UUID, remove legacy id from seed transform, update builders/tests/docs. See existing TODO and user issues with --attributes name queries.