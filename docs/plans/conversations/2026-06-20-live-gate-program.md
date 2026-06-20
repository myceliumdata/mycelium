# Live gate program — opt-in regression (all example networks)

**Date:** 2026-06-20  
**Participants:** Paul + Grok  
**Status:** Design lock for slice (rev. unified `gate-live`)  
**Replaces:** ad hoc manual MCP/CLI sessions for regression detection

---

## Problem

- **Smoke / CI** uses temp fixtures and **mocked** LLMs — fast, no keys, does not prove live deployed roots.
- **Manual gates** are thorough but time-consuming.
- Multiple **example networks** need regression coverage: `baseball`, `crm`, `crm-metering`, `empty-crm`.

---

## Solution

**Single operator entry:** `bin/gate-live <network>` where `<network>` is the example name (same as `refresh-example-network`).

```bash
./bin/gate-live baseball --phase derive --fresh-derive
./bin/gate-live crm --phase protocol
./bin/gate-live crm-metering --phase metering
./bin/gate-live empty-crm --phase growth
./bin/gate-live --list
```

| Piece | Role |
|-------|------|
| `bin/gate-live` | Argparse → env vars → `pytest tests/live/ -m live_gate` |
| `tests/live/networks.yaml` | Registry: network → catalog, anchors, default root |
| `tests/live/catalogs/*.yaml` | Per-network scenario specs |
| `@pytest.mark.live_gate` | Opt-in marker — **never CI** |

**Default root:** `~/mycelium-networks/<network>` (override `MYCELIUM_NETWORK_ROOT`).

**Transport:** in-process `run_query`.

---

## Paul locks

| Topic | Lock |
|-------|------|
| CLI shape | **One script** `gate-live` + **required** network positional (not separate per-network bins) |
| Networks v1 | `baseball`, `crm`, `crm-metering`, `empty-crm` |
| CI | Never from `ci-local` |
| Env | `load_dotenv(repo/.env)` |
| Bootstrap | No in-gate full refresh; preflight asserts deployed state |
| empty-crm | Tests **cold start / growth** — 0 entities preflight, first row on step-2 deliver |
| crm-metering | Dedicated catalog; quote → accept arc (not folded into `crm` only) |
| Baseball cache | `--fresh-derive` for baseball derive phase only |

---

## Network summaries

| Network | Phases | Keys |
|---------|--------|------|
| **baseball** | preflight, identity, m2, derive, infra | Derive: OpenAI + model vars |
| **crm** | preflight, protocol, research, negative | Research: OpenAI + Tavily |
| **crm-metering** | preflight, metering | OpenAI + Tavily for email deliver |
| **empty-crm** | preflight, growth | OpenAI + Tavily if email on step 1 |

---

## Non-goals (v1)

- MCP subprocess, Admin UI, full Lahman re-bootstrap, M5 question field

---

*Archived June 2026.*