# Brave search — direct API (drop `langchain-community`)

> **READY** — Claim per `prompts/cursor/WORKFLOW.md`. **Do not edit `TODO.md`.**

## Context (Paul + Grok, 2026-06-21)

Slice `2500` added `SEARCH_PROVIDER=brave` via `langchain_community.tools.BraveSearch`. Paul validated live gates with Brave:

- **CRM** — all scenarios pass (`meter-02-deliver` triggers research)
- **Baseball** — all scenarios pass (bio_research phase)

Pytest emits a **DeprecationWarning** on Brave path:

```
src/tools/web_search.py:270: DeprecationWarning: `langchain-community` is being sunset...
    from langchain_community.tools import BraveSearch
```

[`langchain-community` was archived 2026-05-22](https://github.com/langchain-ai/langchain-community/issues/674). There is no standalone `langchain-brave` package (unlike `langchain-tavily` / `langchain-exa`). **`langchain-community` is only imported for Brave** in this repo.

**Objective:** Replace the Brave LangChain wrapper with a thin direct HTTP client to Brave Web Search API; remove `langchain-community` from dependencies. **No behavior change** for operators — same env vars, same normalized `SearchHit` output, same research tool contract.

**Live gate: N/A** — internal provider implementation swap; catalogs and scenario counts unchanged. Paul already confirmed Brave gates pass; preserve that behavior.

---

## Design lock

| Topic | Lock |
|-------|------|
| Env | `BRAVE_SEARCH_API_KEY` unchanged |
| Endpoint | `GET https://api.search.brave.com/res/v1/web/search` |
| Auth header | `X-Subscription-Token: <api_key>` |
| Query params | `q` (required), `count` (1–20, use `max_results` from caller) |
| Response mapping | `web.results[]` → `{title, url, description}` (Brave native field names) |
| Normalizer | Extend `_normalize_brave_hits` to accept native API JSON (`{"web": {"results": [...]}}`) **and** keep backward-compat for legacy list / JSON-string shapes (langchain wrapper format used in existing unit tests) |
| HTTP client | **stdlib `urllib.request`** — no new dependency (`httpx` / `requests` not in project today) |
| Errors | HTTP 4xx/5xx and Brave `{"error": ...}` payloads → `WebSearchProviderError` (match Exa/Tavily loud-fail pattern in `_validate_provider_raw`) |
| Dependencies | Remove `langchain-community` from `pyproject.toml`; run `uv lock` / `uv sync` |
| Tavily / Exa | **Do not change** — still use `langchain-tavily` and `langchain-exa` |

### `_search_brave` sketch

```python
def _search_brave(query: str, *, max_results: int) -> dict[str, Any]:
    # urllib GET with q, count=min(max_results, 20)
    # parse JSON; return full body or {"web": {"results": [...]}}
```

`_run_provider_search` → `_normalize_hits` path stays the same.

---

## Files to modify

| File | Action |
|------|--------|
| `src/tools/web_search.py` | Replace `_search_brave`; extend `_normalize_brave_hits`; optional small `_brave_api_request` helper |
| `pyproject.toml` | Remove `langchain-community>=0.4.2` |
| `uv.lock` | Regenerate via `uv sync` |
| `tests/test_web_search.py` | Add native API shape normalizer test; add `_search_brave` HTTP mock test (patch urllib or helper); confirm **no** `DeprecationWarning` when importing/running Brave path |
| `README.md` | One-line note if it still implies Brave uses langchain-community (only if needed) |

**Do not modify:** `tests/live/*`, gate catalogs, `research.py` tool aliases, `.env.example` key names.

---

## Tests (required)

| # | Test | Notes |
|---|------|-------|
| 1 | `test_normalize_brave_native_api_response` | Full Brave JSON with `web.results` using `url` + `description` |
| 2 | `test_search_brave_http_mocked` | Patch HTTP helper; assert query params and header; no live API |
| 3 | Existing brave tests | `test_normalize_hits_from_brave_*`, `test_web_search_brave_backend_mocked` still pass |
| 4 | No deprecation warning | `pytest.warns(None)` or filter — importing `tools.web_search` and calling brave path must not emit `langchain-community` sunset warning |
| 5 | `test_web_search_provider_error_on_brave_http_failure` | 401/429 or error JSON → `WebSearchProviderError` |

Run `./bin/ci-local` green before claiming done.

---

## Verification (Cursor `output.md`)

Document:

- `rg langchain_community` → **zero** matches in `src/` and `pyproject.toml`
- Smoke test count from `./bin/ci-local`
- Deprecation warning eliminated on Brave import path
- **For Grok + Paul:** note Paul validated Brave live gates (CRM + baseball); optional re-run `./bin/gate-live crm-metering --phase metering` with `SEARCH_PROVIDER=brave` if Cursor wants extra confidence (not required for slice completion)

---

## Completion (per WORKFLOW)

1. Claim: move this file `next/` → `in-progress/`
2. Implement + `./bin/ci-local`
3. `prompts/cursor/done/2026-06-21-2510-brave-direct-api-search/` with `prompt.md` + `output.md`
4. Do **not** commit; do **not** edit `TODO.md`

**Suggested commit message:**

```
refactor(search): Brave Web Search API direct client; drop langchain-community
```