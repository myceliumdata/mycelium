# Brave direct API search — output

## Summary

Replaced `langchain_community.tools.BraveSearch` with a stdlib **`urllib.request`** client to Brave Web Search API. Removed **`langchain-community`** from dependencies. Same env vars, same `SearchHit` normalization, same research tool contract. **670 smoke tests pass** via `./bin/ci-local`.

## Changes

| Area | Detail |
|------|--------|
| `_brave_api_request` | `GET https://api.search.brave.com/res/v1/web/search` with `X-Subscription-Token`, `q`, `count` (1–20) |
| `_normalize_brave_hits` | Native `{"web": {"results": [...]}}` + legacy list/JSON-string/`link` shapes |
| Errors | HTTP 4xx/5xx, JSON `error` field → `WebSearchProviderError` |
| Dependencies | Removed `langchain-community` from `pyproject.toml`; `uv sync` updated lockfile |

## Verification

```text
rg langchain_community src/ pyproject.toml   # zero matches
./bin/ci-local                               # 670 passed
```

Deprecation warning on Brave path: **eliminated** (`test_brave_path_no_langchain_community_deprecation`).

## Tests added

| Test | Purpose |
|------|---------|
| `test_normalize_brave_native_api_response` | `web.results` with `url` + `description` |
| `test_search_brave_http_mocked` | `_brave_api_request` params + header path |
| `test_web_search_provider_error_on_brave_http_failure` | 401 → `WebSearchProviderError` |
| `test_brave_path_no_langchain_community_deprecation` | No sunset warning |

Existing brave normalization/backend tests unchanged.

## Live gate

**N/A** — internal swap. Paul already validated CRM + baseball gates with `SEARCH_PROVIDER=brave`. Optional re-check:

```bash
SEARCH_PROVIDER=brave BRAVE_SEARCH_API_KEY=... OPENAI_API_KEY=... ./bin/gate-live crm-metering --phase metering
```

## For Grok + Paul

- Mark **2510** shipped; `langchain-community` fully removed from repo.
- Tavily/Exa paths unchanged (`langchain-tavily`, `langchain-exa`).
- No operator-facing changes beyond quieter pytest (no deprecation warning).

Suggested commit message:

```
refactor(search): Brave Web Search API direct client; drop langchain-community
```
