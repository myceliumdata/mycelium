# Review — Brave direct API search (drop `langchain-community`)

**Verdict: Approved + polish nits**

**Reviewer:** Grok  
**Date:** 2026-06-21  
**CI:** `./bin/ci-local` — **670 smoke passed**, ruff clean, admin-ui build ok

---

## CI

| Step | Result |
|------|--------|
| `uv sync` | Pass |
| admin-ui build | Pass |
| ruff | Pass |
| smoke tests | **670 passed**, 144 deselected |

---

## Delivery

`output.md` matches implementation. Core files:

| File | Role |
|------|------|
| `src/tools/web_search.py` | `_brave_api_request`, native normalizer, no `langchain_community` |
| `pyproject.toml` | `langchain-community` removed |
| `uv.lock` | Regenerated |
| `tests/test_web_search.py` | 4 new smoke tests |

`rg langchain_community src/ pyproject.toml` → **zero** matches (tests only reference the string in deprecation assertion).

**Working-tree note:** Uncommitted changes outside this slice remain in the tree (`bin/gate-live`, `tests/live/*`, gate-live docs, `TODO.md`). Commit **2510 files only** separately from gate-live unified-refresh work.

---

## Spec compliance

| # | Criterion | Result |
|---|-----------|--------|
| 1 | Direct Brave Web Search API (`urllib.request`) | Pass |
| 2 | `BRAVE_SEARCH_API_KEY` / `SEARCH_PROVIDER=brave` unchanged | Pass |
| 3 | Native `web.results` + legacy list/JSON shapes | Pass |
| 4 | HTTP / JSON errors → `WebSearchProviderError` | Pass |
| 5 | Remove `langchain-community` dependency | Pass |
| 6 | Tavily / Exa paths unchanged | Pass |
| 7 | Required unit tests (native, HTTP mock, 401, no deprecation) | Pass |
| 8 | Live gate N/A | N/A — Paul validated CRM + baseball with Brave pre-slice |
| 9 | Do not edit `TODO.md` | **Fail (tree)** — `TODO.md` diff is Grok gate-live doc sync, not in slice `output.md`; revert if bundled with 2510 commit |

---

## Design critique

**Strong**

- `_brave_api_request` is small, testable, and matches the Tavily/Exa pattern (provider function + normalizer).
- `count` clamped to 1–20 per Brave API limits.
- Deprecation warning eliminated without new dependencies.
- `_validate_provider_raw` extended for Brave dict `error` field — consistent with Tavily.

**Acceptable**

- Error handling duplicated in `_brave_api_request` (HTTP + JSON `error`) and `_validate_provider_raw` — harmless belt-and-suspenders.

---

## Tests

| Test | Coverage |
|------|----------|
| `test_normalize_brave_native_api_response` | Native API shape |
| `test_search_brave_http_mocked` | `_brave_api_request` contract |
| `test_web_search_provider_error_on_brave_http_failure` | Loud fail through `web_search` |
| `test_brave_path_no_langchain_community_deprecation` | Sunset warning gone |
| Legacy brave list/JSON tests | Backward compat |

**Gap (non-blocking):** No test that exercises real `urllib` path (e.g. `HTTPError` with mocked `urlopen`). Current tests patch `_brave_api_request` — sufficient for smoke.

---

## Nits (non-blocking)

| ID | Nit |
|----|-----|
| N1 | `test_web_search_brave_backend_mocked` still mocks `_search_brave` returning a **list**; production returns a **dict**. Works via legacy normalizer path; update mock to `{"web": {"results": [...]}}` for realism. |
| N2 | Empty Brave response (`{"web": {}}`) returns `[]` silently — acceptable; optional future test. |

Program polish backlog: none (not MVR / entity-protocol).

---

## For Paul

- **Commit (2510 only):** `refactor(search): Brave Web Search API direct client; drop langchain-community`
- **Files to stage:** `src/tools/web_search.py`, `tests/test_web_search.py`, `pyproject.toml`, `uv.lock`, `prompts/cursor/done/2026-06-21-2510-brave-direct-api-search/`
- **Do not stage** gate-live / live-test / doc / `TODO.md` changes in the same commit unless you want one combined commit.
- **Push:** local only until you ask.
- Paul already confirmed Brave live gates (CRM + baseball); no mandatory re-run for this refactor.