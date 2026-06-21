# Review: 2026-06-21-2500-pluggable-search-providers

**Verdict: Approved + polish nits**

## CI

| Step | Result |
|------|--------|
| `uv sync --all-extras` | Pass |
| `admin-ui` build | Pass |
| `ruff` | Pass |
| smoke pytest | **671 passed**, 144 deselected |

Grok re-ran `./bin/ci-local` 2026-06-21 — matches Cursor `output.md`.

## Delivery

`output.md` claims match working tree. All prompt-required code present:

| File | Status |
|------|--------|
| `src/tools/web_search.py` | New — source of truth |
| `src/tools/tavily.py` | Re-export shim |
| `src/tools/research.py` | `create_web_search_tool()` + aliases |
| `src/tools/__init__.py` | Exports updated |
| `tests/test_web_search.py` | Provider + normalize + mock backends |
| `tests/test_research.py` | Exa/Brave `is_research_available` |
| `tests/live/assertions.py` | Provider-aware `TAVILY_API_KEY` skip alias |
| `tests/test_live_gate_runner_unit.py` | Skip alias unit test |
| `.env.example`, `README.md`, `docs/architecture.md` | Updated |
| `pyproject.toml`, `uv.lock` | `langchain-exa`, `langchain-community` |

## Diff reviewed

Read in full:

- `src/tools/web_search.py`
- `src/tools/tavily.py`, `src/tools/__init__.py`, `src/tools/research.py`
- `tests/test_web_search.py`, `tests/test_research.py`
- `tests/live/assertions.py`, `tests/test_live_gate_runner_unit.py`
- `.env.example`, `README.md`, `docs/architecture.md` (grep + sections)
- `pyproject.toml` dependency lines

`/review` subagent not used (slice scope is bounded; full read sufficient).

## Spec compliance

| Criterion | Result |
|-----------|--------|
| `SEARCH_PROVIDER` tavily \| exa \| brave | Pass |
| Tavily default; unset → Tavily | Pass |
| Keep Tavily; backward-compat `tools.tavily` | Pass |
| Normalized `SearchHit` | Pass |
| LangChain tool name `web_search` | Pass |
| No specialist/pack changes | Pass |
| Provider-aware live gate skip | Pass |
| Exa errors not silent empty hits | Pass (`WebSearchProviderError`) |
| Docs README + architecture | Pass |
| Mocked tests all three providers | Pass |
| `./bin/ci-local` green | Pass |
| Live gate new scenarios | N/A (not required) |

## Legacy / dual-path

- Default `SEARCH_PROVIDER=tavily` + `TAVILY_API_KEY` only: unchanged research path.
- `create_tavily_search_tool()` still returns raw `TavilySearch` for Tavily-only callers.
- Gate YAML still lists `TAVILY_API_KEY`; `missing_env_vars` remaps to active provider key — tested.

## External validation (Paul)

Paul reported **full live gate pass on all examples with `SEARCH_PROVIDER=exa`** before this review. Confirms no silent Tavily fallback and end-to-end research on Exa.

## Design critique

**Strong**

- Clean module split: `web_search.py` source of truth, `tavily.py` shim.
- Unified `web_search` tool name fixes prior `tavily_search` / prompt mismatch.
- Gate skip alias avoids YAML churn while fixing Exa-only runs.
- Strict provider routing in `_run_provider_search` — no cross-provider fallback.

**Acceptable tradeoffs**

- Brave via deprecated `langchain-community` — fine for v1; migrate when standalone Brave package exists.
- `_validate_provider_raw` Exa-only — Tavily quota/errors still rely on invoke exceptions or empty normalize (pre-existing; see backlog).

## Nits (non-blocking)

| ID | Severity | Item | Suggested follow-on |
|----|----------|------|---------------------|
| N1 | polish | `docs/onboarding.md` still says `TAVILY_API_KEY` only | One-line `SEARCH_PROVIDER` pointer |
| N2 | polish | `docs/architecture.md` credentials table still lists `TAVILY_API_KEY` without provider note | Add `SEARCH_PROVIDER` + active key |
| N3 | polish | `docs/plans/specialist-research-phase1.md` still Tavily-only | Optional doc refresh slice |
| N4 | polish | `_validate_provider_raw` not applied to Tavily/Brave error strings | Extend when hardening research errors (432 surfacing) |
| N5 | polish | `web_search()` docstring omits `WebSearchProviderError` in Raises | Trivial doc fix |

No fix slice required.

## For Paul

- **Commit:** Grok commits locally after this review.
- **Push:** Paul only, when ready.
- **Suggested message:** `feat(tools): pluggable SEARCH_PROVIDER for Tavily, Exa, Brave web search`
- **Ops:** `SEARCH_PROVIDER=exa` + `EXA_API_KEY` validated on live gate; Tavily remains default for unchanged deploys.