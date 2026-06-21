# Live gate program — opt-in regression (June 2026)

**Status:** ✅ **Passed** — Baseball program sign-off **2026-06-21** (`27/27`); afternoon sweep **2026-06-20** (all four networks, 32 scenarios).
**Design:** [`docs/plans/conversations/2026-06-20-live-gate-program.md`](../plans/conversations/2026-06-20-live-gate-program.md)

Unified CLI for deployed example networks. Uses real roots under `~/mycelium-networks/<network>` and framework `.env`. **Never run from `ci-local`.**

**CLI note:** Step 2 must use the same `--network` (or `--network-dir`) as step 1; the CLI prints a stderr hint after step 1 and diagnoses cross-network `delivery_id` mismatches on step 2.

---

## Quick start

```bash
./bin/gate-live --list

# Full afternoon sweep (after baseball Lahman reload + .env keys)
./bin/gate-live baseball
./bin/gate-live crm
./bin/gate-live crm-metering
./bin/gate-live empty-crm

# Partial runs
./bin/gate-live crm --phase protocol
./bin/gate-live crm-metering --phase metering
./bin/gate-live baseball --phase m2
./bin/gate-live baseball --phase derive --no-fresh-derive   # keep derive cache
./bin/gate-live empty-crm --phase growth
./bin/gate-live baseball --discover
./bin/gate-live crm --json
```

---

## Networks

| Network | Default root | Phases | `refresh_before_gate` | `fresh_derive_before_gate` |
|---------|--------------|--------|-------------------------|----------------------------|
| `baseball` | `~/mycelium-networks/baseball` | preflight, identity, m2, **pitching**, **team_season**, **fielding**, **roster**, **franchise**, derive, infra | no | **yes** (derive phase only) |
| `crm` | `~/mycelium-networks/crm` | preflight, protocol, research, negative | **yes** | no |
| `crm-metering` | `~/mycelium-networks/crm-metering` | preflight, metering | **yes** | no |
| `empty-crm` | `~/mycelium-networks/empty-crm` | preflight, growth | **yes** | no |

Registry: [`tests/live/networks.yaml`](../../tests/live/networks.yaml)

Catalogs: [`tests/live/catalogs/`](../../tests/live/catalogs/)

**crm-metering:** `meter-01-quote` asserts `quote_required` on **step 1** (`requested_attributes: [email]`); `meter-02-deliver` accepts quote via captured `delivery_id` + `quote_id`.

---

## Prerequisites

### All networks

- Framework repo with `uv sync`
- `.env` at repo root (`load_dotenv` on each run)
- Deployed root under `~/mycelium-networks/<network>` (created on first run when auto-refresh applies)

**Auto-refresh (default):** `crm`, `crm-metering`, and `empty-crm` run `./bin/refresh-example-network <network> --yes` before scenarios so gates always start from a clean example snapshot. Use `./bin/gate-live <network> --no-refresh` to inspect a grown root without wiping. **Baseball** does not auto-refresh (Lahman bootstrap is slow) — refresh manually when needed.

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

**Derive cache (default on):** When the gate includes the **derive** phase (full run or `--phase derive`), `gate-live` automatically clears `agents/batting/storage.json` and `intent_map.json` before scenarios (`fresh_derive_before_gate` in registry). Use `--no-fresh-derive` to keep an existing cache for cache-hit checks. `--phase m2` alone does not clear derive cache.

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

Growth scenarios create the first entity from an empty registry. Auto-refresh wipes the root before each `./bin/gate-live empty-crm` run (no manual refresh required unless you pass `--no-refresh`).

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
| baseball | **34** |
| crm | 7 |
| crm-metering | 4 |
| empty-crm | 5 |

**Afternoon sweep 2026-06-20:** 32/32 pass (Paul). Notable fixes in tree before sweep: warm-cache intent inference removed (`bb-derive-02` `ops`), CLI step-2 network hints, `fresh_derive_before_gate` default, CRM auto-refresh, crm-metering catalog shape.

**Baseball program sign-off 2026-06-21:** **27/27** on optimized Lahman root (`~/mycelium-networks/baseball`). Anchor fix `da5b006` (Fielding sums for `bb-field-01`). Post-program gate: [`2026-06-21-baseball-program-post-program-gate.md`](2026-06-21-baseball-program-post-program-gate.md).

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
