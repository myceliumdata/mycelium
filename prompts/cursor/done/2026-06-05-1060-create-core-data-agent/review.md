# Review: 2026-06-05-1060-create-core-data-agent

**Status:** Approved.

## What was done
- Created `src/agents/core_data.py` with a clean, well-structured `core_data_agent` async node.
- The agent:
  - Coerces state
  - Delegates lookup to `CoreIdentity` via `asyncio.to_thread` (non-blocking)
  - Builds appropriate `PersonResponse` using the existing response helpers (found / not-found / non-core)
  - Returns state deltas: `person`, `response`, `route=None`, `audit_log`, and propagates `invocation_*_id`
- Added proper docstrings explaining its role as the specialist for core CRM lookups.
- Updated `core_identity.py` docstring to note it is now used by the CoreDataAgent.
- Added `core_data_agent` export to `src/agents/__init__.py` (sensible).
- Created `tests/test_core_data_agent.py` with good async tests using a stub (2 tests, covering found/not-found).
- Verification: tests pass, ruff clean, full suite green.

## Code quality
- Follows the exact pattern requested: async def core_data_agent(state) -> dict
- Mirrors the logic that was previously inline in routing, but now encapsulated in its own specialist node.
- Good separation: the agent owns the lookup + response building.
- Comments note that persist will be added later for internal coordination.
- Matches "proper agent" goal and "supervisor remains thin" principle.

## Issues / Notes
- None critical. The agent is not yet wired into the graph (correct per prompt; that's 1070/1100).
- The new test is a nice addition even though not strictly required by the prompt.
- Still uses the CoreIdentity facade (as instructed); full ownership can evolve later.

**Recommendation:** Strongly approve. This is exactly the "proper agent for managing core data" that was needed.

**Follow-up:** Wiring into graph + routing changes (tasks 1070, 1100).

Reviewed by Grok (as requested by user).
