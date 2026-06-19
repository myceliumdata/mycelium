# Review — baseball intent normalization (M4b)

**Verdict:** **Approved**

**CI:** `./bin/ci-local` — **580** smoke passed, ruff clean, admin-ui build ok.  
**Baseball E2E:** `./bin/smoke-baseball-e2e` — 13 scenarios passed.  
**M4b pytest:** 22 passed (intent map, normalization, dedup e2e, llm_models + derive regressions).

---

## Scope reviewed

| Area | Files |
|------|--------|
| Intent map | `src/network/intent_map.py` |
| Intent LLM | `src/network/intent_normalization.py` |
| Warehouse context extract | `src/network/warehouse_context.py` |
| Model env | `src/utils/llm_models.py` — `intent_normalization_model()` |
| Batting derive path | `batting_specialist.py`, `derive_resolve.py` |
| Provenance deliver | `query_provenance.py` — slug fallback + `parameters.attribute` rewrite |
| Tests | `test_intent_map.py`, `test_intent_normalization.py`, `test_baseball_intent_dedup.py` |
| Docs | `.env.example`, hand-test M4b-1 row |

---

## Design alignment

| Lock | Shipped |
|------|---------|
| `intent_map.json` per network | Yes — atomic save, versioned mappings |
| Split models | Yes — `MYCELIUM_INTENT_NORMALIZATION_MODEL` vs computation codegen |
| Slug shape `[a-z0-9_]+` max 64 | Yes — validate + one retry |
| Storage under intent slug | Yes — test asserts `career_batting_average` in storage, not `career_avg` |
| Deliver requested label | Yes — `results.career_avg` / `results.batting_average` |
| Provenance both fields | Yes — `attribute` + `intent_slug`; query provenance rewrites attribute on slug hit |
| No second codegen on synonym | Yes — e2e `codegen_counter == 1` after two delivers |
| Legacy read | Yes — requested-key fallback before derive |

---

## Strong points

- `warehouse_context.py` extraction removes duplication; pack `derive_resolve` slims down cleanly.
- `query_provenance` slug fallback closes the UX gap (client sees requested label in provenance when cache is under slug).
- E2e test proves storage layout, map persistence, codegen call count, and provenance shape.

---

## Polish nits (non-blocking)

| # | Item |
|---|------|
| P1 | ~~Hand-test summary table row `batting_average`~~ — fixed in gate doc pass |
| P2 | No `intent_dedup_mocked` smoke scenario (pytest-only per prompt — acceptable) |
| P3 | Intent LLM still called on second synonym (`intent_calls == 2`) even when slug cache hit — expected v1 (map warms per label); could skip LLM when slug storage hit before intent resolve in a future polish |

---

## Operator (Paul)

```bash
MYCELIUM_INTENT_NORMALIZATION_MODEL=gpt-4o-mini
MYCELIUM_COMPUTATION_CODEGEN_MODEL=gpt-4o
```

Clear batting `storage.json` + `intent_map.json`; manual M4b-1: `career_avg` then `batting_average`.

**Manual gate:** ✅ **CLEAR** 2026-06-19 — Aaron `0.305` both labels; shared timestamp + `intent_slug: career_batting_average`; no second codegen. [`docs/manual-checks/2026-06-19-baseball-m4b-intent-normalization-gate.md`](../../../../docs/manual-checks/2026-06-19-baseball-m4b-intent-normalization-gate.md)

---

## Commit

```
baseball: intent normalization for derive cache dedup (M4b)
```