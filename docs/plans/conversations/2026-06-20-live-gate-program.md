# Live gate program — opt-in regression suites (baseball + CRM)

**Date:** 2026-06-20  
**Participants:** Paul + Grok  
**Status:** Design lock for slice  
**Replaces:** ad hoc manual MCP/CLI sessions for regression detection

---

## Problem

- **Smoke / CI** uses temp fixtures and **mocked** LLMs — fast, no keys, does not prove live Lahman anchors (Aaron `0.305`, `755`, M4b dedup) or deployed CRM roots.
- **Manual gates** in `docs/manual-checks/` are thorough but time-consuming and not diffable run-to-run.
- Hank Aaron / CRM two-step sessions require real `.env` and `~/mycelium-networks/*` roots.

---

## Solution

**Live gate** tier: opt-in pytest suite + operator scripts. **Never** run from `bin/ci-local`.

| Piece | Role |
|-------|------|
| `@pytest.mark.live_gate` | Marker — excluded from CI smoke |
| `tests/live/gate_runner.py` | YAML catalog → step 1/2 `run_query` → assertions |
| `tests/live/conftest.py` | `load_dotenv`, root resolution, skip if preflight fails |
| `bin/gate-baseball-live` | Operator entry — baseball |
| `bin/gate-crm-live` | Operator entry — CRM |
| Scenario YAML | Executable spec (anchors, phases, depends_on) |
| `docs/manual-checks/runs/*.json` | Per-run reports (gitignored) |

**Transport:** in-process `run_query` (same graph as MCP). No Claude required.

---

## Paul locks

| Topic | Lock |
|-------|------|
| CI | **Never** invoke live gates from `ci-local` or GitHub CI |
| Root default | `~/mycelium-networks/baseball` / `~/mycelium-networks/crm` (override `MYCELIUM_NETWORK_ROOT`) |
| Env | `load_dotenv(repo/.env)`; baseball derive requires `OPENAI_API_KEY` + intent/codegen model vars |
| Bootstrap | **No full Lahman re-bootstrap** in gate — preflight asserts warehouse + registry exist |
| Cache | Baseball `--fresh-derive` clears batting `storage.json` + `intent_map.json` before derive phase |
| CRM research | **Optional phase** `--phase research` — requires `OPENAI_API_KEY` + `TAVILY_API_KEY`; may be flaky |
| CRM metering | **Optional phase** `--phase metering` — uses `crm-metering` network (separate root) |
| Anchors | Versioned JSON under `tests/live/anchors/`; `--discover` prints drift vs live root |
| Thorough | Catalog must cover manual gate tables (baseball hand-test M2–M4b; CRM MVR post-program + smoke-crm scenarios) |

---

## Baseball phases

| Phase | Source doc | LLM |
|-------|------------|-----|
| `preflight` | warehouse file, env, resolve Aaron | No |
| `identity` | partial lookup, negatives | No |
| `m2` | M2 extended #1–#7 | No |
| `derive` | M3 career_avg, M4 ops, M4b dedup | Yes |
| `infra` | describe_network blurb (optional subprocess or import) | No |

---

## CRM phases

| Phase | Source doc | Keys |
|-------|------------|------|
| `preflight` | 15 entities, `bind_values` shape | No |
| `protocol` | two-step, batch 645, fuzzy typo, create_on_deliver | No |
| `research` | email deliver (single + batch) | OpenAI + Tavily |
| `metering` | quote_required → assembled on `crm-metering` | OpenAI + Tavily |
| `negative` | not_found, legacy CLI rejected (subprocess) | No |

---

## Assertion vocabulary (YAML)

- `equals`, `approx` (+ `decimals`, `tolerance`)
- `contains` (string / provenance path)
- `outcome`, `total_matches`, `len_results`
- `same_provenance_timestamp_as` (scenario id)
- `audit_log_excludes` / `audit_log_includes` (debug substring)
- `skip_if_missing_env` on scenario or phase

---

## Non-goals (v1)

- MCP subprocess wire tests
- Full Lahman `--full` refresh in gate
- M3b chaos / injected SQL failures
- Admin UI browser automation
- `EntityQuery.question` (M5 deferred)

---

*Archived June 2026.*