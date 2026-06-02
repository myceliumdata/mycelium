# Review — 2026-06-02-1100-supervisor-as-coordinator-router

**Reviewer:** Grok (on behalf of Paul + Grok)

**Overall:** Strong, well-structured refactor. Cursor made significant progress toward the architectural goal of making the supervisor a narrow coordinator/router. The extraction into `routing.py`, `responses.py`, and `core_identity.py` is a clear improvement in separation of concerns.

## Strengths

- **Meaningful reduction in supervisor responsibility**: The main `supervisor.py` went from ~150 lines of mixed logic down to ~45 lines of coordination. This is exactly the kind of narrowing the architecture calls for.
- **Good modular design**:
  - `routing.py` now owns decision logic and `SupervisorDecision`.
  - `responses.py` centralizes all `PersonResponse` construction.
  - `core_identity.py` provides a clean facade over storage (with a clear path to replace it with a real specialist later).
- **Correct use of the accessor pattern**: The supervisor no longer imports `get_storage`, `find_person`, or `upsert_person` directly. Data access is delegated through `CoreIdentityAccessor`.
- **Preserved behavior**: All existing flows (lookup, non-core, ingestion) continue to work at the `PersonResponse` level with no regressions (8 tests passing).
- **New test coverage**: The addition of `test_supervisor_routing.py` with stubbed accessors is excellent for testing routing decisions in isolation.
- **Honest documentation of remaining gaps**: The output clearly calls out that `CoreIdentityAccessor` is still a wrapper and that true specialist delegation is future work.

## Minor Observations / Risks

1. **The "thin supervisor" is still doing quite a lot indirectly**  
   While the module itself is small, `evaluate_supervisor_turn` in `routing.py` has absorbed most of the previous logic. Some of the complexity has simply moved rather than been eliminated. This is acceptable as a first major step, but future iterations should continue pushing logic out (especially response construction and non-core detection).

2. **CoreIdentityAccessor is still tightly coupled to the singleton**  
   It correctly hides the direct import, but it still reaches into `get_storage()`. This is the right Phase 1 compromise, but the design makes it clear that a real `CoreIdentity` specialist can replace this later.

3. **Graph state still carries a `person` object**  
   Several paths still put `person` into the returned dict for the graph state. While this is internal, it means some data ownership still leaks through the graph contract rather than being fully encapsulated in the accessor.

4. **Response builders are still centralized**  
   `responses.py` is a good intermediate step, but as more specialist types are added, we may want per-domain response builders.

## Verdict

**Approved with enthusiasm.**

This is one of the more impactful refactors we've done toward the long-term architecture. The supervisor is now visibly acting as a coordinator rather than a data-owning agent. The new module structure provides a much better foundation for future specialist integration.

**Status:** Approved. No blocking issues. Minor follow-up suggestions noted above.

**Recommended next steps:**
- Continue the pattern: push more decision-making and response construction out of the central routing function as real specialists are introduced.
- Consider whether the graph state contract (`person`, `validation_passed`, etc.) should be made more explicit or split for the ingestion flow.
- The dead-code cleanup from 1010 is now nicely complemented by this structural improvement.

Ready for the next iteration.