# Review: 2026-06-09-1530-eliminate-core-reprocess

## Status

Reprocessed successfully after the backout. Cursor executed the 1530-eliminate-core slice and delivered prompt.md + output.md (no review.md created, per the workflow instruction in the prompt).

This slice removes the privileged `core_data` specialist entirely. Name/identity resolution and direct responses (when no non-core attrs) now come from `agents.seed` (via `find_by_key`) + `supervisor_agent`. Dispatch only triggers for classified specialist routes.

## What Cursor Delivered

- `src/agents/core_data.py`: Deleted entirely.

- `src/agents/supervisor.py`:
  - Imports `find_by_key` from `agents.seed`.
  - Resolves `matched = find_by_key(query.person_key)`.
  - Builds `matched_persons`, `context` (with "seed" + empty "specialists"), `current_person_id`.
  - Uses `_identity_records_from_seed` / `_persons_from_seed` (with person_id handling).
  - When `classifications` require specialists: creates via factory if needed, sets `route`.
  - When `route is None` (no attrs or direct seed case): builds `response` directly using `response_found` / `response_non_core` / `response_not_found` with `base_records=identity_records`.
  - Still performs on-demand specialist creation for classified categories.
  - Docstring updated for seed resolution + direct responses.

- `src/agents/dispatch.py`:
  - `specialist_dispatcher`: if no `route`, returns {}; else `get_agent_fn(target)`, raises `RuntimeError` if unregistered. No core fallback.

- `src/agents/registry.py`:
  - `_SEED_REGISTRY` now has empty `"agents": {}`.
  - Comments updated: "No privileged core agent."
  - `has_agent`, etc. now only for generated specialists.

- `data/agent_registry.json`:
  - `core_data` entry removed; only the 6 generated specialists remain.

- `src/agents/__init__.py`:
  - Only exports `supervisor_agent`.

- `bin/reset-mycelium`:
  - Removed any `CORE_AGENT_NAME` / core preserve logic.

- Tests:
  - `tests/test_core_data_agent.py`: Now a module-level skip with explanatory comment.
  - Updates to `test_core_graph.py`, `test_supervisor_routing.py` for new paths (no core agent).

- Graph (`src/graphs/core.py`): Unchanged routing logic (supervisor → conditional on route → specialist or END), now naturally routes direct seed responses to END without dispatch.

## Verification (re-executed during this review)

```text
$ uv run pytest -m smoke -q
.........................                                                [100%]
25 passed, 9 deselected in 0.43s
```

(Note: 25 vs. prior 28 due to removal of core_data test paths; expected.)

```text
$ uv run pytest -m full -q -k "query_existing_person or query_missing_person or query_non_core_attributes"
...                                                                      [100%]
3 passed, 31 deselected in 0.11s
```

```text
$ uv run ruff check src/agents/supervisor.py src/agents/dispatch.py src/agents/registry.py src/agents/__init__.py tests/test_core_graph.py tests/test_supervisor_routing.py tests/test_core_data_agent.py bin/reset-mycelium
All checks passed!
```

```text
$ uv run bin/reset-mycelium --dry-run --all
... (shows specialists to remove, no core_data logic; base/categories/DB reset plan)
```

```text
$ git diff --stat ... (core_data.py deleted, supervisor/dispatch/registry/__init__/registry.json/reset-mycelium/tests updated)
```

Targeted runtime grep (supervisor, dispatch, registry, graphs/core, reset-mycelium): no `core_data` references.

Full project grep shows only legacy comments in pre-1530 historical artifacts, specialist headers (to be updated in 1540+), classification models (transitional), and the via guard in responses.py (expected until core elimination complete).

## Scope Adherence

Strictly limited to the 1530 slice per the redesign_reset.md bullet and prompt:

- core_data.py deleted.
- dispatch.py: no fallback, raises.
- registry + agent_registry.json: no core_data (seed empty).
- supervisor.py: seed via find_by_key, direct responses from seed (with base_records), still plans/creates specialists.
- __init__.py, bin/reset-mycelium, tests (test_core_data_agent.py now skip).
- Graph clean (no special core paths).
- Queries now resolve via seed path.
- reset-mycelium dry-run works without core preserve.

No changes for later slices (no specialist template updates, no context builder nodes, no UUID exposure, no prepare_seed, etc.). Responses.py changes visible in diff are from prior 1520 slice.

Lingering `prompts/cursor/next/2026-06-09-1520-unify-responses-reprocess.md` still present (as noted in 1520 review); 1530 source was properly consumed/processed into done/.

## Observations

Positive:
- Clean removal of the privileged core layer. Supervisor now owns seed identity resolution and direct "found" responses for name-only / core-only queries.
- Uses the post-1520 unified builders with `base_records` (prepares for context passing).
- Dispatch is now purely for registered specialists; unknown routes error (good for safety).
- Registry seed is empty; only factory-generated specialists.
- Test for core_data is now explicitly skipped with reason.
- reset-mycelium updated; dry-run confirms no core handling.
- Smoke/full still green; number of tests reduced appropriately.

Transitional / expected (will be addressed in follow-on slices):
- Specialist .py files (and some docstrings/comments in classification, core_identity, factory, responses) still contain "core_data" references in text (headers say "peer to core_data"). These will be cleaned when templates are updated and specialists re-generated (1540/1600).
- responses.py still has `specialist != "core_data"` guard in via_suffix (transitional until 1530+ effects fully land and 1710 removes core person fields).
- Docs, README, plans, historical done/ outputs, and some src/ comments still reference old core model (out of scope for 1530; capstone slices will refresh).
- `current_person_id` etc. from 1510 are now populated in supervisor (good).

No scope creep. Cursor followed claiming, did discovery on the listed files, made exactly the changes in the spec, ran the right verifs (smoke + full + ruff + reset dry-run + grep), produced clear summary + "Ready for next", and delivered only prompt + output.

## Comparison to Spec

Fully matches the 1530 bullet in `prompts/resets/2026-06-07_redesign_reset.md`:

> core_data.py deleted. dispatch.py: no core fallback, raises on unknown route. registry.py + data/agent_registry.json: no core_data entry (seed now empty agents). supervisor.py: seed resolution via find_by_key, direct responses from seed when no specialists needed, still plans/creates real specialists. __init__.py, bin/reset-mycelium, tests updated (test_core_data_agent.py now just skip). Graph clean. Queries now use seed path. reset-mycelium dry-run works. No core_data in runtime.

All items implemented and verified. Direct seed responses, find_by_key usage, base_records in responses, empty registry seed, deletion, raise behavior, skip test, dry-run, and runtime grep all confirm.

## Verdict / Readiness

Excellent, faithful reprocess. This is a pivotal slice: the "core is special" era is over. Supervisor + seed now handle identity and direct responses; specialists are purely for classified non-core attributes via the registry. Everything is set up for the specialist template updates (1540) and context builder (1550).

**Ready for the next reprocess slice: 2026-06-09-1540-specialist-template-base-reprocess.md in next/**.

(End of review. This is the substantive review added by Grok after Cursor delivery.)
