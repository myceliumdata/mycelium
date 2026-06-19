# LLM computation codegen model — remediation output

## Done

- **Renamed** `MYCELIUM_DERIVE_MODEL` → `MYCELIUM_COMPUTATION_CODEGEN_MODEL` (no backward compat).
- **Renamed** `derive_model()` → `computation_codegen_model()` in `src/utils/llm_models.py`.
- **Wired** `derive_resolve.py` to new accessor.
- **Docs:** `.env.example` (framework-generic computation codegen block), `docs/architecture.md`, hand-test doc.
- **Tests:** `test_llm_models.py` updated for new env key.

## Env var (replaces derive)

| Env var | Purpose | Default |
|---------|---------|---------|
| `MYCELIUM_COMPUTATION_CODEGEN_MODEL` | LLM codegen + semantic review for computation-on-miss | `gpt-4o-mini` |

Unchanged: `MYCELIUM_DERIVE_MAX_ATTEMPTS` (retry budget only).

## Verification

```text
uv run pytest tests/test_llm_models.py tests/test_baseball_career_avg_derive.py tests/test_baseball_ops_derive.py -q  # 15 passed
./bin/ci-local                    # 579 smoke passed
rg 'MYCELIUM_DERIVE_MODEL|derive_model\(' src/ tests/ examples/ .env.example docs/architecture.md docs/manual-checks/  # empty
```

## For Grok + Paul

- Remediation complete; mark **LLM model configuration — env-only** done in `TODO.md` using `MYCELIUM_COMPUTATION_CODEGEN_MODEL` (not old derive name).
- **Paul:** rename `.env` key — `MYCELIUM_DERIVE_MODEL=gpt-4o` → `MYCELIUM_COMPUTATION_CODEGEN_MODEL=gpt-4o`. Old key is **not read**.

## Suggested commit message

```
config: rename MYCELIUM_COMPUTATION_CODEGEN_MODEL; fix model env docs
```
