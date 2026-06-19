# Baseball derive codegen sandbox (M3)

> **READY** — Claim per `prompts/cursor/WORKFLOW.md`. **After M2 polish** (`2026-06-19-1700`) on `main`.

**Priority:** Layer 3 phase 3 — on manifest **cache miss** (no alias / convention), LLM generates a sandboxed Python compute for one guinea-pig attr; provenance records real code + full `parameters`.

**Parent:** [`docs/plans/conversations/2026-06-19-warehouse-factory-layer3-specialist-emergence.md`](../../docs/plans/conversations/2026-06-19-warehouse-factory-layer3-specialist-emergence.md)

**Principles:**

- **M2 path unchanged** — aliased attrs (`career_hr`, `birth_date`, …) still use committed `warehouse_resolve.py`; no LLM on cache hit.
- **Computation-centric provenance** — `sources[]` (dataset pin) + `computation.inline` (generated code that ran) + `parameters` (all values: `lahman.playerID`, `warehouse`, `attribute`, …).
- **Pack Lahman logic** stays pack-only; framework provides **sandbox runner** + optional **derive orchestration** hook specialists call.
- **No web research** for warehouse batting/bio paths.
- **Do not edit `TODO.md`.**

---

## Objective

When `batting_specialist` cannot resolve an owned field via manifest aliases (today: `career_avg` → `N/A`), invoke a **derive pipeline**:

1. Build context from live `warehouse_manifest.json` (domain tables, columns, conventions).
2. LLM emits a **single Python function** `compute(player_id: str, warehouse: Path) -> str` using only allowed APIs.
3. Run in **sandbox**; on success `write_computed_field` + cache; on failure `write_na_field`.
4. Second deliver serves from cache (no LLM).

**Guinea pig:** `career_avg` on baseball — `SUM(H) / SUM(AB)` on `Batting` for full Lahman Aaron ≈ **0.305** (fixture: compute from minimal `Batting.csv`).

---

## Locked behavior

| Case | Behavior |
|------|----------|
| Alias hit (`career_hr`) | Existing M2b path — **no LLM** |
| Alias miss (`career_avg`) | Derive codegen once per entity+attr (cache miss) |
| LLM / sandbox failure | `N/A`; no partial value |
| Provenance | `computation.inline` = generated source; include `parameters.warehouse`, `parameters.attribute`, model id in `computation` metadata if useful |

**Sandbox allowlist (v1):**

- `pathlib.Path`, `sqlite3` via existing `query_warehouse` only
- No `import os`, `subprocess`, `open` outside warehouse path, no network

Validate with AST or restricted exec namespace before run.

---

## Implement

### 1 — Framework sandbox

**File:** `src/network/derive_sandbox.py` (or `src/agents/derive_sandbox.py` if closer to specialists)

- `validate_derive_source(source: str) -> None` — raise on forbidden constructs
- `run_derive_function(source: str, *, player_id: str, warehouse: Path) -> str` — exec function, return string value
- Unit tests: reject `import os`; accept minimal `query_warehouse` sum example

### 2 — Derive orchestration (framework or pack helper)

**File:** `examples/networks/baseball/specialists/derive_resolve.py` (pack) calling framework sandbox

- `build_derive_prompt(attr, manifest, domain) -> str` — tables, columns, grain, conventions, attr name
- `generate_and_run_derive(attr, player_id, warehouse, paths, *, manifest) -> ResolvedField | None`
- Use env `OPENAI_API_KEY`; model from `MYCELIUM_DERIVE_MODEL` default `gpt-4o-mini`; temperature 0
- **Tests:** mock LLM to return fixed `career_avg` function; fixture Aaron delivers non-`N/A` value

### 3 — Wire `batting_specialist`

After `resolve_domain_attribute` returns `None`, call derive for owned batting attrs **only when** manifest domain exists and warehouse present. Do not derive for unknown categories.

Cache semantics: successful derive → normal `write_computed_field`; failures → `write_na_field` (sticky na per M2 — acceptable for M3).

### 4 — Manifest hint (optional v1)

In `warehouse_domains.json` batting domain, optional:

```json
"derive_candidates": ["career_avg"]
```

Or document in manifest that unaliased attrs in `categories.json` batting examples may derive — pick one approach in `output.md`.

### 5 — Tests + smoke

- `tests/test_derive_sandbox.py` — framework unit tests
- `tests/test_baseball_career_avg_derive.py` — mocked LLM end-to-end on minimal fixture
- Extend `bin/smoke-baseball-e2e` optional row OR pytest-only if LLM key absent in CI (mock required for CI green)

**Regression:** all M2 tests + `test_baseball_batting_specialist.py` career_hr paths unchanged.

---

## Non-goals (M4+)

- Free-form `derive` label / intent hash (M4)
- Natural language `question` (M5)
- OPS, WAR, cross-table franchise
- Auto-promote derive → committed alias without human slice
- `TODO.md` edits

---

## Verification

```bash
./bin/ci-local
uv run pytest tests/test_derive_sandbox.py tests/test_baseball_career_avg_derive.py tests/test_baseball_batting_specialist.py -q
./bin/smoke-baseball-e2e
```

Manual (Paul, live Lahman): `career_avg` on Hank Aaron after clearing batting storage if stale `N/A`; `provenance: true` shows generated inline + warehouse parameters.

---

## For Grok + Paul (output.md)

- M3 done; note fixture expected `career_avg` decimal format (e.g. `.305` vs `0.305` — lock one).
- Queue M3b or M4 only if scope split needed.

**Suggested commit message:**

```
baseball: LLM derive sandbox for career_avg (M3)
```