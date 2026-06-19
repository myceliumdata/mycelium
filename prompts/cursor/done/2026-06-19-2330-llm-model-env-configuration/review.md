# Review — LLM model env configuration (2330)

**Verdict:** **Approved** (v1 foundation; naming/docs completed in remediation `2026-06-20-0900`)

**CI:** `./bin/ci-local` — 579 smoke passed, ruff clean, admin-ui build ok.

---

## Scope reviewed

Central `src/utils/llm_models.py`; wiring to classification, ontology, research, alias expansion, agent factory refine, baseball `derive_resolve`; `.env.example` block; `docs/architecture.md`; `tests/test_llm_models.py`; classification `model_used` on classify persist paths.

Remediation slice superseded `MYCELIUM_DERIVE_MODEL` → `MYCELIUM_COMPUTATION_CODEGEN_MODEL` before commit — see sibling review.

---

## What works

- Single `FALLBACK_MODEL` constant; no scattered `gpt-4o-mini` in `src/` hot paths or baseball specialists.
- `model=` removed from `classify` / `refresh_from_llm` / `generate_skeleton_ontology` public APIs.
- Alias expansion reads model at invoke time (not import time).
- `classify()` sets `model_used` on successful apply and `_cache_as_unknown`.
- Tests cover unset, empty, and per-accessor env set.

---

## Known limitations (accepted for v1; strict redesign on TODO)

- Unset vars silently fall back to `gpt-4o-mini` — Paul lock: **strict (review)** item tracks required provider+model + startup hard fail.
- No provider dimension (OpenAI-only call sites unchanged).
- `output.md` table still says `MYCELIUM_DERIVE_MODEL` / “Baseball derive” — historical artifact; shipped docs corrected in remediation.

---

## Polish nits (non-blocking)

| # | Item |
|---|------|
| P1 | `src/agents/classification/models.py` comment example still `gpt-4o-mini` — optional update to “env-configured model”. |
| P2 | Hand-test doc notes “default `gpt-4o-mini`” — accurate for v1; revise when strict config lands. |

---

## Commit

Bundled with remediation slice in one commit (same working-tree hunk set).