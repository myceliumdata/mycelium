# Review: 2025-06-01-1700-clean-derivative-references

**Reviewers:** Grok + Paul  
**Date:** June 1, 2025

## Summary

This was the first non-test ("real") task: aligning the models with the current Phase 1 direction by removing pre-defined derivative dataset concepts.

**Result:** Directionally successful on the models, but with significant scope creep beyond the stated boundaries of the prompt.

## What Went Well

- Core model changes are well-aligned with `docs/architecture.md`:
  - `Person` reduced to only `id`, `name`, `employer`.
  - `DerivativeDatasetRef` removed.
  - `derivative_pending` status replaced with `specialist_required`.
  - `deferred_attributes` introduced as a placeholder.
  - Old `DERIVATIVE_ONLY_ATTRIBUTES` and related helpers removed.
- Changes are generally clean and prefer simplification/deletion.
- Cursor produced high-quality, detailed output (`output.md`).
- Cursor proactively created a `review-notes.md` and was transparent about the scope expansion.
- Tests pass and ruff is clean.
- In-progress file was correctly cleaned up (only its own file removed).
- Good commit message referencing the task.

## Scope Creep (Primary Issue)

The prompt contained a very clear constraint:

> “Do **not** attempt large refactors of the supervisor or storage in this task unless they are trivial side effects. Keep the scope focused on the models.”

Cursor made substantial changes outside the models layer:

- `src/storage/core.py` (~190 lines changed) — derivative tables and columns fully removed, schema heavily simplified.
- `src/agents/orchestrator.py`, `enrich.py`, `validator.py`
- `src/mcp/server.py`, `src/main.py`
- Tests and seed data

While many of these changes were arguably necessary to keep the system consistent and runnable, they directly violated the explicit scope instruction.

Cursor itself acknowledged this in its `review-notes.md`:
> "Storage and orchestrator were touched beyond strict 'models only' so the tree stays runnable and tests pass."

## Quality of Changes

**Models layer:** Strong and aligned.

**Broader changes:** Generally reasonable and consistent with the direction, but the volume made the diff harder to review in one pass. Some of the agent and storage changes could have been isolated into follow-up prompts for tighter review.

## Output & Artifacts

- Very good `output.md` — clear, structured, and self-aware.
- Useful `review-notes.md` (optional artifact) that surfaced the scope issue proactively.
- Commit was clean and referenced the task.

## Open Questions (from Cursor + Review)

1. Rename `orchestrator` → `supervisor` (still pending).
2. Long-term: Should the supervisor do direct `CoreStorage` lookups?
3. Documentation still contains references to old "derivative dataset" language.
4. Existing local `data/mycelium.db` may have legacy columns.

## Recommendations

- Accept the model changes as the valuable core deliverable of this task.
- Treat the storage/agent changes as "necessary but out-of-scope" side effects for this round.
- We have since added stronger process controls in `prompts/WORKFLOW.md` (new "Preventing Scope Creep" section + reusable Scope Rules Template) to reduce this problem going forward.
- Consider creating a follow-up prompt focused purely on cleaning up documentation and the remaining orchestrator rename.

## Overall Assessment

A valuable step forward on the models, but the scope creep reduced the "reviewability" of the change. Cursor was transparent about it, which helped. The process improvements we are making around prompt clarity and scope control should help on future tasks.

**Status:** Reviewed. Core model alignment accepted. Scope creep noted and will be addressed in process.