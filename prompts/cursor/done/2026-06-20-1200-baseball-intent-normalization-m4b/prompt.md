# Baseball intent normalization (M4b)

> **READY** — Claim per `prompts/cursor/WORKFLOW.md`.

**Design:** [`docs/plans/conversations/2026-06-20-baseball-m4b-intent-normalization.md`](../../docs/plans/conversations/2026-06-20-baseball-m4b-intent-normalization.md)

**Objective:** Before computation-on-miss derive, resolve a canonical **intent slug** per requested label. Synonym labels (`career_avg`, `batting_average`) share one specialist storage key and one derive. **`results[]` always uses the requested label**; provenance records both requested label and `intent_slug`.

**Principles:**

- Framework-owned `intent_map.json` + intent normalization (not baseball-only long-term); v1 wire through batting `derive_on_miss` path only.
- **`MYCELIUM_INTENT_NORMALIZATION_MODEL`** (cheap, e.g. mini) — new sixth accessor in `llm_models.py`; separate from **`MYCELIUM_COMPUTATION_CODEGEN_MODEL`** (codegen + review unchanged).
- Slug validation: non-empty `[a-z0-9_]+`, max 64 — same as attribute normalization; reject/retry on bad slug.
- **Do not edit `TODO.md`.**
- No M5 `question` field; no static stat glossary.

---

## Paul locks (must implement)

| Lock | Requirement |
|------|-------------|
| Map file | `{network_root}/intent_map.json` — label → intent slug, per network |
| Storage key | Computed derive cache under **intent slug** only |
| Deliver | `values[requested_label]` in specialist output — never rename key to slug |
| Provenance | `parameters.attribute` = requested label; add `parameters.intent_slug` |
| Models | Intent LLM uses `intent_normalization_model()`; derive uses `computation_codegen_model()` |

---

## Implement

### 1 — `src/utils/llm_models.py`

Add:

```python
def intent_normalization_model() -> str:
    return llm_model("MYCELIUM_INTENT_NORMALIZATION_MODEL")
```

### 2 — Framework intent map (`src/network/intent_map.py`)

- Path: `NetworkPaths.root / "intent_map.json"`
- JSON shape (versioned):

```json
{
  "version": "1.0",
  "mappings": {
    "career_avg": "career_batting_average",
    "batting_average": "career_batting_average"
  }
}
```

- `load_intent_map(paths) -> dict[str, str]` (normalized keys)
- `save_intent_mapping(paths, label: str, intent_slug: str) -> None` (atomic write, merge)
- `lookup_intent_slug(label: str, mappings: dict[str, str]) -> str | None`

### 3 — Framework intent normalization (`src/network/intent_normalization.py`)

- `INTENT_SLUG_RE = re.compile(r"^[a-z0-9_]{1,64}$")`
- Pydantic `IntentProposal`: `intent_slug: str`, `confidence: float`
- `validate_intent_slug(slug: str) -> bool`
- `resolve_intent_slug(label, *, domain: str, manifest: dict, paths: NetworkPaths, intent_map: dict[str, str], llm_invoke: Callable | None = None) -> str`
  - Normalize label (`strip().lower()`)
  - If label in `intent_map` → return mapped slug (validate)
  - Else LLM structured call with warehouse context (reuse `format_warehouse_context` from pack via import from `derive_resolve` **or** duplicate minimal context builder in framework — prefer **thin framework prompt** that accepts domain + manifest snippet; avoid circular imports: extract shared `format_warehouse_context` to `src/network/warehouse_context.py` if needed, or pass preformatted context string from batting specialist)
  - Persist label → slug to `intent_map.json` on successful LLM resolution
  - Confidence threshold: **0.7** (match classification); below threshold → fall back to **label as its own slug** (no cross-label dedup for that request)
  - Invalid slug from LLM → one retry with fix hint; still invalid → fall back to label as slug
  - Injectable `llm_invoke` for tests (no API key)

**Prompt intent:** Given requested attribute label and warehouse domain context, emit canonical snake_case slug for “what stat/computation does this label mean?” — not category routing.

### 4 — `batting_specialist.py` (derive-on-miss path only)

Refactor `_evaluate_batting_fields` derive branch:

**Unchanged:** M2 `resolve_domain_attribute` hits still use `key` (requested label) for storage lookup/write.

**Derive-on-miss path** (when `resolved is None` and `derive_on_miss_enabled`):

1. `requested_key = key`
2. `intent_slug = resolve_intent_slug(...)` (framework)
3. **Cache check:** `record.get(intent_slug)` for `field_has_value` / `field_is_na` **before** derive
   - On hit: `values[requested_key] = ...` (display from intent_slug entry); do not write duplicate row under requested_key
4. **Derive:** `generate_and_run_derive(requested_key, ...)` — prompts still use human label
5. **Write:** `write_computed_field(entity_id, intent_slug, ...)` — storage key = slug
6. **Provenance:** `parameters` includes `attribute=requested_key`, `intent_slug=intent_slug`
7. **Return:** `values[requested_key] = written`

**Legacy read (one release):** If `intent_slug` cache miss but `record.get(requested_key)` has computed value (pre-M4b storage), use it without re-derive; do **not** copy to slug in v1 (hand-test clears cache).

Audit: optional `batting_specialist: intent {requested_key} -> {intent_slug}` line in derive audit when slug ≠ requested_key.

### 5 — `derive_resolve.py`

- Extend `provenance_parameters(..., attribute: str, intent_slug: str | None = None)` — add `intent_slug` when set
- No change to codegen/review model selection

### 6 — `.env.example`

Document sixth var (commented):

```bash
# MYCELIUM_INTENT_NORMALIZATION_MODEL=gpt-4o-mini
```

Note: cheap model for label→intent slug; separate from computation codegen (`gpt-4o` recommended).

### 7 — Tests

**`tests/test_intent_map.py`** — load/save/lookup round-trip.

**`tests/test_intent_normalization.py`** — slug validation; mock LLM returns slug; map hit skips LLM; low confidence falls back to label.

**`tests/test_baseball_intent_dedup.py`** (e2e, mocked):

- Fixture network + minimal Lahman (reuse baseball derive fixtures)
- Mock **intent** LLM: `career_avg` → `career_batting_average`, `batting_average` → `career_batting_average`
- Mock **codegen + review** LLM: return fixed derive source (reuse career_avg fixture pattern)
- Step A: deliver `career_avg` → value found, storage under `career_batting_average` (or chosen slug), `intent_map.json` updated
- Step B: deliver `batting_average` → **same value**, assert codegen mock call count did **not** increase on step B
- Assert `results` keys are `career_avg` / `batting_average` respectively
- Assert provenance `parameters.intent_slug` present; `parameters.attribute` matches requested label

**Update `tests/test_llm_models.py`** — cover `intent_normalization_model` accessor.

### 8 — Docs (minimal)

- `docs/manual-checks/2026-06-19-baseball-specialist-hand-test.md` — M4b gate row: Aaron `career_avg` then `batting_average`, clear batting cache first; expect no second codegen
- Conversation doc already exists — no edit required unless behavior differs

### 9 — Smoke (optional)

Add `intent_dedup_mocked` scenario to `bin/smoke-baseball-e2e` if pattern fits; pytest-only acceptable.

---

## Non-goals

- Pitching/bio `derive_on_miss` intent (batting only v1)
- Migrating old storage keys to slug automatically
- M5 NL `question`
- Strict env hard-fail (separate TODO)
- `describe_network` surfacing `intent_map.json` (defer)

---

## Verification

```bash
uv run pytest tests/test_intent_map.py tests/test_intent_normalization.py tests/test_baseball_intent_dedup.py tests/test_llm_models.py -q
uv run pytest tests/test_baseball_career_avg_derive.py tests/test_baseball_ops_derive.py -q
./bin/ci-local
./bin/smoke-baseball-e2e
```

```bash
rg 'MYCELIUM_DERIVE_MODEL|derive_model\(' src/ tests/ examples/
```

---

## For Grok + Paul (`output.md`)

- Summarize intent map + dedup behavior
- Note Paul must set `MYCELIUM_INTENT_NORMALIZATION_MODEL` in `.env` (and rename computation codegen var if not done)
- M4b manual gate: clear batting storage; `career_avg` then `batting_average`
- Suggested commit message: `baseball: intent normalization for derive cache dedup (M4b)`