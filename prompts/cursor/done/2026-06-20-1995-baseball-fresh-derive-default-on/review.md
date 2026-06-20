# Review — baseball live gate default fresh-derive

**Verdict:** **Approved**

**CI:** `./bin/ci-local` — **611** smoke passed, ruff clean, admin-ui build ok (Grok, 2026-06-20).  
**Slice pytest:** `tests/test_live_gate_runner_unit.py` — **16** passed.

---

## Delivery

| Check | Result |
|-------|--------|
| `output.md` matches implementation | Pass |
| Prompt in `done/` | Pass |
| `TODO.md` untouched | Pass |
| `prompts/cursor/next/` empty | Pass per Cursor `output.md` |

---

## Spec compliance

| # | Exit criterion | Result |
|---|----------------|--------|
| 1 | Baseball derive gate clears cache by default; `--no-fresh-derive` skips | Pass — `should_fresh_derive()` + registry flag |
| 2 | Non-derive baseball phases do not clear | Pass — `derive_phase_in_scope` |
| 3 | `--list` shows `fresh_derive_before_gate` | Pass |
| 4 | Unit tests cover helper + registry | Pass — 6 new `should_fresh_derive` / flag tests |
| 5 | Manual gate doc updated | Pass |
| 6 | `./bin/ci-local` green | Pass — 611 smoke |

---

## Diff reviewed

| File | Grok read |
|------|-----------|
| `bin/gate-live` | Full file |
| `tests/live/gate_runner.py` | `NetworkEntry`, `should_fresh_derive`, cache helpers, `run_scenario` validation |
| `tests/live/networks.yaml` | Full file |
| `tests/test_live_gate_runner_unit.py` | Full file |
| `docs/manual-checks/2026-06-20-live-gate-program.md` | Quick start + Baseball + auto-refresh sections |
| `prompts/cursor/done/2026-06-20-1995-baseball-fresh-derive-default-on/output.md` | Claims vs diff |

---

## Design critique

**Strong**

- Mirrors `refresh_before_gate` / `--no-refresh` — consistent operator model.
- `should_fresh_derive()` in `gate_runner.py` is unit-testable; logic matches design lock table.
- Stale-cache **warning** when `--no-fresh-derive` + derive in scope + files exist — good guardrail.
- `LIVE_GATE_FRESH_DERIVE` set on auto-clear, not only explicit flag.
- In-run `bb-derive-01` → `03` state unchanged (clear once before pytest).

**Bundled in same diff (acceptable)**

- `refresh_before_gate` auto-refresh for CRM networks — earlier live-gate program work; lands coherently with registry + `--no-refresh`.
- `ValidationError` → failed scenario in `run_scenario` — helps invalid catalog fail clearly (crm-metering fix path).
- Failure-summary `try/except` in `gate-live` — avoids secondary crash on summary.

**Minor**

- Stderr always prints "Clearing baseball derive cache: …" when `do_fresh_derive`, even if files were already absent — slightly noisier than old "only when removed" behavior; non-blocking.

---

## Nits

| # | Severity | Item |
|---|----------|------|
| N1 | Non-blocking | Clear message prints even when no files deleted |
| N2 | Info | `gate_runner.py` scope exceeded prompt ("loader only") with helpers + validation — all reasonable |

---

## Commit hygiene

**Include in this commit** (live-gate bundle):

- `bin/gate-live`
- `tests/live/gate_runner.py`
- `tests/live/networks.yaml`
- `tests/test_live_gate_runner_unit.py`
- `docs/manual-checks/2026-06-20-live-gate-program.md`
- `prompts/cursor/done/2026-06-20-1995-baseball-fresh-derive-default-on/`

**Still unstaged** (separate — crm-metering gate catalog fix):

- `tests/live/catalogs/crm_metering.yaml`
- `examples/networks/crm-metering/README.md`
- `examples/networks/empty-crm/README.md`

---

## For Paul

- **Commit message:** `feat(gate-live): default fresh-derive for baseball derive phase`
- **Operator UX:** `./bin/gate-live baseball` no longer needs `--fresh-derive`
- **Push:** local only until you ask
- **Remaining unstaged:** crm-metering catalog/README — commit separately when ready