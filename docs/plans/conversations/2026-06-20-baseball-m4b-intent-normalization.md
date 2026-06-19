# M4b — intent normalization (label → canonical slug)

**Date:** 2026-06-20  
**Participants:** Paul + Grok  
**Status:** Shipped — manual gate **CLEAR** 2026-06-19 (`5fdf865`; [`docs/manual-checks/2026-06-19-baseball-m4b-intent-normalization-gate.md`](../../manual-checks/2026-06-19-baseball-m4b-intent-normalization-gate.md))  
**Builds on:** M4 (`derive_on_miss`), M3c derive pipeline

---

## Problem (M4 v1)

Cache key = normalized **requested label**. `career_avg` and `batting_average` are the same stat but separate storage rows and duplicate LLM codegen.

---

## Solution

Before cache lookup / derive on manifest miss:

1. Normalize requested label (existing `strip().lower()`).
2. Resolve **intent slug** — LLM (`MYCELIUM_INTENT_NORMALIZATION_MODEL`) with domain + warehouse context; structured `{ intent_slug, confidence }`.
3. Validate slug shape (attribute convention); reject/retry on violation.
4. Consult **`intent_map.json`** at network root (label → slug); persist new mappings.
5. Cache read/write under **intent slug** only.
6. On cache hit or after derive: return value under **requested label** in `results[]`.

Codegen + semantic review unchanged; uses **`MYCELIUM_COMPUTATION_CODEGEN_MODEL`** only.

---

## Paul locks

| Topic | Lock |
|-------|------|
| Intent resolution | LLM intent slug (not static glossary) |
| Models | Split: cheap intent model vs expensive computation codegen |
| Slug shape | Non-empty snake_case `[a-z0-9_]+`, max 64 — same as attribute normalization |
| Persistence | `intent_map.json` per `network_root` |
| Map scope | Per network (global across entities) |
| Deliver | `results[]` key = **requested** label only — never rewrite to canonical slug (same UX rule as retired “first team” display: don’t substitute a different key than the client asked for) |
| Provenance | Both requested label + `intent_slug` on version (operator/debug replay) |
| Protocol | Still `requested_attributes` — no M5 `question` field |

---

## Guinea pig

Aaron: deliver `career_avg` (derive) → deliver `batting_average` → cache hit on shared intent, **no second codegen**.

---

## Non-goals (M4b v1)

- M5 natural language `question`
- Cross-network intent map
- Pitching/bio domains unless trivial `derive_on_miss` extension

---

*Archived June 2026.*