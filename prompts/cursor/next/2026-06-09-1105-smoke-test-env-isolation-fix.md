# Task: Smoke test env isolation — review hygiene

> **READY** — Non-protocol fix. Run before or alongside Slice 3; does not block `1200` but makes local `pytest -m smoke` trustworthy when `.env` is present.

**Read these first (mandatory):**
- `prompts/cursor/WORKFLOW.md`
- [`prompts/cursor/done/2026-06-09-1100-entity-outcome-infrastructure-phase2/review.md`](../done/2026-06-09-1100-entity-outcome-infrastructure-phase2/review.md)

---

## Objective

Fix two smoke tests that fail when repo `.env` sets `MYCELIUM_NETWORK` or API keys. **Test isolation only** — no product behavior changes.

### 1. `test_bootstrap_fails_when_unconfigured`

`bootstrap_admin()` calls `load_dotenv()` which re-injects `MYCELIUM_NETWORK=crm` after monkeypatch clears it.

**Fix:** `monkeypatch.setattr("mycelium_admin.server.load_dotenv", lambda *a, **k: None)` (or equivalent) so test controls env. Assert `NO_NETWORK_CONFIGURED_MSG` still raised.

### 2. `test_create_specialist_writes_files_and_registers`

Assumes research unavailable (`pending`) but `.env` keys trigger sync research → `na`.

**Fix:** In test (or `_setup_factory_env`), `monkeypatch.delenv("OPENAI_API_KEY", raising=False)` and `monkeypatch.delenv("TAVILY_API_KEY", raising=False)` — match pattern in `test_entity_key_suggestions.py`.

---

## Verification

```bash
# With .env present (Paul's machine)
uv run pytest tests/test_admin_daemon.py::test_bootstrap_fails_when_unconfigured tests/test_agent_factory.py::test_create_specialist_writes_files_and_registers -m smoke -q
uv run pytest -m smoke -q
```

---

## Governance

- **Do not edit `TODO.md`.**
- **Do not git commit** until Grok + Paul review.

---

## Deliverables

`prompts/cursor/done/2026-06-09-1105-smoke-test-env-isolation-fix/` with `prompt.md`, `output.md`.