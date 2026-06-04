# Review — 2026-06-09-1550-supervisor-context-graph-reprocess

**Reviewer:** Grok (on behalf of Paul + Grok)

**Overall:** Solid execution of the multi-node graph for seed-data-context. Cursor added the context builder, updated supervisor to pure planning, introduced the three dispatch nodes, rewired the graph with conditional routing, and updated tests/fixtures. Verifications pass and the flow is exercised.

## Strengths
- New `src/agents/context.py` implements `ContextBuilder.build_full_context` pulling seed + specialist stores by person_id (with the exact TODO for peer retrieval).
- `supervisor.py` now plans *all* specialists via `_collect_specialists_to_invoke`, stores plan in `context._meta`, always sets `route=None`, and enriches state with matched_persons/context/current_person_id.
- `dispatch.py` cleanly splits into `build_context_node`, `invoke_specialists_node` (sequential with full context + target_fields + contributions collection), and `assemble_response_node` (merges using pending logic + "via ..." labels); legacy alias preserved.
- `graphs/core.py` adds the nodes and conditional (`_specialists_planned` → build_context vs direct assemble_response) with proper fan-in edges.
- Tests updated (test_core_graph.py etc.) to assert the new paths, "assemble_response" in logs, contributions in debug, no "core record" language.
- Smoke + full tests green (25 smoke, 7+ full including core_graph). Ruff clean. No core_data left in the new files.
- Scope respected: only graph orchestration + context builder; no specialist re-gen (that's 1600) or other slices.

## Minor Notes / Observations
- Manual CLI-like queries (name-only + multi-attr) are covered by the updated full tests, which check planning, context build, contributions=2 in debug, "not currently available" / "via" messages, and "assembled" outcome.
- Some test updates appear in other files (e.g. test_supervisor_routing.py) — likely cumulative from prior slices but don't affect this scope.
- Committed specialists still have old headers (expected until 1600 re-gen).
- The assemble_response for name-only bypasses context/specialists as designed (direct seed response).

## Follow-up Recommendations (for next Grok/Paul planning)
1. Next is 1600 capstone: run reset-mycelium, re-gen all 6 specialists with the new template, update docs/architecture.md/TODO.md, full matrix including ambiguous names and post-reset.
2. Consider adding a quick manual CLI smoke in the 1550 output (name-only + one multi-attr) once 1600 lands, for end-to-end trace.
3. The peer-retrieval TODO in context.py can be a later phase item.

**Status:** Approved. No changes requested. Ready to move forward.

**Next suggested objective for the reset prompt / TODO:** 1600 integration-tests-reset-docs-regen (re-gen specialists, update docs, full verification matrix). See existing TODO and plan.