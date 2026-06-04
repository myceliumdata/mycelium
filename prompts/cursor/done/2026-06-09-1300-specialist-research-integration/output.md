# specialist-research-integration (slice 1300) — Output

## Claim

Moved `prompts/cursor/next/2026-06-04-1300-specialist-research-integration.md` → `prompts/cursor/in-progress/2026-06-09-1300-specialist-research-integration/prompt.md`.

**Depends on:** slices **1100**, **1200** (done).

## Summary

Closed Phase 1 specialist research with integration tests and documentation updates. No production code changes beyond docs/README.

### Tests (`tests/test_specialist_research_integration.py`)

All **`@pytest.mark.smoke`** (fully mocked; no API keys in CI):

| Test | Purpose |
|------|---------|
| `test_run_query_email_returns_found_in_same_response_when_research_mocked` | End-to-end `run_query` for `Test User` + `email`; mocks `run_field_research` → `results[0]["email"]` with value in **same** response; message does not claim unavailable |
| `test_run_query_email_pending_when_research_unavailable_no_crash` | `is_research_available()` false → pending messaging, no crash |

Fixture `research_integration_env` mirrors `test_core_graph` isolation (tmp DB/seed/registry/specialist dirs) and copies `data/categories.json` when present.

### Docs

- **`docs/architecture.md`** — Specialists section: sync research + Tavily; “Next phases” updated to **implemented Phase 1 sync** with link to `docs/plans/specialist-research-phase1.md` and async deferred.
- **`README.md`** — Short **Research latency** note under Quick start.

## Verification

```
$ uv run pytest -m smoke -q
42 passed, 11 deselected in 0.63s

$ uv run ruff check src tests
All checks passed!
```

## Phase 1 queue

**End of Phase 1 research queue** (`1100` → `1200` → `1300`). Optional follow-ups (not in `next/` unless requested): polish/timeouts, slice **1400** filter public results.
