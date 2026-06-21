# Live gate program — opt-in regression (all example networks)

**Date:** 2026-06-20  
**Participants:** Paul + Grok  
**Status:** Shipped + afternoon sweep **passed** (2026-06-20)  
**Replaces:** ad hoc manual MCP/CLI sessions for regression detection

---

## Problem

- **Smoke / CI** uses temp fixtures and **mocked** LLMs — fast, no keys, does not prove live deployed roots.
- **Manual gates** are thorough but time-consuming.
- Multiple **example networks** need regression coverage: `baseball`, `crm`, `crm-metering`, `crm-empty`.

---

## Solution

**Single operator entry:** `bin/gate-live <network>` where `<network>` is the example name (same as `refresh-example-network`).

```bash
./bin/gate-live baseball          # auto-refreshes root first (full Lahman)
./bin/gate-live crm-seeded               # auto-refreshes root first
./bin/gate-live crm-metering
./bin/gate-live crm-empty
./bin/gate-live --list
```

| Piece | Role |
|-------|------|
| `bin/gate-live` | Argparse → env vars → `pytest tests/live/ -m live_gate` |
| `tests/live/networks.yaml` | Registry: network → catalog, anchors, default root, `refresh_before_gate` |
| `tests/live/catalogs/*.yaml` | Per-network scenario specs |
| `@pytest.mark.live_gate` | Opt-in marker — **never CI** |

**Default root:** `~/mycelium-networks/<network>` (override `MYCELIUM_NETWORK_ROOT`).

**Transport:** in-process `run_query`.

**Operator doc:** [`docs/manual-checks/2026-06-20-live-gate-program.md`](../../manual-checks/2026-06-20-live-gate-program.md)

---

## Paul locks

| Topic | Lock |
|-------|------|
| CLI shape | **One script** `gate-live` + **required** network positional (not separate per-network bins) |
| Networks v1 | `baseball`, `crm`, `crm-metering`, `crm-empty` |
| CI | Never from `ci-local` |
| Env | `load_dotenv(repo/.env)` |
| Auto-refresh | `refresh_before_gate: true` on all four networks — gate wipes root before scenarios (baseball includes full Lahman bootstrap and derive cache); `--no-refresh` to skip |
| crm-empty | Tests **cold start / growth** — 0 entities preflight, first row on step-2 deliver |
| crm-metering | Dedicated catalog; quote on step 1 (`quote_required`), deliver on step 2 with `delivery_id` + `quote_id` |
| CLI two-step UX | Step 1 stderr hint with `--network`; cross-network `delivery_id` diagnosis on step-2 miss |

---

## Network summaries

| Network | Phases | Keys |
|---------|--------|------|
| **baseball** | preflight, identity, m2, derive, infra | Derive: OpenAI + model vars |
| **crm** | preflight, protocol, research, negative | Research: OpenAI + Tavily |
| **crm-metering** | preflight, metering | OpenAI + Tavily for email deliver |
| **crm-empty** | preflight, growth | OpenAI + Tavily if email on step 1 |

---

## Non-goals (v1)

- MCP subprocess, Admin UI, M5 question field

---

*Archived June 2026. Updated after afternoon sweep pass; unified auto-refresh for all networks (2026-06-21).*