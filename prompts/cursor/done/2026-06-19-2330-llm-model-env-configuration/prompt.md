# LLM model configuration — env-only

> **READY** — Claim per `prompts/cursor/WORKFLOW.md`.

**Objective:** Unify LLM model selection across framework subsystems. Every production LLM call reads its model from a documented `MYCELIUM_*_MODEL` env var. **No** scattered `gpt-4o-mini` literals; **no** `model=` parameters on public/hot-path APIs. Document all five vars in `.env.example` with operator guidance (derive needs a high-end model).

**Origin:** `TODO.md` — *LLM model configuration — env-only*; live derive-on-miss (`ops`) passed on `gpt-4o` but failed on `gpt-4o-mini`.

**Principles:**

- One module owns resolution and the single fallback constant.
- Tests inject `llm=` mocks where they already do; otherwise `monkeypatch.setenv` on the relevant `MYCELIUM_*_MODEL`.
- **Do not edit `TODO.md`.**
- Keep scope tight — no new features, no provider abstraction beyond existing `ChatOpenAI` usage.

---

## The five env vars

| Env var | Subsystem | Default when unset |
|---------|-----------|-------------------|
| `MYCELIUM_DERIVE_MODEL` | Specialist derive-on-miss: LLM codegen + semantic review before caching computed fields (today: pack `derive_resolve.py`) | `gpt-4o-mini` |
| `MYCELIUM_CLASSIFICATION_MODEL` | Category tree `classify()` + `refresh_from_llm()` | `gpt-4o-mini` |
| `MYCELIUM_ONTOLOGY_MODEL` | `network create` skeleton ontology generation | `gpt-4o-mini` |
| `MYCELIUM_RESEARCH_MODEL` | Specialist research runner (`src/tools/research.py`) | `gpt-4o-mini` |
| `MYCELIUM_ALIAS_EXPANSION_MODEL` | Lazy bind-field alias expansion | `gpt-4o-mini` |

All five must be documented in `.env.example` (commented examples). **Operator note (required in `.env.example`):** derive codegen + review is code production — `gpt-4o-mini` is insufficient for composite warehouse stats; recommend **`gpt-4o`** or stronger for `MYCELIUM_DERIVE_MODEL` when using derive-on-miss. Classification, ontology, research, and alias expansion are fine on mini for cost. Baseball `ops` may appear only as an example in comments, not in var names or subsystem titles.

---

## Implement

### 1 — Central resolver (`src/utils/llm_models.py`)

Add a small module:

```python
def llm_model(env_key: str) -> str:
    """Read model from env_key; empty/unset → FALLBACK_MODEL."""

def derive_model() -> str: ...
def classification_model() -> str: ...
def ontology_model() -> str: ...
def research_model() -> str: ...
def alias_expansion_model() -> str: ...
```

- Single module-level `FALLBACK_MODEL = "gpt-4o-mini"` (only place the default string lives).
- Each accessor calls `llm_model("MYCELIUM_*_MODEL")`.
- Export names above; no other public API required.

### 2 — Wire subsystems (remove hardcoding + `model=` params)

| File | Change |
|------|--------|
| `examples/networks/baseball/specialists/derive_resolve.py` | Delete local `derive_model()`; `from utils.llm_models import derive_model` |
| `src/agents/classification/engine.py` | Remove `model: str = "gpt-4o-mini"` from `_llm_propose_for_attributes` and `refresh_from_llm`; use `classification_model()` when constructing `ChatOpenAI`; persist `classification_model()` into `CategoryTreeData.model_used` on LLM refresh paths |
| `src/network/ontology.py` | Remove `model` param from `generate_skeleton_ontology`, `_invoke_llm`, `_convert_proposed` call chain; use `ontology_model()` |
| `src/network/create.py` | Remove `_DEFAULT_ONTOLOGY_MODEL`; `ontology.model_used` already comes from generator |
| `src/tools/research.py` | Replace inline `os.getenv` with `research_model()` from central module |
| `src/agents/bind_alias_expansion.py` | Replace module-level `_ALIAS_EXPANSION_MODEL` with lazy `alias_expansion_model()` call at invoke time (or import accessor; avoid stale import-time env) |

**`classify()` on-demand path:** ensure first-time unknown classification also sets `model_used` when it persists (today only `refresh_from_llm` sets it — fix if missing).

### 3 — Agent factory refine (minimal)

`src/agents/factory/agent_factory.py` `_refine_with_llm`: use `llm_model("MYCELIUM_AGENT_FACTORY_REFINE_MODEL")` from the same module (sixth var, **optional** — document in `.env.example` as commented optional; not one of the five). Keeps TODO’s “agent factory refine” item satisfied without expanding the five-var table.

**Non-goal:** `examples/networks/baseball/bootstrap_experiment.py` (`MYCELIUM_BOOTSTRAP_MODEL`) — dev script; leave as-is or add one-line comment pointing to central module pattern.

### 4 — `.env.example`

Under the existing model providers section, add a block **LLM models (per subsystem)** listing all five vars with commented defaults and the derive high-end note (see table above). Include optional `MYCELIUM_AGENT_FACTORY_REFINE_MODEL` comment.

### 5 — `docs/architecture.md` (minimal)

In **Framework credentials vs network data**, add one sentence: LLM model selection is env-only via `MYCELIUM_*_MODEL` vars (see `.env.example`); derive recommends `gpt-4o+`.

### 6 — Tests

- **`tests/test_llm_models.py`** (new): unset env → fallback; set each `MYCELIUM_*_MODEL` → returned; empty string → fallback.
- **`tests/test_network_ontology.py`**: remove `model=` args if any; `model_used` assertion uses fallback or monkeypatched `MYCELIUM_ONTOLOGY_MODEL`.
- **Classification tests** (if any assert model): monkeypatch `MYCELIUM_CLASSIFICATION_MODEL`.
- Existing derive/research/alias tests must stay green (mocked LLM paths unchanged).

---

## Non-goals

- `MYCELIUM_DEFAULT_MODEL` shared override chain (five explicit vars only in v1).
- Separate review vs codegen model env vars for derive.
- Provider switching (Anthropic/Grok) — OpenAI paths only, same as today.
- Changing baseball provenance `computation.model` stamping logic (already correct).

---

## Verification

```bash
uv run pytest tests/test_llm_models.py tests/test_network_ontology.py -q
./bin/ci-local
```

Spot-check: `rg 'gpt-4o-mini' src/ examples/networks/baseball/specialists/` → only `src/utils/llm_models.py` (and test fixtures if needed).

---

## For Grok + Paul (`output.md`)

- List files touched and env var table.
- Note: Paul should set `MYCELIUM_DERIVE_MODEL=gpt-4o` in `.env` for derive-on-miss production use.
- Ask Grok to mark **LLM model configuration — env-only** done in `TODO.md`.
- Suggested commit message: `config: env-only LLM model selection for all subsystems`