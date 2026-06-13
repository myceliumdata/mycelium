# Review — Program 2 Slice 3 (polish)

**Verdict:** **Approved + polish nits**  
**Reviewer:** Grok  
**Date:** 2026-06-13  
**CI (Grok):** `./bin/ci-local` — **378 passed**, 26 deselected; ruff clean; admin-ui build ok.

---

## Scope vs spec

| Requirement | Status |
|-------------|--------|
| Dynamic `mvr.bind_fields` on create-on-deliver | ✅ `bind_provisional_from_scope` iterates MVR + scope lookup |
| Document CRM v1 cache/`bind_index` limits | ✅ `_apply_cache_field` / `_cache_values` docstrings |
| Research operator deference in prompts | ✅ `operator_overrides_for_target_fields` + `_operator_deference.j2` |
| Allow research append over operator-current (P2-6) | ✅ `_persist_field_version` bypass when `actor.kind == operator` |
| Tests: dynamic bind, operator prompt, operator→v2 | ✅ `test_attribute_write`, `test_research` |
| Docs: crm README, onboarding, next-chunk-prep, storage | ✅ |
| Hygiene grep | ✅ living docs updated; no stale “registry-only MVR” left in active paths |
| Optional `payment_required` smoke | Skipped (documented; deferred from M10) |
| Out of scope: operator edit UI, `bind_versions[]` | ✅ |

---

## What works well

1. **Minimal dynamic bind change** — filters scope lookup to declared `mvr.bind_fields` only; still delegates to unified write.
2. **P2-6 honored end-to-end** — prompt deference + persist path allows `v2` append; test proves two versions with research winning current pointer.
3. **Template isolation** — `_operator_deference.j2` mirrors peer/disambiguation fragment pattern; easy to tune copy without touching Python.
4. **`versioned_operator` fixture** — reusable for Program 3 operator-write tests.

---

## Nits (non-blocking)

| # | Finding | Suggestion |
|---|---------|------------|
| N1 | **Prompt block ordering** — when both `operator_overrides` and `peer_display` exist, peer insert uses same `insert_at` as operator and can appear *before* operator deference. | Program 3 or research polish: compute insert index from blocks already inserted. |
| N2 | **Slice 1 carry-forward** — multi-specialist writes still not atomic; extra bind fields not denormalized on entity row beyond name/employer. | Documented; Program 3 or later if needed. |
| N3 | **`attribute-provenance-program2.md` header** still said “Slice 1 queued” | Grok fixes in commit. |

---

## Program 2 complete

Slices 1–3 shipped locally. **Program 3** next (operator edit UI + force re-research). Optional Paul manual gate before Program 3 kickoff.

---

## Next steps

1. **Grok:** commit locally (done with this review).
2. **Paul + Grok:** `TODO.md` bump when ready; queue Program 3 spec/prompt.
3. **Push:** when Paul says deliver — 3 commits ahead of `origin/main` (Slices 1–3).