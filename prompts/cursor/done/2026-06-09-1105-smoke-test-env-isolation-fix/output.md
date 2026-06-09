# Output — Smoke test env isolation fix (`1105`)

## Summary

Fixed two smoke tests that failed when repo `.env` sets `MYCELIUM_NETWORK` or API keys. **Test isolation only** — no product behavior changes.

## Changes

| File | Fix |
|------|-----|
| `tests/test_admin_daemon.py` | `test_bootstrap_fails_when_unconfigured`: stub `load_dotenv` so `.env` cannot re-inject `MYCELIUM_NETWORK` after monkeypatch clears env |
| `tests/test_agent_factory.py` | `_setup_factory_env`: `delenv` for `OPENAI_API_KEY` and `TAVILY_API_KEY` so generated specialist research stays `pending` (not sync `na`) |

## Verification

```bash
uv run pytest tests/test_admin_daemon.py::test_bootstrap_fails_when_unconfigured \
  tests/test_agent_factory.py::test_create_specialist_writes_files_and_registers -m smoke -q
# 2 passed

uv run pytest -m smoke -q
# 174 passed, 20 deselected
```

## For Grok + Paul

- Mark **`1105`** done in `TODO.md` when reviewed.
- **No git commit** per fix-slice governance — Paul/Grok commit after review.
- Local `pytest -m smoke` is now trustworthy with `.env` present.
