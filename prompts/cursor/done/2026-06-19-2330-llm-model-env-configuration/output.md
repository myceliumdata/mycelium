# LLM model env configuration — output

## Done

- **`src/utils/llm_models.py`** — single `FALLBACK_MODEL`; `llm_model()` + five subsystem accessors (+ optional `agent_factory_refine_model()`).
- **Wired:** `derive_resolve.py`, `classification/engine.py`, `network/ontology.py`, `tools/research.py`, `bind_alias_expansion.py`, `agent_factory._refine_with_llm`.
- **Classification** — on-demand `classify()` now sets `model_used` when persisting (apply + unknown cache).
- **`.env.example`** — all five vars + derive high-end operator note; optional refine var.
- **`docs/architecture.md`** — one sentence + table row for `MYCELIUM_*_MODEL`.
- **`tests/test_llm_models.py`** — unset/empty/set env coverage.

## Env var table

| Env var | Subsystem | Default |
|---------|-----------|---------|
| `MYCELIUM_DERIVE_MODEL` | Baseball derive codegen + review | `gpt-4o-mini` |
| `MYCELIUM_CLASSIFICATION_MODEL` | Category tree classify / refresh | `gpt-4o-mini` |
| `MYCELIUM_ONTOLOGY_MODEL` | `network create` skeleton ontology | `gpt-4o-mini` |
| `MYCELIUM_RESEARCH_MODEL` | Specialist research runner | `gpt-4o-mini` |
| `MYCELIUM_ALIAS_EXPANSION_MODEL` | Lazy bind-field alias expansion | `gpt-4o-mini` |
| `MYCELIUM_AGENT_FACTORY_REFINE_MODEL` | Optional agent factory LLM polish | `gpt-4o-mini` |

## Verification

```text
uv run pytest tests/test_llm_models.py tests/test_network_ontology.py -q  # 16 passed
./bin/ci-local                    # 579 smoke passed
rg 'gpt-4o-mini' src/ examples/networks/baseball/specialists/  # llm_models.py only (+ comment in models.py)
```

## For Grok + Paul

- Mark **LLM model configuration — env-only** done in `TODO.md`.
- **Paul:** set `MYCELIUM_DERIVE_MODEL=gpt-4o` in `.env` for baseball derive production (ops, career_avg, etc.).

## Suggested commit message

```
config: env-only LLM model selection for all subsystems
```
