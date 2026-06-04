# Review: 2026-06-09-1540-specialist-template-base-reprocess

## Status

Reprocessed successfully after the backout. Cursor executed the 1540-specialist-template-base slice and delivered prompt.md + output.md (no review.md created, per the explicit instruction in the prepared prompt).

This slice updates the Jinja2 template for generated specialists (and supporting code) to the seed-data-context model: person_id/context/target_fields resolution, 3 scenarios (found/pending/na), specialist_contrib return value, unified base_records builders, daemon-thread stub for research, and the exact robustness TODO.

Committed specialist .py files were intentionally left untouched (regeneration is 1600).

## What Cursor Delivered

- `src/agents/factory/templates/specialist_agent.py.j2`:
  - New header: "Records are keyed by person_id (stable UUID from seed loader). See agents/specialists/base.py."
  - "First-class owner of {{ category }} data in the seed + specialist context model."
  - "Receives context, person_id, and owned fields from supervisor/graph (not CoreIdentity)."
  - Explicit "Three scenarios (seed-data-context redesign):" with 1/2/3 descriptions.
  - `_resolve_person_id`, `_resolve_owned_fields`, `_identity_from_context`.
  - `_field_has_value`, `_field_is_pending`, `_field_is_na`, `_field_display_value`.
  - `_stub_background_research` (placeholder).
  - `_start_research_if_needed` (marks pending, saves, starts daemon=True thread).
  - `_evaluate_owned_fields` (applies the 3 scenarios per field, returns values + overall status).
  - Specialist fn: uses `current.context`, `current.current_person_id`, `current.target_fields`.
  - Returns `specialist_contrib` payload (person_id, category, fields, values, status).
  - Uses `base_records=identity_records` in `response_found` / `response_non_core`.
  - Returns additional state bags (matched_persons, classifications, context, current_person_id, target_fields).
  - The exact robustness TODO preserved:
    "# TODO: revisit this later to make sure it's robust — e.g., research thread dying and
    # leaving "pending" forever."
  - No `core_identity` / CoreIdentity usage.

- `src/agents/specialists/base.py`:
  - Comment in initial storage example:
    "# records keyed by person_id (uuid from seed loader), e.g.:
    # {\"<person-id>\": {\"email\": \"a@b.com\", \"phone\": {\"status\": \"pending\", ...},
    #                  \"linkedin\": {\"status\": \"na\"}}}"

- `src/agents/factory/agent_factory.py`:
  - `_refine_with_llm` prompt updated to reference new style:
    "thin _coerce, SpecialistStorage keyed by person_id, context + target_fields, 3 scenarios, specialist_contrib, response builders"

- `tests/test_agent_factory.py`:
  - Asserts in creation test: "core_identity" not in text, "person_id" in text, "specialist_contrib" in text, "not currently available but may be in the future" in text.
  - New manual test block using `MyceliumGraphState` with `current_person_id`, seed context containing person_id, `target_fields=["email"]`.
  - Invokes, asserts `specialist_contrib.status == "pending"`, message contains the pending phrase, and storage written with `records[person_id]["email"]["status"] == "pending"`.
  - Minimal smoke marker updates (tests remain under -m smoke).

- No changes to committed `src/agents/specialists/*.py` files (explicitly noted in output.md; correct per scope).

## Verification (re-executed during this review)

```text
$ uv run ruff check src/agents/specialists/base.py src/agents/factory/agent_factory.py tests/test_agent_factory.py
All checks passed!
```

```text
$ uv run pytest -m smoke -q tests/test_agent_factory.py
....                                                                     [100%]
4 passed in 0.35s
```

```text
$ uv run pytest -m smoke -q
.........................                                                [100%]
25 passed, 9 deselected in 0.36s
```

Manual exercise (via the updated test, re-run above): factory create + dynamic load + invoke with person_id + target_fields exercises pending path, writes status to storage, returns correct contrib + message. Matches spec.

`git diff --stat` shows only the four expected files (template has the bulk of the redesign).

## Scope Adherence

Strictly limited to the 1540 slice per the redesign_reset.md bullet and prompt:

- Only specialist_agent.py.j2 (full template redesign per spec), base.py (person_id comment), agent_factory.py (refine prompt), test_agent_factory.py (marker + manual invoke test).
- Explicitly did **not** regenerate the committed specialists under src/agents/specialists/ (that is 1600).
- No supervisor/graph/context builder changes (1550), no core elimination (already done), no seed loader, no responses unification (1520), etc.

The prompt file in `next/` was properly consumed (not present in current next/).

## Observations

Positive:
- Template now fully encodes the 3 scenarios, person_id/context/target_fields resolution, specialist_contrib, daemon stub, and unified builders with base_records.
- The robustness TODO is present verbatim as required.
- Test now actually exercises the new pending path with proper state (current_person_id, target_fields, context seed) and verifies storage side-effect + contrib.
- Factory refine prompt kept in sync.
- Scope discipline excellent: no over-regeneration of live specialists.

Transitional / expected (addressed in later slices):
- The 6 committed specialist .py files still have old headers (mention "core_data", pre-redesign structure, old generation dates). They will be refreshed in 1600 (after --specialists reset + re-gen).
- The `_stub_background_research` is still a no-op placeholder (as designed; real LLM+tools research deferred).
- Some legacy "core_data" comments remain in classification, core_identity, older docs/historical outputs, and the via_suffix guard in responses.py (until 1710+).
- The specialists still import and use the old-style response builders in places, but the new template paths use base_records correctly.

No scope creep. Cursor documented the claim, did targeted discovery, made precisely the listed changes, ran smoke + ruff + manual test, noted the regeneration boundary clearly, and produced "Ready for next".

## Comparison to Spec

Fully matches the 1540 bullet in `prompts/resets/2026-06-07_redesign_reset.md`:

> Updated specialist_agent.py.j2 (header, removed core_identity, added person_id/context/target_fields resolution, full 3 scenarios with _start_research_if_needed + daemon thread stub + pending/na/found logic + specialist_contrib, robustness TODO exact quote, uses unified builders with base_records). base.py: comment on person_id keys in records. agent_factory.py: refine prompt updated. test_agent_factory.py minimal marker updates. Smoke green. Manual tmp factory create + dynamic load/invoke test exercises scenarios correctly (pending path writes status, returns correct contrib/message).

All elements present and verified (TODO quote exact, manual test does exactly the pending/storage/contrib exercise, no premature regen).

## Verdict / Readiness

Excellent, faithful reprocess. This is the key template update that makes the specialist side of the new model concrete. The 3 scenarios, person_id/context flow, contrib payload, and pending research stub are now in the generator. Everything lines up for the supervisor context/graph work in 1550 and the full re-gen + capstone in 1600.

**Ready for the next reprocess slice: 2026-06-09-1550-supervisor-context-graph-reprocess.md in next/**.

(End of review. This is the substantive review added by Grok after Cursor delivery.)
