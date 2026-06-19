# LLM model env — remediation (naming + doc fixes)

> **READY** — Claim per `prompts/cursor/WORKFLOW.md`. **Remedial** follow-up to `2026-06-19-2330-llm-model-env-configuration` (not yet reviewed/committed).

**Objective:** Fix documentation and naming gaps from the env-only model slice; rename the opaque derive env var to operator-clear **`MYCELIUM_COMPUTATION_CODEGEN_MODEL`**; rename the matching Python accessor. This is framework-wide capability (LLM writes `computation` provenance code), not baseball-specific.

**Principles:**

- Operator-facing names match provenance vocabulary (`computation`) and behavior (`codegen`).
- **Do not edit `TODO.md`.**
- Do not rename internal pack modules (`derive_resolve.py`, `derive_sandbox.py`, `DeriveRunResult`, …) — M5 will lift orchestration; this slice is env/API clarity only.
- Do not edit historical files under `prompts/cursor/done/` except this slice’s own `output.md`.

---

## 1 — Rename env var + accessor

| Old | New |
|-----|-----|
| `MYCELIUM_DERIVE_MODEL` | `MYCELIUM_COMPUTATION_CODEGEN_MODEL` |
| `derive_model()` in `src/utils/llm_models.py` | `computation_codegen_model()` |

**No backward compatibility.** Read only `MYCELIUM_COMPUTATION_CODEGEN_MODEL`; unset/empty → `FALLBACK_MODEL`. Remove `derive_model()` entirely (no alias — callers import `computation_codegen_model` only). Remove all `MYCELIUM_DERIVE_MODEL` references from source, tests, and docs.

### Wire callers

| File | Change |
|------|--------|
| `src/utils/llm_models.py` | Implement rename (new env key only) |
| `examples/networks/baseball/specialists/derive_resolve.py` | `from utils.llm_models import computation_codegen_model`; replace all `derive_model()` calls |
| `tests/test_llm_models.py` | Test new env key + empty → fallback; remove `derive_model` / `MYCELIUM_DERIVE_MODEL` |

**Do not change** `MYCELIUM_DERIVE_MAX_ATTEMPTS` (retry budget — separate concern).

---

## 2 — Documentation fixes (missed from 2330 + nits)

These shipped wrong or baseball-specific in the prior slice. Fix to **framework-generic** wording.

### `.env.example`

Replace the derive block with:

```bash
# LLM models (per subsystem) — unset defaults to gpt-4o-mini (src/utils/llm_models.py)
#
# Computation codegen: when no recipe exists for a requested attribute, the framework
# LLM-writes Python to compute the value from warehouse/sources, reviews it, then caches.
# Used for both codegen and semantic review. Prefer gpt-4o or stronger — gpt-4o-mini
# often fails on composite stats (e.g. OPS from batting totals).
# MYCELIUM_COMPUTATION_CODEGEN_MODEL=gpt-4o
# MYCELIUM_CLASSIFICATION_MODEL=gpt-4o-mini
# MYCELIUM_ONTOLOGY_MODEL=gpt-4o-mini
# MYCELIUM_RESEARCH_MODEL=gpt-4o-mini
# MYCELIUM_ALIAS_EXPANSION_MODEL=gpt-4o-mini
# Optional: agent factory LLM polish (off by default in normal render path)
# MYCELIUM_AGENT_FACTORY_REFINE_MODEL=gpt-4o-mini
```

- Subsystem titles must **not** say "Baseball" or "derive".
- OPS may appear only as a parenthetical example.

### `docs/architecture.md`

In **Framework credentials vs network data**:

- Table row: change `derive recommends gpt-4o+` → `computation codegen recommends gpt-4o+`.
- Prose sentence: replace `baseball derive production use recommends MYCELIUM_DERIVE_MODEL=gpt-4o` with generic: computation codegen production use recommends `MYCELIUM_COMPUTATION_CODEGEN_MODEL=gpt-4o` or stronger.

### `docs/manual-checks/2026-06-19-baseball-specialist-hand-test.md`

- Line referencing `MYCELIUM_DERIVE_MODEL` → `MYCELIUM_COMPUTATION_CODEGEN_MODEL` with same meaning (framework env, not baseball-only).

### `src/utils/llm_models.py` module docstring

One line: central env-only model selection; `computation_codegen_model` = LLM that writes provenance `computation` code on attribute miss.

---

## 3 — Verification nits (confirm 2330 deliverables)

Quick audit — fix if still broken:

| Check | Expected |
|-------|----------|
| `rg 'gpt-4o-mini' src/ examples/networks/baseball/specialists/` | Only `src/utils/llm_models.py` (+ innocuous comments if any) |
| `rg 'model: str.*gpt-4o-mini' src/` | Empty (no `model=` params on hot-path APIs) |
| `rg 'MYCELIUM_DERIVE_MODEL' src/ tests/ .env.example docs/` | Empty |
| `rg 'derive_model' src/ tests/ examples/` | Empty |
| Classification `classify()` persists `model_used` on apply + unknown cache | Already shipped — leave unless regressed |

---

## Non-goals

- Rename `derive_resolve.py`, `derive_sandbox`, pack loader names, or audit log prefix `derive ops`.
- Split codegen vs review into two env vars.
- Update Paul's live `.env` on disk (Paul must rename `MYCELIUM_DERIVE_MODEL` → `MYCELIUM_COMPUTATION_CODEGEN_MODEL` before/after deploy).

---

## Verification

```bash
uv run pytest tests/test_llm_models.py tests/test_baseball_career_avg_derive.py tests/test_baseball_ops_derive.py -q
./bin/ci-local
rg 'MYCELIUM_DERIVE_MODEL|derive_model\(' src/ tests/ examples/ .env.example docs/architecture.md docs/manual-checks/
```

---

## For Grok + Paul (`output.md`)

- Summarize rename + doc fixes.
- Note: Paul must rename `.env` key to `MYCELIUM_COMPUTATION_CODEGEN_MODEL=gpt-4o` (old key is not read).
- Ask Grok to update `TODO.md` env-only item to reference `MYCELIUM_COMPUTATION_CODEGEN_MODEL` when marking done.
- Suggested commit message: `config: rename MYCELIUM_COMPUTATION_CODEGEN_MODEL; fix model env docs`