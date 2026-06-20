# Live gate program — unified `gate-live` (all example networks)

> **READY** — Claim per `prompts/cursor/WORKFLOW.md`.

**Design:** [`docs/plans/conversations/2026-06-20-live-gate-program.md`](../../docs/plans/conversations/2026-06-20-live-gate-program.md)

**Objective:** Ship **one** opt-in regression runner `bin/gate-live <network>` for **`baseball`**, **`crm`**, **`crm-metering`**, and **`empty-crm`**. Real deployed roots + `.env`. **Never CI.**

**Principles:**

- **Single script** with required network argument — not `gate-baseball-live` / `gate-crm-live`.
- Network registry `tests/live/networks.yaml` maps example name → catalog + anchors + default root.
- In-process `run_query`; YAML scenario catalogs; `@pytest.mark.live_gate` only.
- **Do not edit `TODO.md`.**

---

## Deliverables

| Item | Path |
|------|------|
| Operator script | **`bin/gate-live`** (only entry) |
| Network registry | `tests/live/networks.yaml` |
| Framework | `tests/live/gate_runner.py`, `conftest.py`, `assertions.py` |
| Catalogs | `tests/live/catalogs/{baseball,crm,crm_metering,empty_crm}.yaml` |
| Anchors | `tests/live/anchors/baseball_aaron_lahman_v2025.json`, `crm_seed_v1.json` |
| Tests | `tests/live/test_live_gate.py` (one module; network from env) |
| Unit tests | `tests/test_live_gate_runner_unit.py` (`smoke` OK) |
| Docs | `docs/manual-checks/2026-06-20-live-gate-program.md` |
| Gitignore | `docs/manual-checks/runs/` |

---

## 1 — `bin/gate-live`

```bash
./bin/gate-live <network> [options]

# Examples
./bin/gate-live baseball --phase derive --fresh-derive
./bin/gate-live crm --phase protocol
./bin/gate-live crm-metering --phase metering
./bin/gate-live empty-crm --phase growth
./bin/gate-live --list                    # networks + phases + default roots
./bin/gate-live baseball --discover       # anchor drift vs live root
./bin/gate-live crm --json
```

**Positional `network`:** required unless `--list`. Must be key in `tests/live/networks.yaml`. Validate early with clear error + hint to `--list`.

**Options:**

| Flag | Effect |
|------|--------|
| `--phase NAME` | Run one phase (repeatable or comma-separated) |
| `--fresh-derive` | Baseball only: rm `agents/batting/storage.json` + `intent_map.json` before derive phase |
| `--discover` | Print live anchor drift (entity counts, Aaron stats, seed persons) |
| `--json` | JSON report to stdout |
| `--root PATH` | Override `MYCELIUM_NETWORK_ROOT` |

**Bootstrap:** `load_dotenv(REPO_ROOT / ".env")`; set `LIVE_GATE_NETWORK`, `LIVE_GATE_PHASE`, `LIVE_GATE_FRESH_DERIVE`, `MYCELIUM_NETWORK_ROOT` from registry default `~/mycelium-networks/<network>`.

**Invoke:** `uv run pytest tests/live/test_live_gate.py -m live_gate -v`

**Exit:** non-zero on any scenario failure; stderr summary table.

**`bin/ci-local`:** comment only — `./bin/gate-live <network>` opt-in, never CI.

**`pyproject.toml`:** add `live_gate` marker.

---

## 2 — `tests/live/networks.yaml`

```yaml
baseball:
  catalog: catalogs/baseball.yaml
  anchors: anchors/baseball_aaron_lahman_v2025.json
  default_root: ~/mycelium-networks/baseball
  phases: [preflight, identity, m2, derive, infra]

crm:
  catalog: catalogs/crm.yaml
  anchors: anchors/crm_seed_v1.json
  default_root: ~/mycelium-networks/crm
  phases: [preflight, protocol, research, negative]

crm-metering:
  catalog: catalogs/crm_metering.yaml
  anchors: anchors/crm_seed_v1.json
  default_root: ~/mycelium-networks/crm-metering
  phases: [preflight, metering]

empty-crm:
  catalog: catalogs/empty_crm.yaml
  anchors: null
  default_root: ~/mycelium-networks/empty-crm
  phases: [preflight, growth]
```

Loader resolves paths relative to `tests/live/`.

---

## 3 — Shared framework

Same as prior spec: `gate_runner.py` loads catalog YAML; step 1/2 `run_query`; assertion vocabulary (`equals`, `approx`, `outcome`, `same_timestamp_as`, `skip_if_missing_env`, etc.).

**`conftest.py`:**

- Read `LIVE_GATE_NETWORK` → load registry entry → apply `NetworkPaths` to `MYCELIUM_NETWORK_ROOT`.
- **No** `refresh_example_network` in live gate.
- **No** `delenv OPENAI_API_KEY`.
- `reset_core_graph()` between scenarios.
- Session report → `docs/manual-checks/runs/{ts}-{network}-live-gate.json`.

**`test_live_gate.py`:**

- Single parametrized run over active network's catalog (filter by phase).
- `@pytest.mark.live_gate` only.

---

## 4 — Catalogs (minimum scenarios)

### `catalogs/baseball.yaml`

Phases: preflight, identity, m2, derive, infra — **15+ scenarios** from hand-test + M4b gate:

- Aaron resolve, M2 #1–#7, career_avg 0.305, cache, ops ≈ 0.928, M4b dedup, XYZZY negative.
- Derive phase: `skip_if_missing_env` for OpenAI + model vars.
- `--fresh-derive` support.

### `catalogs/crm.yaml`

Phases: preflight, protocol, research, negative — from `smoke-crm-e2e` + MVR post-program gate:

- 15 entities, bind_values, Nichanan, Andrea, 645 batch (3), fuzzy 654→645, create_on_deliver Nobody, batch email deliver.
- **No metering here** — crm-metering has its own catalog.

### `catalogs/crm_metering.yaml`

Phases: preflight, metering:

- Preflight: `metering.enabled` in network.json or quote path available; 15 entities.
- `meter-01-quote`: Paul Murphy / Acme + email → `quote_required` + quote_id + delivery_id.
- `meter-02-deliver`: depends_on meter-01; step2 with quote_id → `assembled`; email present or documented skip.
- Mirror `bin/demo-metering-negotiation` acceptance.
- `skip_if_missing_env: [OPENAI_API_KEY, TAVILY_API_KEY]`.

### `catalogs/empty_crm.yaml`

Phases: preflight, growth — from `empty-crm/README` + queries:

- `ec-preflight-01`: registry **0** entities (or empty entities store).
- `ec-growth-01`: Paul Murphy / Acme + email step1 → `lookup_resolved`, `create_on_deliver: true`, 0 matches.
- `ec-growth-02`: step2 deliver → `found` or `assembled`; **entity count becomes 1**.
- `ec-growth-03`: repeat same lookup step1 → `lookup_resolved`, **1 match**, no `create_on_deliver`.
- Optional step2 identity deliver on ec-growth-03 delivery_id.
- Research on growth step if email requested: skip_if_missing_env.

**Note:** empty-crm gate assumes a **fresh** empty root. Document in operator doc: refresh `empty-crm --yes` before gate if growth phase was run previously.

---

## 5 — Anchors

**`anchors/baseball_aaron_lahman_v2025.json`** — career_hr 755, career_avg 0.305, etc.

**`anchors/crm_seed_v1.json`** — shared by `crm` and `crm-metering`:

```json
{
  "seed_count": 15,
  "persons": {
    "nichanan": {"name": "Nichanan Kesonpat", "employer": "1k(x)"},
    "andrea": {"name": "Andrea Kalmans", "employer": "Lontra Ventures"},
    "paul_metering": {"name": "Paul Murphy", "employer": "Acme Corp"},
    "batch_employer": "645 Ventures",
    "batch_match_count": 3
  }
}
```

---

## 6 — Documentation

**`docs/manual-checks/2026-06-20-live-gate-program.md`**

- Unified CLI examples for all four networks.
- Prereqs per network (refresh commands).
- empty-crm: must be empty before growth phase.
- Phase / runtime / key matrix.
- Link `networks.yaml` + catalogs.

Update:

- `docs/manual-checks/2026-06-19-baseball-specialist-hand-test.md` — pointer to `./bin/gate-live baseball`
- `examples/networks/crm/README.md`, `crm-metering/README.md`, `empty-crm/README.md`, `baseball/README.md` — one line each.

---

## 7 — Verification

```bash
./bin/ci-local
uv run pytest tests/test_live_gate_runner_unit.py -q
uv run pytest -m live_gate --collect-only   # must not run in ci-local smoke

# Operator (deployed roots)
./bin/gate-live --list
./bin/gate-live crm --phase protocol
./bin/gate-live crm-metering --phase metering
./bin/gate-live empty-crm --phase growth    # fresh empty root
./bin/gate-live baseball --phase m2
```

---

## For Grok + Paul (`output.md`)

- Scenario counts per network
- `--list` output sample
- Suggested commit: `tests: unified gate-live regression for example networks (opt-in)`