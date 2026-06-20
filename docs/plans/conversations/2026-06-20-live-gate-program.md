# Live gate program — opt-in regression (all example networks)

**Date:** 2026-06-20  
**Participants:** Paul + Grok  
**Status:** Shipped + afternoon sweep **passed** (2026-06-20)  
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
./bin/gate-live baseball          # derive cache auto-clears
./bin/gate-live crm               # auto-refreshes root first
./bin/gate-live crm-metering
./bin/gate-live empty-crm
./bin/gate-live --list
```

| Piece | Role |
|-------|------|
| `bin/gate-live` | Argparse → env vars → `pytest tests/live/ -m live_gate` |
| `tests/live/networks.yaml` | Registry: network → catalog, anchors, default root, refresh/fresh-derive flags |
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
| Networks v1 | `baseball`, `crm`, `crm-metering`, `empty-crm` |
| CI | Never from `ci-local` |
| Env | `load_dotenv(repo/.env)` |
| CRM refresh | `refresh_before_gate: true` on crm, crm-metering, empty-crm — gate wipes before scenarios; `--no-refresh` to skip |
| Baseball refresh | **No** in-gate full Lahman reload (slow); operator runs `refresh-example-network baseball` manually |
| Baseball derive cache | `fresh_derive_before_gate: true` — auto-clear batting storage + `intent_map.json` when derive phase runs; `--no-fresh-derive` to skip |
| empty-crm | Tests **cold start / growth** — 0 entities preflight, first row on step-2 deliver |
| crm-metering | Dedicated catalog; quote on step 1 (`quote_required`), deliver on step 2 with `delivery_id` + `quote_id` |
| CLI two-step UX | Step 1 stderr hint with `--network`; cross-network `delivery_id` diagnosis on step-2 miss |

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

- MCP subprocess, Admin UI, full Lahman re-bootstrap inside gate, M5 question field

---

*Archived June 2026. Updated after afternoon sweep pass.*