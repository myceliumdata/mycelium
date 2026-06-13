# Program 2 — Slice 3: Polish (dynamic bind + research deference)

## Summary

Closed Program 2 with fully dynamic `mvr.bind_fields` on create-on-deliver, research **operator deference** in prompts (while still allowing new research versions), and post-ship docs/hygiene.

## Changes

| Area | Change |
|------|--------|
| **`src/agents/target_deliver.py`** | `bind_provisional_from_scope` iterates `load_mvr().bind_fields` and passes only mapped scope values to unified write |
| **`src/agents/attribute_write.py`** | Documented CRM v1 cache/`bind_index` limits for extra bind fields |
| **`src/tools/research.py`** | `operator_overrides_for_target_fields`, `_current_actor_kind`; operator block in prompts; `_persist_field_version` allows append when current actor is `operator` |
| **`research/_operator_deference.j2`** (new) | Prompt block: prefer operator value; override only with very strong evidence; else `na` |
| **Tests** | Dynamic bind-field create-on-deliver; operator prompt injection; operator → research `v2` append |
| **Docs** | `crm/README.md`, `onboarding.md`, `next-chunk-prep.md`, `attribute-provenance-and-storage.md`, `architecture.md` |

## Operator deference (P2-6)

When a target field’s current version has `actor.kind == "operator"`, research prompts include:

```
OPERATOR OVERRIDE (deference required):
- email: manual@corp.com (set 2026-06-12T…; note: Verified by operator)
```

Research **may** still append `v2` — `_persist_field_version` no longer short-circuits on operator-current `found` values.

## Verification

```bash
./bin/ci-local
# CI local: all steps passed.
# 378 passed, 26 deselected
```

Skipped optional `payment_required` smoke (deferred from M10; not flaky to add in this slice).

## For Grok + Paul

- **Slice complete** — Program 2 finished (Slices 1–3).
- **Hands-on:** Create-on-deliver with custom `mvr.bind_fields` writes all mapped fields to specialist storage; operator-set email in storage → research prompt shows OPERATOR OVERRIDE block.
- **Program 3 next** — admin operator edit UI + force re-research.
- **Not committed** — awaiting review.
- **TODO.md:** Mark Program 2 complete; queue Program 3 when ready.

Suggested commit message:

```
feat: close Program 2 with dynamic bind fields and research operator deference

Generalize create-on-deliver bind collection from mvr.bind_fields; inject
operator deference into research prompts; allow research to append versions
over operator-current values; update docs for taxonomy-owned MVR storage.
```
