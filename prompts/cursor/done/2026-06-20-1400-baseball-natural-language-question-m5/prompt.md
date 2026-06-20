# Baseball natural language question (M5)

> **READY** — Claim per `prompts/cursor/WORKFLOW.md`.

**Design:** [`docs/plans/conversations/2026-06-20-baseball-m5-natural-language-question.md`](../../docs/plans/conversations/2026-06-20-baseball-m5-natural-language-question.md)

**Objective:** Step 1 accepts optional **`question`** (NL string) instead of `requested_attributes`. Framework resolves question → **intent slug**, issues delivery scope, routes through existing supervisor + batting `derive_on_miss` / M4b cache path. Step 2 echoes `question` on `QueryResponse`; `results[]` uses **intent_slug** as key.

**Principles:**

- Framework-owned question resolution — not baseball-only.
- Reuse **`intent_normalization_model()`** (same env var as M4b); computation codegen unchanged.
- **`question` XOR `requested_attributes`** when either is non-empty.
- **Do not edit `TODO.md`.**
- M4b label path regression must stay green.

---

## Paul locks (must implement)

| Lock | Requirement |
|------|-------------|
| XOR | Non-empty `question` forbids non-empty `requested_attributes`; validator error |
| Intent | `resolve_question_intent()` → validated slug; confidence ≥ 0.7 to persist |
| Map | Persist whitespace-collapsed lowercased question → slug in `intent_map.json` |
| Scope | `DeliveryScope.question` + `DeliveryScope.resolved_intent_slug`; `requested_attributes: [slug]` |
| Results | Question path: `results[].{intent_slug}`; label path: unchanged (requested label) |
| Echo | `QueryResponse.question` on step-2 deliver when scope had question |
| Provenance | `parameters.question`, `parameters.intent_slug`, `parameters.attribute` (= slug) |
| Domains | Batting derive guinea pig; manifest-hit HR question routes without codegen |

---

## Implement

### 1 — `EntityQuery` (`src/models/state.py`)

- Add `question: str | None` (step 1 only; default None).
- Validator: if delivery step, reject `question` (like `requested_attributes`).
- Validator: if both `question.strip()` and any non-empty `requested_attributes` → `ValueError`.
- Update JSON schema / examples for MCP.

### 2 — `DeliveryScope` (`src/network/delivery.py`)

- Add `question: str | None = None`
- Add `resolved_intent_slug: str | None = None`
- Extend `issue_delivery(...)` kwargs; backward compatible defaults.

### 3 — Question intent (`src/network/question_intent.py`)

- `normalize_question(text) -> str` — strip, collapse whitespace, lower.
- Pydantic `QuestionIntentProposal`: `intent_slug: str`, `confidence: float`
- `resolve_question_intent(question, *, manifest, categories: dict, paths, intent_map, llm_invoke=None) -> str`
  - Map hit on normalized question → return slug
  - LLM structured call with warehouse context (`format_warehouse_context`) + short category/domain summary from `categories.json`
  - Prompt: given NL question + domain context, emit canonical intent slug for the stat/computation asked
  - Validate slug; retry once on invalid; confidence threshold 0.7
  - Persist question → slug via `save_intent_mapping`
  - Below threshold or LLM failure → raise or return controlled error (prefer: fall back to slug derived from aggressive token extraction only if tests require — **default: fail loud with clear message in audit / N/A path**; design prefers no silent garbage slug)

**Refactor:** Share slug validation + map persistence with `intent_normalization.py` (extract `_validate_and_persist_slug` helper if clean).

### 4 — `target_resolve.py`

- Before `issue_delivery`, when `query.question` set:
  - Load manifest + categories + intent_map from network paths
  - `slug = resolve_question_intent(...)`
  - `issue_delivery(..., requested_attributes=[slug], question=query.question, resolved_intent_slug=slug)`
- Else existing path unchanged.

### 5 — Graph state + deliver

- When loading delivery scope for step 2, bind `delivery_scope_attrs` from scope (already does).
- Pass `scope.question` into graph state if needed for response assembly (add `delivery_scope_question: str | None` on `MyceliumGraphState` or read from re-loaded scope in assemble).

### 6 — `QueryResponse` + assemble

- Add optional `question: str | None` on `QueryResponse`.
- Step-2 assembled response: set `question` from delivery scope when present.
- Omit from JSON when None (field serializer / model config).

### 7 — Provenance (`src/agents/query_provenance.py`)

- When delivery scope has `question`, include `parameters.question` on versions.
- Question path: `parameters.attribute` = intent_slug (not full question text).

### 8 — Batting specialist

- **No protocol fork.** Receives `intent_slug` as attr key in `requested_attributes`.
- M4b `resolve_intent_slug(slug)` should map-hit or pass through when key already is canonical slug.
- Verify derive + cache paths work when incoming key is `career_batting_average` not `career_avg`.

### 9 — MCP / CLI

- `mycelium_mcp/server.py` — document `question` in tool description.
- `main.py` — optional `--question` flag if trivial; else MCP-only v1 is acceptable if CLI skipped (note in output.md).

### 10 — Tests

**`tests/test_question_intent.py`** — normalize; map hit skips LLM; mock LLM persists mapping; slug validation; low confidence behavior.

**`tests/test_entity_query_question.py`** — XOR validator; step-2 rejects question.

**`tests/test_baseball_question_deliver.py`** — e2e on minimal fixture:
- Mock question intent → `career_batting_average`
- Mock derive codegen (reuse `baseball_derive_fixtures`)
- Assert `results[0]["career_batting_average"]` numeric
- Assert `response.question` echoed
- Assert provenance `parameters.question` + `intent_slug`
- Cross-cache: pre-seed storage under slug; question deliver → no second codegen call

**`tests/test_baseball_intent_dedup.py`** — regression unchanged.

**`tests/test_baseball_question_hr_manifest.py`** (or single file) — HR question mocks intent → `career_hr`; manifest path; no derive mock invoked.

### 11 — Docs

- `docs/manual-checks/2026-06-19-baseball-specialist-hand-test.md` — M5 gate rows M5-1..M5-5
- `.env.example` — comment that question intent uses `MYCELIUM_INTENT_NORMALIZATION_MODEL`

---

## Verification

```bash
./bin/ci-local
./bin/smoke-baseball-e2e
uv run pytest tests/test_question_intent.py tests/test_entity_query_question.py tests/test_baseball_question_deliver.py tests/test_baseball_intent_dedup.py -q
```

---

## Operator (Paul) — after merge

```bash
MYCELIUM_INTENT_NORMALIZATION_MODEL=gpt-4o-mini
MYCELIUM_COMPUTATION_CODEGEN_MODEL=gpt-4o
rm -f ~/mycelium-networks/baseball/agents/batting/storage.json
rm -f ~/mycelium-networks/baseball/intent_map.json
./bin/refresh-example-network baseball --sync-only
```

Manual M5-1..M5-3 on live Aaron.

---

## For Grok + Paul (`output.md`)

- M5 pytest + smoke counts
- Manual gate checklist
- Suggested commit: `baseball: natural language question → intent slug deliver (M5)`