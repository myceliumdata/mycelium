# Live gate program — baseball + CRM (opt-in regression)

> **READY** — Claim per `prompts/cursor/WORKFLOW.md`.

**Design:** [`docs/plans/conversations/2026-06-20-live-gate-program.md`](../../docs/plans/conversations/2026-06-20-live-gate-program.md)

**Objective:** Ship **opt-in live regression gates** that reproduce manual hand-test / MVR gate sessions against **deployed** network roots + real `.env`. **Never** run from CI.

**Principles:**

- In-process `run_query` (same as MCP graph path).
- Scenario **YAML catalogs** + versioned **anchor JSON** — hand-test docs remain human spec; YAML is executable spec.
- `@pytest.mark.live_gate` only — **do not** add `smoke` marker to live tests.
- **Do not edit `TODO.md`.**
- Reuse patterns from `bin/smoke-baseball-e2e` / `bin/smoke-crm-e2e` for reporting (scenario results + JSON report).

---

## Deliverables

| Item | Path |
|------|------|
| Marker | `pyproject.toml` — `live_gate` |
| Framework | `tests/live/gate_runner.py`, `tests/live/conftest.py`, `tests/live/assertions.py` |
| Baseball catalog | `tests/live/catalogs/baseball_lahman_gate.yaml` |
| Baseball anchors | `tests/live/anchors/baseball_aaron_lahman_v2025.json` |
| Baseball tests | `tests/live/test_baseball_lahman_gate.py` |
| CRM catalog | `tests/live/catalogs/crm_gate.yaml` |
| CRM anchors | `tests/live/anchors/crm_seed_v1.json` |
| CRM tests | `tests/live/test_crm_live_gate.py` |
| Operator scripts | `bin/gate-baseball-live`, `bin/gate-crm-live` |
| Docs | `docs/manual-checks/2026-06-20-live-gate-program.md` |
| Gitignore | `docs/manual-checks/runs/` |
| CI guard | Comment in `bin/ci-local` — live gates excluded |

---

## 1 — Pytest marker + CI exclusion

**`pyproject.toml`:**

```toml
"live_gate: real deployed network root + optional live LLM; opt-in only — never CI"
```

**`bin/ci-local`:** add comment after smoke line: live gates are `./bin/gate-baseball-live` / `./bin/gate-crm-live` only.

**`.gitignore`:** `docs/manual-checks/runs/`

---

## 2 — Shared framework (`tests/live/`)

### `conftest.py`

- Session-scoped `load_dotenv(REPO_ROOT / ".env")`.
- Fixtures: `repo_root`, `network_root` from env (see defaults below).
- `gate_report_path` — write JSON to `docs/manual-checks/runs/{timestamp}-{network}-live-gate.json` on session end (pytest hook or fixture finalizer).
- **Do not** `monkeypatch.delenv("OPENAI_API_KEY")` in live tests.
- **Do not** call `refresh_example_network` for live gates (uses existing deployed root).
- `reset_core_graph()` between scenarios (match smoke scripts).

### `gate_runner.py`

- Load YAML catalog: `id`, `phase`, `network`, `depends_on`, `requires_fresh_cache`, `skip_if_missing_env[]`.
- Step runner: build `EntityQuery` from `lookup` / `requested_attributes` / `provenance` → `run_query` step 1 → step 2 with `delivery_id`.
- Phase filter from env `LIVE_GATE_PHASE` or pytest `-k`.
- `--fresh-derive` equivalent: env `LIVE_GATE_FRESH_DERIVE=1` deletes `agents/batting/storage.json` and `intent_map.json` under baseball root before `derive` phase (in conftest or runner).
- Store scenario artifacts (response public dict, duration_ms) for report.

### `assertions.py`

Implement assertion types from design doc:

- `outcome`, `total_matches`, `results_count`
- `results.{attr}.equals` / `approx` / `matches` (regex)
- `provenance_path` dot-path checks (`contains`, `equals`)
- `same_timestamp_as` — compare provenance `at` across scenario ids (store in runner state)
- `delivery.create_on_deliver` bool
- `suggestions[0].suggested_lookup` equals
- `audit_log_excludes` — parse `response.debug` or state audit if exposed

Parametrize tests from YAML: one pytest per scenario or one test loops catalog (prefer parametrized `ids=` for clear failures).

---

## 3 — Baseball

### Defaults

- `MYCELIUM_NETWORK_ROOT` default: `~/mycelium-networks/baseball` (expanduser).
- Player: **Hank Aaron** — resolve `id`, `lahman.playerID` via preflight partial lookup scenario.

### Anchors `tests/live/anchors/baseball_aaron_lahman_v2025.json`

```json
{
  "lahman_version": "v2025.1",
  "player": "Hank Aaron",
  "player_id": "aaronha01",
  "career_hr": 755,
  "career_rbi": 2297,
  "career_hits": 3771,
  "career_avg": 0.305,
  "birth_date": "1934-02-05",
  "bats": "R",
  "birth_city": "Mobile",
  "ops_approx": 0.928,
  "ops_tolerance": 0.05
}
```

Use `{anchor: career_hr}` in YAML or loader resolves anchors.

### Catalog `tests/live/catalogs/baseball_lahman_gate.yaml`

**Minimum scenarios (map from hand-test + M4b gate):**

| id | phase | Summary |
|----|-------|---------|
| `bb-preflight-warehouse` | preflight | `warehouse/lahman.sqlite` exists |
| `bb-preflight-resolve-aaron` | preflight | partial `{player: Hank Aaron}` → `lookup_resolved`, capture id |
| `bb-id-01-negative-xyzzy` | identity | `XYZZY` → `not_found` |
| `bb-m2-01-career-hr-birth` | m2 | `career_hr` + `birth_date`, provenance warehouse + inline |
| `bb-m2-02-career-rbi-hits` | m2 | 2297, 3771 |
| `bb-m2-03-six-attr` | m2 | debut + career + birth anchors |
| `bb-m2-04-bio-raw` | m2 | bats, throws, birth_city |
| `bb-m2-05-cache-hit` | m2 | repeat m2-03; same values; provenance version id unchanged |
| `bb-derive-01-career-avg` | derive | `requires_fresh_cache`; career_avg ≈ 0.305; provenance computation |
| `bb-derive-02-career-avg-cache` | derive | depends_on bb-derive-01; same value; same provenance `at` |
| `bb-derive-03-career-hr-regression` | derive | career_hr still 755 (manifest, no derive) |
| `bb-derive-04-ops` | derive | ops non-N/A, numeric; optional approx 0.928 if anchor set |
| `bb-m4b-01-career-avg` | derive | fresh cache variant or subphase after 04 clear intent map only |
| `bb-m4b-02-batting-average-dedup` | derive | depends_on m4b-01; same 0.305; same timestamp; `intent_slug: career_batting_average` |

Use `skip_if_missing_env: [OPENAI_API_KEY, MYCELIUM_COMPUTATION_CODEGEN_MODEL, MYCELIUM_INTENT_NORMALIZATION_MODEL]` on derive phase scenarios.

### `bin/gate-baseball-live`

```bash
./bin/gate-baseball-live                    # all phases
./bin/gate-baseball-live --phase m2         # no LLM
./bin/gate-baseball-live --phase derive --fresh-derive
./bin/gate-baseball-live --discover         # print Aaron id, debut bind, anchor drift
./bin/gate-baseball-live --list
./bin/gate-baseball-live --json             # report only
```

Implementation: argparse → set `MYCELIUM_NETWORK_ROOT`, `LIVE_GATE_PHASE`, `LIVE_GATE_FRESH_DERIVE` → `uv run pytest tests/live/test_baseball_lahman_gate.py -m live_gate -v`.

`load_dotenv` in script bootstrap (like `bin/baseball-query`).

Exit non-zero on any failure; print summary table to stderr.

---

## 4 — CRM

### Defaults

- `MYCELIUM_NETWORK_ROOT` default: `~/mycelium-networks/crm`.
- Metering scenarios: switch root to `~/mycelium-networks/crm-metering` via scenario `network: crm-metering` field.

### Anchors `tests/live/anchors/crm_seed_v1.json`

Seed-known rows (from `examples/networks/crm/seed.json`):

```json
{
  "seed_count": 15,
  "persons": {
    "nichanan": {"name": "Nichanan Kesonpat", "employer": "1k(x)"},
    "andrea": {"name": "Andrea Kalmans", "employer": "Lontra Ventures"},
    "batch_employer": "645 Ventures",
    "batch_match_count": 3
  }
}
```

### Catalog `tests/live/catalogs/crm_gate.yaml`

**Minimum scenarios (map from `bin/smoke-crm-e2e` + `docs/manual-checks/2026-06-13-mvr-redesign-post-program-gate.md`):**

| id | phase | Summary |
|----|-------|---------|
| `crm-preflight-entities` | preflight | registry count 15; sample person discoverable |
| `crm-preflight-bind-values` | preflight | first entity has `bind_values.name` / `employer` (read entities.json) |
| `crm-proto-01-exact-identity` | protocol | Nichanan full MVR → step2 `found` |
| `crm-proto-02-partial-batch-resolve` | protocol | employer 645 Ventures + email step1; 3 matches; empty results |
| `crm-proto-03-batch-deliver` | protocol | step2 assembled; 3 distinct ids |
| `crm-proto-04-fuzzy-employer` | protocol | `654 Ventures` → `lookup_suggested` → 645 |
| `crm-proto-05-create-on-deliver` | protocol | Nobody Here / Nowhere Inc → `create_on_deliver` |
| `crm-proto-06-andrea` | protocol | Andrea Kalmans / Lontra Ventures (MVR gate check 6) |
| `crm-negative-01-not-found` | negative | impossible bind → `not_found` or 0-hit create path per policy |
| `crm-research-01-email-single` | research | Paul Murphy / Acme Corp + email; assembled; email non-empty **or** document pending if keys weak |
| `crm-research-02-email-batch` | research | 645 batch + email step2; 3 rows with email key present |
| `crm-metering-01-quote` | metering | crm-metering: Paul Murphy Acme + email → `quote_required` |
| `crm-metering-02-deliver` | metering | depends_on metering-01; quote_id + delivery_id → `assembled` |

Research/metering: `skip_if_missing_env: [OPENAI_API_KEY, TAVILY_API_KEY]`.

For research tests: **do not mock** Tavily. Accept `assembled` with non-empty email OR skip with clear message if keys missing. Optionally allow `pending` only if documented in scenario `allowed_outcomes` — prefer strict when keys present.

### `bin/gate-crm-live`

Same flags as baseball (`--phase protocol|research|metering`, `--discover`, `--list`, `--json`).

---

## 5 — Documentation

**`docs/manual-checks/2026-06-20-live-gate-program.md`**

- Operator quick start (prereqs, refresh `--sync-only` baseball / `--yes` crm when needed).
- Phase tables + expected runtime / LLM cost notes.
- Link catalogs as source of truth.
- Update baseball hand-test doc: add one paragraph pointing to `./bin/gate-baseball-live`.
- Update `examples/networks/crm/README.md`: add live gate paragraph.

---

## 6 — Tests of the framework

**`tests/test_live_gate_runner_unit.py`** (smoke marker OK):

- Load minimal fake YAML; assert assertion helpers with fixture dicts.
- No live root required.

Live gate tests themselves: `@pytest.mark.live_gate` only.

---

## Verification

```bash
./bin/ci-local   # must NOT collect live_gate tests
uv run pytest tests/test_live_gate_runner_unit.py -q

# Operator (Paul) — requires deployed roots:
./bin/gate-crm-live --phase protocol
./bin/gate-baseball-live --phase m2
./bin/gate-baseball-live --phase derive --fresh-derive   # needs OPENAI_API_KEY
```

Confirm `pytest -m smoke` does not run live_gate tests.

---

## For Grok + Paul (`output.md`)

- Scenario counts per network
- Sample report JSON path
- Any anchor drift discovered on first `--discover`
- Suggested commit: `tests: live gate regression suites for baseball and CRM (opt-in)`