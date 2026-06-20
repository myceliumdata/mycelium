# Live gate program output — unified `gate-live`

## Done

| Item | Path |
|------|------|
| Operator script | `bin/gate-live` |
| Network registry | `tests/live/networks.yaml` |
| Framework | `tests/live/gate_runner.py`, `conftest.py`, `assertions.py` |
| Catalogs | `tests/live/catalogs/{baseball,crm,crm_metering,empty_crm}.yaml` |
| Anchors | `tests/live/anchors/baseball_aaron_lahman_v2025.json`, `crm_seed_v1.json` |
| Tests | `tests/live/test_live_gate.py` |
| Unit tests | `tests/test_live_gate_runner_unit.py` (smoke) |
| Docs | `docs/manual-checks/2026-06-20-live-gate-program.md` |
| Gitignore | `docs/manual-checks/runs/` |

## Scenario counts

| Network | Scenarios |
|---------|-----------|
| baseball | 16 |
| crm | 7 |
| crm-metering | 4 |
| empty-crm | 5 |
| **Total** | **32** |

## `--list` sample

```text
Live gate networks (./bin/gate-live <network>):
  baseball
    default_root: ~/mycelium-networks/baseball
    phases: preflight, identity, m2, derive, infra
  crm
    default_root: ~/mycelium-networks/crm
    phases: preflight, protocol, research, negative
  crm-metering
    default_root: ~/mycelium-networks/crm-metering
    phases: preflight, metering
  empty-crm
    default_root: ~/mycelium-networks/empty-crm
    phases: preflight, growth
```

## Verification

```text
./bin/ci-local                              # 590 smoke passed (includes 8 unit tests)
uv run pytest tests/test_live_gate_runner_unit.py -q   # 8 passed
uv run pytest tests/live/test_live_gate.py -m live_gate --collect-only -q  # 1 collected (parametrize; needs LIVE_GATE_NETWORK)
```

`live_gate` marker is **not** in `ci-local` smoke selection.

## Operator (Paul)

```bash
./bin/gate-live --list
./bin/gate-live crm --phase protocol
./bin/gate-live crm-metering --phase metering
./bin/gate-live empty-crm --phase growth    # refresh empty root first
./bin/gate-live baseball --phase m2
./bin/gate-live baseball --phase derive --fresh-derive
```

## For Grok + Paul

- Live gate v1 shipped; mark TODO slice done.
- Added `pyyaml` dependency for catalog loading.
- empty-crm growth mutates root — document refresh before re-run (in operator doc).

## Suggested commit message

```
tests: unified gate-live regression for example networks (opt-in)
```
