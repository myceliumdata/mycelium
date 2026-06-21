# Pluggable web search providers (Tavily, Exa, Brave)

> **READY** — Paul requirement (2026-06-21): integrate **Exa** and **Brave** alongside **Tavily**; select backend via **`SEARCH_PROVIDER`**. **Do not edit `TODO.md`.**

## Context — Grok draft on working tree

Grok started this slice locally (unreviewed). **Claim this prompt and finish it** — do not rewrite from scratch unless the draft is wrong.

| Path | Status |
|------|--------|
| `src/tools/web_search.py` | **Untracked** — must be added |
| `src/tools/tavily.py` | Re-export shim (was full implementation) |
| `src/tools/research.py` | Uses `create_web_search_tool()` |
| `src/tools/__init__.py` | Exports from `web_search` |
| `tests/test_web_search.py` | Provider smoke tests |
| `.env.example` | `SEARCH_PROVIDER` + key comments |
| `pyproject.toml` / `uv.lock` | `langchain-exa`, `langchain-community` |

Run `git status` first. Treat Grok’s code as a draft; fix gaps in **Review checklist** below.

---

## Objective

Provider-agnostic web search for specialist research (`run_field_research` tool loop):

1. **`SEARCH_PROVIDER`** env: `tavily` (default) | `exa` | `brave`
2. **Keep Tavily** as default; no behavior change when unset
3. **Normalized `SearchHit`** (`url`, `title`, `snippet`, optional `score`) regardless of provider
4. **LangChain tool name `web_search`** — must match research Jinja templates (`_system.j2`, bind hints)
5. **`tools.tavily`** remains importable (backward-compat re-exports)

---

## Design (locked)

### Module layout

| Module | Role |
|--------|------|
| `src/tools/web_search.py` | **Source of truth**: `search_provider()`, `is_web_search_available()`, `web_search()`, `create_web_search_tool()`, `SearchHit`, provider normalizers |
| `src/tools/tavily.py` | Thin re-export shim only — no duplicated logic |
| `src/tools/research.py` | Import from `web_search` only; bind `create_web_search_tool()` in `_run_llm_loop` |

### Env vars

| `SEARCH_PROVIDER` | Required key |
|-------------------|--------------|
| `tavily` (default) | `TAVILY_API_KEY` |
| `exa` | `EXA_API_KEY` |
| `brave` | `BRAVE_SEARCH_API_KEY` |

Invalid `SEARCH_PROVIDER` → `is_web_search_available()` is `False`; `search_provider()` raises `UnknownSearchProviderError`.

Tavily-only kwargs (`topic`, `search_depth`) are ignored for Exa/Brave.

### Research loop

- Tool exposed to LLM: **`web_search`** (not `tavily_search`)
- `tools_by_name` aliases: `web_search`, `tavily_search`, `exa_search_results_json`, `brave_search` (LLM may call legacy names)
- Tool result shape: Tavily-like `{"query", "results": [{url, title, content, score?}]}` for consistent `ToolMessage` text

### Dependencies

- Keep `langchain-tavily`
- Add `langchain-exa`, `langchain-community` (Brave tool) — already in draft `pyproject.toml`; run `uv sync`

---

## Review checklist (Grok draft — verify and fix)

Cursor must explicitly confirm each item in `output.md`:

| # | Item | Draft status | Action if needed |
|---|------|--------------|------------------|
| 1 | `web_search.py` tracked and complete | Untracked | `git add`; no missing exports |
| 2 | Default `SEARCH_PROVIDER=tavily` preserves existing behavior | OK | Regression: tests with only `TAVILY_API_KEY` |
| 3 | `create_web_search_tool().name == "web_search"` | OK | Keep |
| 4 | Exa normalization handles `SearchResponse.results` + dict rows | OK | Add unit test with mock object/dict |
| 5 | Brave normalization handles JSON string + `link` field | OK | Add unit test |
| 6 | Exa API errors (`repr(e)` string) not silently empty hits | **Gap** | Surface as exception or explicit tool error in research `errors[]`; do not return `[]` as success |
| 7 | Live gate `skip_if_missing_env` still lists `TAVILY_API_KEY` only | **Gap** | Research scenarios must skip when **active provider** key missing (see below) |
| 8 | Docs: `README.md`, `docs/architecture.md` still Tavily-only | **Gap** | Short pointer to `SEARCH_PROVIDER` + `web_search.py` |
| 9 | Mocked tests per provider (`exa`, `brave`) | **Gap** | At least one smoke test each patching `_search_exa` / `_search_brave` |
| 10 | `langchain-community` deprecation warning | Acceptable | Note in `output.md`; no blocker |

---

## Live gate (required — provider-aware skip)

Research scenarios currently use:

```yaml
skip_if_missing_env:
  - OPENAI_API_KEY
  - TAVILY_API_KEY
```

**Problem:** With `SEARCH_PROVIDER=exa` + `EXA_API_KEY`, scenarios still skip (TAVILY missing). With `SEARCH_PROVIDER=exa` but only `TAVILY_API_KEY` set, scenarios run and fail.

**Fix (preferred):** In `tests/live/gate_runner.py` (or `tests/live/assertions.py`), add helper e.g. `research_search_env_var()` mirroring `web_search._PROVIDER_KEY_ENV`. For scenarios that list `TAVILY_API_KEY` in `skip_if_missing_env`, treat “search key present” as: **key for active `SEARCH_PROVIDER` is set** (still require `OPENAI_API_KEY`).

- Do **not** remove `TAVILY_API_KEY` from YAML yet (backward compat for gate docs); implement smart skip OR document replacement with a symbolic name like `SEARCH_API_KEY` — pick one approach and document in `output.md`.
- **No new gate scenarios** required; existing `bb-bio-research-01` / CRM research scenarios must pass unchanged with `SEARCH_PROVIDER=tavily` + Tavily keys.
- **Manual verify note** in `output.md`: Paul can run `./bin/gate-live baseball` with `SEARCH_PROVIDER=exa` + `EXA_API_KEY` after anchor-unchanged pass on Tavily.

**Mark:** `@pytest.mark.live_gate` only — never default CI.

---

## Tests

| Layer | Requirement |
|-------|-------------|
| `tests/test_web_search.py` | Provider default/reject; normalize Tavily/Exa/Brave; `is_web_search_available` per provider; mocked `_search_*` for **all three** providers |
| `tests/test_research.py` | Existing smokes green; `is_research_available` with each provider key |
| Regression | `./bin/ci-local` green (663+ smoke) |

---

## Docs (may modify)

- `.env.example` — already drafted; verify comments
- `README.md` — one paragraph: `SEARCH_PROVIDER`, three keys, default Tavily
- `docs/architecture.md` — research line: `tools/web_search.py` not Tavily-only

Do **not** expand scope to Firecrawl, Serper, or live provider A/B benchmarks.

---

## Constraints

- No specialist/pack changes
- No `derive_on_miss` / ontology changes
- Thin wrapper only — no second LLM inside search APIs
- `./bin/ci-local` must pass

---

## Output

Follow `prompts/cursor/WORKFLOW.md`. Deliver under `prompts/cursor/done/2026-06-21-2500-pluggable-search-providers/`.

In `output.md` **For Grok + Paul**:

- Review checklist table (all 10 items: pass / fixed / N/A)
- Provider env matrix
- Gate skip behavior after fix
- Manual gate commands for Tavily vs Exa spot-check

Suggested commit message:

```
feat(tools): pluggable SEARCH_PROVIDER for Tavily, Exa, Brave web search
```