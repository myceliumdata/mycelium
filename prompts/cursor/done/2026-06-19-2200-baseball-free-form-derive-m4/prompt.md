# Baseball free-form derive (M4)

> **READY** — Claim per `prompts/cursor/WORKFLOW.md`. **After** tag `first_llm_computed_result` / M3c on `main`.

**Design:** [`docs/plans/conversations/2026-06-19-baseball-m4-free-form-derive.md`](../../docs/plans/conversations/2026-06-19-baseball-m4-free-form-derive.md)

**Objective:** Remove M3 `derive_candidates` whitelist. On batting domain **manifest miss**, run the existing M3c derive pipeline for **any** owned attribute label the client requests (guinea pig: **`ops`**).

**Principles:**

- Reuse `derive_resolve.generate_and_run_derive()` — context, semantic review, retry — no fork.
- **No** new `EntityQuery` fields (M5 owns NL `question`).
- **No** intent-hash synonym cache in v1 — storage field key = normalized requested label.
- End user: value or `N/A`; operator `operator_audit` unchanged.
- **Do not edit `TODO.md`.**

---

## Implement

### 1 — Manifest (`warehouse_domains.json`)

Batting domain:

```json
"derive_on_miss": true
```

Remove `derive_candidates` array (or document ignored when `derive_on_miss` is true — pick one clean approach).

### 2 — `derive_resolve.py`

- Replace `is_derive_candidate()` with `derive_on_miss_enabled(manifest, domain) -> bool` reading domain flag.
- `generate_and_run_derive(attr, ...)` unchanged except gate check.

### 3 — `batting_specialist.py`

When `resolve_domain_attribute` returns `None`:

```python
if dr.derive_on_miss_enabled(manifest, "batting"):
    derive_result = dr.generate_and_run_derive(...)
```

Remove `is_derive_candidate` branch.

### 4 — Ontology routing

Ensure guinea pig routes to batting:

- Add `"ops": "batting"` to `examples/networks/baseball/categories.json` `attribute_map` if missing.

### 5 — Tests

**Fixtures** (`tests/baseball_derive_fixtures.py`):

- `OPS_DERIVE_SOURCE` — minimal mocked compute returning a fixed OPS string on fixture (e.g. `"0.900"` from stub rows).

**E2E** (`tests/test_baseball_ops_derive.py` or extend career_avg file):

- Mock codegen + review; deliver `ops` on minimal Aaron fixture → non-`N/A`.
- Assert `career_avg` tests still pass (whitelist removed).

**Unit:** `derive_on_miss_enabled` true/false from manifest dict.

### 6 — Smoke

- Optional `ops_derive_mocked` scenario in `bin/smoke-baseball-e2e` OR pytest-only with mock (match M3 pattern).

### 7 — Docs (minimal)

- Hand-test doc: one row for M4 `ops` (mocked CI; live optional).
- `examples/networks/baseball/README.md`: one line on `derive_on_miss` if README mentions derive.

---

## Non-goals

- Pitching/bio `derive_on_miss`
- NL question / M5
- Intent hash cache
- Deep provenance

---

## Verification

```bash
uv run pytest tests/test_baseball_career_avg_derive.py tests/test_baseball_ops_derive.py tests/test_derive_review.py -q
./bin/ci-local
./bin/smoke-baseball-e2e
```

---

## For Grok + Paul (`output.md`)

- M4 v1 done; note live `ops` sanity if Paul runs it.
- Recommend M4b: intent-hash / label normalization if needed.

**Suggested commit message:**

```
baseball: free-form derive on manifest miss (M4)
```