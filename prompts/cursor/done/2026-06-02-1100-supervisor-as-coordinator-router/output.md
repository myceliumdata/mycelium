# Output: Supervisor as coordinator / router

## Design

Split supervisor responsibilities into three modules so `supervisor.py` only coordinates:

| Module | Role |
|--------|------|
| `agents/routing.py` | Classify graph state; delegate find/persist via accessor; return `SupervisorDecision` |
| `agents/responses.py` | Build `PersonResponse` for each outcome |
| `agents/core_identity.py` | Phase 1 facade over `CoreStorage` (`find_by_key`, `persist`) |
| `agents/person_prep.py` | `ensure_person_id` (used by enrich, not supervisor) |
| `agents/supervisor.py` | Coerce state → `evaluate_supervisor_turn` → apply route/response |

`supervisor.py` no longer imports `get_storage`, `find_person`, or `upsert_person`.

## Before / after (supervisor)

**Before:** ~150 lines with inline storage calls, response construction, and routing.

**After:** ~45 lines — `evaluate_supervisor_turn` + `_apply_decision` only.

## Data access delegation

```text
supervisor_agent → evaluate_supervisor_turn → CoreIdentityAccessor → get_storage()
```

Ingest persist after validation runs in `routing.evaluate_supervisor_turn` via `accessor.persist()`, not in the supervisor module body.

## Files added / modified

| Path | Change |
|------|--------|
| `src/agents/core_identity.py` | **New** — identity facade + test reset |
| `src/agents/routing.py` | **New** — routing decisions |
| `src/agents/responses.py` | **New** — response builders |
| `src/agents/person_prep.py` | **New** — `ensure_person_id` moved from supervisor |
| `src/agents/supervisor.py` | Thin coordinator |
| `src/agents/enrich.py` | Import `person_prep` |
| `docs/architecture.md` | "Supervisor as coordinator" subsection |
| `tests/test_core_graph.py` | Reset `core_identity` in fixture |
| `tests/test_supervisor_routing.py` | **New** — stub accessor tests |
| `TODO.md` | Marked supervisor refactor complete; follow-ups added |

## Verification

- `uv run pytest` — **8 passed**
- `uv run ruff check src tests` — clean
- Lookup, missing, non-core, ingest flows unchanged at the `PersonResponse` level

## Remaining gaps (documented in TODO)

- `CoreIdentityAccessor` still wraps shared storage (no specialist agent yet).
- Non-core attributes are detected in routing but not delegated to real specialists.
- Response builders remain centralized in `responses.py` (could split per specialist later).

## In-progress cleanup

Removed only `prompts/cursor/in-progress/2026-06-02-1100-supervisor-as-coordinator-router.md`.
