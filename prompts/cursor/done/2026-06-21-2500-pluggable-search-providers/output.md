# Pluggable web search providers — output

## Summary

Finished Grok’s draft: provider-agnostic `src/tools/web_search.py` with **`SEARCH_PROVIDER`** (`tavily` | `exa` | `brave`), normalized `SearchHit`, LangChain tool name **`web_search`**, and backward-compat `tools.tavily` re-exports. **671 smoke tests pass** via `./bin/ci-local`.

## Review checklist (10 items)

| # | Item | Status | Notes |
|---|------|--------|-------|
| 1 | `web_search.py` tracked and complete | **Fixed** | Module complete; add to commit with other slice files |
| 2 | Default `SEARCH_PROVIDER=tavily` preserves behavior | **Pass** | Unset env → Tavily; regression tests with `TAVILY_API_KEY` only |
| 3 | `create_web_search_tool().name == "web_search"` | **Pass** | Unchanged from draft |
| 4 | Exa normalization (`SearchResponse.results` + dict) | **Pass** | + unit test with `SimpleNamespace` object rows |
| 5 | Brave normalization (JSON string + `link`) | **Pass** | + unit test for JSON string payload |
| 6 | Exa API errors not silent empty hits | **Fixed** | `WebSearchProviderError` via `_validate_provider_raw`; propagates to research `errors[]` via tool loop |
| 7 | Live gate skip uses active provider key | **Fixed** | `missing_env_vars`: `TAVILY_API_KEY` → `active_search_api_key_env()`; YAML unchanged |
| 8 | Docs README + architecture | **Fixed** | `SEARCH_PROVIDER` paragraph + `web_search.py` pointer |
| 9 | Mocked tests per provider | **Fixed** | `_search_tavily` / `_search_exa` / `_search_brave` smoke tests |
| 10 | `langchain-community` deprecation warning | **N/A** | Acceptable; Brave uses community tool; note only |

## Provider env matrix

| `SEARCH_PROVIDER` | Required key | LangChain backend |
|-------------------|--------------|-------------------|
| `tavily` (default) | `TAVILY_API_KEY` | `langchain_tavily.TavilySearch` |
| `exa` | `EXA_API_KEY` | `langchain_exa.ExaSearchResults` |
| `brave` | `BRAVE_SEARCH_API_KEY` | `langchain_community.tools.BraveSearch` |

Invalid `SEARCH_PROVIDER` → `is_web_search_available()` false; `search_provider()` raises `UnknownSearchProviderError`.

## Gate skip behavior

Research scenarios still list `TAVILY_API_KEY` in YAML (backward compat). **`tests/live/assertions.py`** treats that entry as “active search key present”:

- `SEARCH_PROVIDER=exa` + `EXA_API_KEY` → **runs** (Tavily key not required)
- `SEARCH_PROVIDER=exa` + only `TAVILY_API_KEY` → **skips** (missing `EXA_API_KEY`)

## Manual gate commands

**Tavily (default):**
```bash
SEARCH_PROVIDER=tavily ./bin/gate-live baseball   # or crm
# Requires OPENAI_API_KEY + TAVILY_API_KEY
```

**Exa spot-check:**
```bash
SEARCH_PROVIDER=exa EXA_API_KEY=... OPENAI_API_KEY=... ./bin/gate-live baseball
# bb-bio-research-01 / CRM research scenarios should run without TAVILY_API_KEY
```

## Key files

| Path | Role |
|------|------|
| `src/tools/web_search.py` | Source of truth |
| `src/tools/tavily.py` | Re-export shim |
| `src/tools/research.py` | `create_web_search_tool()` + tool name aliases |
| `tests/test_web_search.py` | Provider + normalization + mocked backends |
| `tests/live/assertions.py` | Provider-aware skip |
| `.env.example` | All three keys documented |

## Verification

```text
./bin/ci-local    # 671 passed
```

## For Grok + Paul

- Mark **2500** shipped; Grok draft retained with gaps closed.
- Commit should include **untracked** `src/tools/web_search.py` plus modified files from this slice.
- Optional manual: Exa/Brave live search on one CRM research scenario after Tavily gate green.

Suggested commit message:

```
feat(tools): pluggable SEARCH_PROVIDER for Tavily, Exa, Brave web search
```
