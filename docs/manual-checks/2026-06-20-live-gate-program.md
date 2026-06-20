# Live gate program — opt-in regression (June 2026)

**Status:** Ready for operators  
**Design:** [`docs/plans/conversations/2026-06-20-live-gate-program.md`](../plans/conversations/2026-06-20-live-gate-program.md)

Unified CLI for deployed example networks. Uses real roots under `~/mycelium-networks/<network>` and framework `.env`. **Never run from `ci-local`.**

---

## Quick start

```bash
./bin/gate-live --list

./bin/gate-live crm --phase protocol
./bin/gate-live crm-metering --phase metering
./bin/gate-live baseball --phase m2
./bin/gate-live baseball --phase derive --fresh-derive
./bin/gate-live empty-crm --phase growth
./bin/gate-live baseball --discover
./bin/gate-live crm --json
```

---

## Networks

| Network | Default root | Phases |
|---------|--------------|--------|
| `baseball` | `~/mycelium-networks/baseball` | preflight, identity, m2, derive, infra |
| `crm` | `~/mycelium-networks/crm` | preflight, protocol, research, negative |
| `crm-metering` | `~/mycelium-networks/crm-metering` | preflight, metering |
| `empty-crm` | `~/mycelium-networks/empty-crm` | preflight, growth |

Registry: [`tests/live/networks.yaml`](../../tests/live/networks.yaml)  
Catalogs: [`tests/live/catalogs/`](../../tests/live/catalogs/)

---

## Prerequisites

### All networks

- Framework repo with `uv sync`
- `.env` at repo root (`load_dotenv` on each run)
- Deployed root: `./bin/refresh-example-network <network> --yes`

### Baseball

```bash
./bin/refresh-example-network baseball --yes   # full Lahman bootstrap (slow)
./bin/refresh-example-network baseball --sync-only   # pack-only updates
```

Derive phase needs:

```bash
OPENAI_API_KEY=...
MYCELIUM_COMPUTATION_CODEGEN_MODEL=gpt-4o
MYCELIUM_INTENT_NORMALIZATION_MODEL=gpt-4o-mini   # M4b synonym dedup
```

Use `--fresh-derive` to clear `agents/batting/storage.json` and `intent_map.json` before the derive phase.

### CRM

```bash
./bin/refresh-example-network crm --yes
```

Research phase needs `OPENAI_API_KEY` and `TAVILY_API_KEY`.

### CRM metering

```bash
./bin/refresh-example-network crm-metering --yes
```

Metering phase needs `OPENAI_API_KEY` and `TAVILY_API_KEY` (email research on deliver).

### Empty CRM

**Must be empty before growth phase.** Growth scenarios create the first entity.

```bash
./bin/refresh-example-network empty-crm --yes
./bin/gate-live empty-crm --phase preflight   # expect 0 entities
./bin/gate-live empty-crm --phase growth      # creates Paul Murphy row
```

Re-run growth only after refreshing to a clean root.

---

## Phase / key matrix

| Phase | Keys required |
|-------|----------------|
| baseball `derive` | `OPENAI_API_KEY`, `MYCELIUM_COMPUTATION_CODEGEN_MODEL` (+ intent model for M4b dedup) |
| crm `research` | `OPENAI_API_KEY`, `TAVILY_API_KEY` |
| crm-metering `metering` | `OPENAI_API_KEY`, `TAVILY_API_KEY` |
| empty-crm `growth` | `OPENAI_API_KEY`, `TAVILY_API_KEY` (when email requested on step 1) |

Scenarios with missing keys are **skipped** (not failed).

---

## Scenario counts (v1)

| Network | Scenarios |
|---------|-----------|
| baseball | 16 |
| crm | 7 |
| crm-metering | 4 |
| empty-crm | 5 |

---

## Reports

Session JSON reports: `docs/manual-checks/runs/{timestamp}-{network}-live-gate.json` (gitignored).

---

## Related manual gates

- Baseball hand test: [`2026-06-19-baseball-specialist-hand-test.md`](2026-06-19-baseball-specialist-hand-test.md) — use `./bin/gate-live baseball` for automated regression
- MVR post-program: [`2026-06-13-mvr-redesign-post-program-gate.md`](2026-06-13-mvr-redesign-post-program-gate.md)
- M4b intent: [`2026-06-19-baseball-m4b-intent-normalization-gate.md`](2026-06-19-baseball-m4b-intent-normalization-gate.md)

---

## Verification (developers)

```bash
./bin/ci-local
uv run pytest tests/test_live_gate_runner_unit.py -q
uv run pytest -m live_gate --collect-only   # must not run in ci-local smoke
```
