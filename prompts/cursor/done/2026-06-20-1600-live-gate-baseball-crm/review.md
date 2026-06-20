# Review — live gate program (`gate-live`)

**Verdict:** **Approved + polish nits**

**CI:** `./bin/ci-local` — **591** smoke passed (includes 8 live-gate runner unit tests), ruff clean, admin-ui build ok.  
**Unit:** `uv run pytest tests/test_live_gate_runner_unit.py -q` — **8** passed.  
**Collect:** `uv run pytest tests/live/test_live_gate.py -m live_gate --collect-only` — 1 parametrized module (needs `LIVE_GATE_NETWORK` from `./bin/gate-live`).  
**CLI:** `./bin/gate-live --list` — four networks, phases, default roots.

---

## Delivery

| Check | Result |
|-------|--------|
| `output.md` matches files on disk | Pass |
| Prompt in `done/` | Pass — `prompt.md` present |
| Prompt removed from `next/` | **Fail** — duplicate still in `next/` (remove on commit) |
| `live_gate` excluded from `ci-local` | Pass — comment only; marker deselected |
| `docs/manual-checks/runs/` gitignored | Pass |

---

## Spec compliance

| Requirement | Result |
|-------------|--------|
| Single `bin/gate-live <network>` entry | Pass |
| Four networks in `networks.yaml` | Pass |
| YAML catalogs + anchors | Pass — 32 scenarios total (16/7/4/5) |
| `@pytest.mark.live_gate` only | Pass |
| `load_dotenv`, env vars, `--phase`, `--fresh-derive`, `--discover`, `--json`, `--root` | Pass |
| Operator doc + README one-liners | Pass |
| `pyyaml` + `live_gate` marker in `pyproject.toml` | Pass |
| Baseball ≥15 scenarios | Pass — 16 |
| CRM minimum scenarios | Pass — 7 (covers prompt list) |
| crm-metering quote → deliver | Pass — matches `demo-metering-negotiation` 3-step shape |
| empty-crm growth arc | Pass — 5 scenarios with `depends_on` chain |

---

## Diff reviewed

| Area | Files |
|------|--------|
| CLI | `bin/gate-live` |
| Framework | `tests/live/gate_runner.py`, `conftest.py`, `assertions.py`, `test_live_gate.py` |
| Data | `networks.yaml`, `catalogs/*.yaml`, `anchors/*.json` |
| Unit | `tests/test_live_gate_runner_unit.py` |
| Config | `pyproject.toml`, `uv.lock`, `.gitignore`, `bin/ci-local` |
| Docs | `docs/manual-checks/2026-06-20-live-gate-program.md`, hand-test pointer, example READMEs |

---

## Design notes

- **Metering catalog** correctly mirrors `bin/demo-metering-negotiation`: resolve → lookup+email `quote_required` → `delivery_id`+`quote_id` deliver.
- **Scenario context** (`depends_on`, `capture`, `same_timestamp_as`) uses session-scoped dict; pytest parametrization preserves catalog order — works for `bb-derive-03`, `meter-02-deliver`, empty-crm growth.
- **`--json`** runs `run_catalog` in-process (no pytest); failure path on pytest exit re-runs catalog for stderr summary table — reasonable.
- **`discover_anchor_drift`** gives operators a quick anchor sanity check without full gate.

---

## Polish nits (non-blocking)

| # | Item |
|---|------|
| N1 | **`crm-negative-01` (654 Ventures)** expects `lookup_suggested` via composite fuzzy scorer — **depends on uncommitted fuzzy-bind-field slice** (`entity_resolution.py`). Live `negative` phase fails on deployed CRM until that ships. |
| N2 | **Duplicate prompt** in `prompts/cursor/next/` — remove when committing (workflow). |
| N3 | **Do not commit** `tests/live/__pycache__/`, `examples/networks/baseball/checkpoints.sqlite`. |
| N4 | **empty-crm growth** mutates root — operator doc covers refresh; consider `--phase preflight` guard note in `--list` output. |
| N5 | **Network name** still `empty-crm` in registry (TODO targets `crm-empty` rename — separate slice). |
| N6 | `bin/ci-local` missing trailing newline (pre-existing pattern). |

---

## Commit hygiene

**Live-gate-only paths** (this commit):

- `bin/gate-live`, `tests/live/` (exclude `__pycache__`)
- `tests/test_live_gate_runner_unit.py`
- `.gitignore`, `bin/ci-local`, `pyproject.toml`, `uv.lock`
- `docs/manual-checks/2026-06-20-live-gate-program.md`
- `docs/manual-checks/2026-06-19-baseball-specialist-hand-test.md`
- `examples/networks/{baseball,crm,crm-metering,empty-crm}/README.md`
- `prompts/cursor/done/2026-06-20-1600-live-gate-baseball-crm/`
- Delete `prompts/cursor/next/2026-06-20-1600-live-gate-baseball-crm.md`

**Exclude** (separate slices): fuzzy bind-field (`entity_resolution.py`, fuzzy tests/docs), unrelated plan doc edits.

---

## For Paul

**Suggested commit:**

```
tests: unified gate-live regression for example networks (opt-in)
```

- Operator smoke: `./bin/gate-live --list`; then per-network phases when roots are deployed.
- Mark TODO live-gate item done after commit.
- **Next uncommitted slice:** fuzzy bind-field upgrade (`prompts/cursor/done/2026-06-18-2100-fuzzy-bind-field-suggestion-upgrade/`) — required for `crm-negative-01` live pass.