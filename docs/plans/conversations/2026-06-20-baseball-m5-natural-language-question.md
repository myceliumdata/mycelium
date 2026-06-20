# M5 — natural language `question` → intent → deliver

**Date:** 2026-06-20  
**Participants:** Paul + Grok  
**Status:** **Deferred — unlikely to implement** (June 2026)  
**Index:** [`docs/plans/unlikely/README.md`](../unlikely/README.md) — not on `TODO.md`  
**Builds on:** M4 (`derive_on_miss`), M4b (intent slug + `intent_map.json`), M3c derive pipeline

---

## Decision record (why we are not doing this)

**Conclusion:** Do **not** add a `question` field to `EntityQuery`. The warehouse derive **M track ends at M4b** for product purposes.

### Who would have been the client?

| Caller | Reality |
|--------|---------|
| **Claude + MCP** (baseball demo) | Already translates NL → `requested_attributes` before `query_entity`. Server-side NL parsing duplicates the host LLM. |
| **CLI / operators** | Send labels or read `describe_network` / hand-test docs. |
| **Anonymous agents** | Not a near-term baseball consumer. |
| **Thin non-LLM API clients** | Hypothetical (dumb form, fixed integration). None on the roadmap. |

### Why M4b is enough

- Free-form labels (`ops`, `career_avg`) + **intent slug dedup** (M4b) cover the server-side factory value: cache, derive, provenance, synonym collapse.
- Natural language belongs in the **MCP host** (agent/client), not in the structured two-step wire protocol — consistent with [`docs/architecture.md`](../../architecture.md) (CLI/MCP expose lookups via `EntityQuery`, not caller prose).

### Cost of M5 if we built it

- Extra server LLM call per query (intent model), latency, protocol surface, tests, and docs — for a path the demonstrated client does not use.

### What we keep from this doc

- Design locks below remain valid **if** assumptions change (e.g. a committed non-LLM product surface that posts user prose directly to Mycelium).
- Cursor prompt archived cancelled: `prompts/cursor/done/2026-06-20-1400-baseball-natural-language-question-m5/`.

---

## Problem (M4b ceiling) — original design

Clients must speak **attribute labels** in `requested_attributes` — even free-form labels like `ops`. Agentic users ask **natural language** (“What was Hank Aaron’s career batting average?”). The factory should accept that without a new protocol later.

M4b solved **synonym dedup among labels** (`career_avg` ↔ `batting_average`). M5 solves **question → canonical intent** so the same specialist cache and derive path applies.

---

## Solution (framework lift)

Step 1 may send **`question`** (NL string) **instead of** `requested_attributes`.

1. **Resolve question → intent** — LLM (`MYCELIUM_INTENT_NORMALIZATION_MODEL`) with warehouse manifest + network ontology context; structured `{ intent_slug, confidence }`.
2. Validate slug (`[a-z0-9_]+`, max 64); reject/retry on violation; confidence threshold **0.7** (match M4b / classification).
3. **Persist** normalized question text → slug in existing **`intent_map.json`** (same per-network file; question string is just another map key).
4. **Expand for delivery** — treat resolved `intent_slug` as the sole virtual requested attribute for supervisor routing + specialist execution (step 1 issues delivery scope with `requested_attributes: [intent_slug]`).
5. **Store original question** on `DeliveryScope` for step-2 replay, provenance, and response echo.
6. **Cache / derive** — unchanged M4b + M3c path inside specialists (storage under slug).
7. **Return** — `results[]` key = **`intent_slug`**; echo original `question` on `QueryResponse` (step 2).

Codegen unchanged; **`MYCELIUM_COMPUTATION_CODEGEN_MODEL`** only on manifest miss derive.

---

## Paul locks

| Topic | Lock |
|-------|------|
| Protocol | Step 1: **`question` XOR `requested_attributes`** (mutually exclusive when non-empty). Identity-only queries (neither set) unchanged. |
| Question shape | Single string v1; no `questions[]` array |
| Intent resolution | LLM intent slug (not static glossary); **reuse `intent_normalization_model()`** — same subsystem as M4b label→slug |
| Slug shape | `[a-z0-9_]+`, max 64 |
| Persistence | Same `intent_map.json`; key = whitespace-collapsed, lowercased question text |
| Delivery expansion | `requested_attributes` on issued scope = `[intent_slug]` |
| Storage / cache | Under **intent slug** only (M4b) |
| `results[]` key | **`intent_slug`** for question queries (client did not supply a label) |
| Response echo | `QueryResponse.question` = original step-1 question on step-2 deliver |
| Provenance | `parameters.question`, `parameters.intent_slug`, `parameters.attribute` = intent_slug |
| Step 2 | Still `delivery_id` only — question bound on scope, not re-sent |
| Classification | Supervisor `classify(intent_slug)` — ontology routes domain; no stat glossary in `attribute_map` |
| Domains v1 | Batting `derive_on_miss` guinea pig; manifest-hit stats (e.g. `career_hr`) must route without derive |

---

## Wire protocol

**Step 1 — question (derive guinea pig):**

```json
{
  "lookup": {"player": "Hank Aaron"},
  "question": "What was Hank Aaron's career batting average?",
  "provenance": true
}
```

**Step 1 — manifest hit (routing guinea pig):**

```json
{
  "lookup": {"player": "Hank Aaron"},
  "question": "How many career home runs did Hank Aaron hit?",
  "provenance": true
}
```

**Step 2:**

```json
{
  "delivery_id": "d_…"
}
```

**Step 2 response shape (question path):**

```json
{
  "outcome": "assembled",
  "question": "What was Hank Aaron's career batting average?",
  "results": [
    {
      "id": "ba05e94b-…",
      "career_batting_average": "0.305"
    }
  ]
}
```

`requested_attributes` path unchanged — M4b deliver rules still apply (results key = requested label).

---

## Guinea pigs

| # | Scenario | Expect |
|---|----------|--------|
| M5-1 | Aaron career BA question (clear batting cache) | Derive ≈ **0.305**; `results.career_batting_average`; `question` echoed |
| M5-2 | Same question after M5-1 | Cache hit; same timestamp; no second codegen |
| M5-3 | Cross-path dedup | After M4b `career_avg` derive, question → same slug → cache hit, no codegen |
| M5-4 | Manifest hit | HR question → **755** via `career_sum`; no LLM codegen |
| M5-5 | Regression | `requested_attributes: ["career_avg"]` unchanged (M4b rules) |

---

## Implementation sketch (framework)

| Layer | Change |
|-------|--------|
| `EntityQuery` | Optional `question: str` (step 1 only); validator XOR with `requested_attributes` |
| `DeliveryScope` | `question: str \| None`, `resolved_intent_slug: str \| None` |
| `src/network/question_intent.py` | `resolve_question_intent(question, *, manifest, categories_summary, paths, intent_map)` |
| `target_resolve` | Before `issue_delivery`, if `question`: resolve → set scope attrs + slug + question |
| `QueryResponse` | Optional `question` field |
| `query_provenance` | Emit `parameters.question` when scope had question |
| Specialists | No baseball-only fork — receive `intent_slug` as attr key; M4b path handles cache |

**Refactor note:** Extract shared LLM prompt builder from `intent_normalization.py` so label and question paths share slug validation + map persistence; question prompt adds ontology/manifest “what stat is being asked?” framing.

---

## Non-goals (M5 v1)

- Multiple questions per step 1
- `question` + `requested_attributes` in one request
- Cross-network intent map
- Pitching / bio / team-season question routing beyond what `classify()` already does
- M5b: skip intent LLM when slug storage already hit (M4b P3 polish — defer)
- Strict six-var LLM startup hard fail (separate slice)
- Deep provenance lineage expansion

---

## Risks

| Risk | Mitigation |
|------|------------|
| Question LLM returns wrong slug | Semantic review unchanged on derive; manifest hits are deterministic |
| classify() fails on novel slug | Same as M4 free-form labels — LLM classification with warehouse categories in context |
| intent_map bloat from varied phrasings | Slug-level specialist cache is the real dedup; map only avoids repeat intent LLM for exact question text |
| CRM networks get `question` | Framework-safe; guinea pig is baseball; CRM questions classify to research specialists as today |

---

*Archived June 2026.*