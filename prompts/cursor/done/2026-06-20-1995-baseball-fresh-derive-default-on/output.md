# Baseball fresh-derive default — output

## Done

| Item | Change |
|------|--------|
| Registry | `fresh_derive_before_gate: true` on `baseball` in `tests/live/networks.yaml` |
| `gate_runner.py` | `NetworkEntry.fresh_derive_before_gate`, `should_fresh_derive()`, `derive_phase_in_scope()`, `derive_cache_files_exist()` |
| `bin/gate-live` | Default clear before derive phase; `--no-fresh-derive` opt-out; stderr hints + stale-cache warning |
| `--list` | Shows `fresh_derive_before_gate: yes|no` per network |
| `LIVE_GATE_FRESH_DERIVE` | Set when auto or explicit fresh-derive runs |
| Docs | Quick start + Baseball section updated |

## Behavior

| Command | Clears derive cache? |
|---------|----------------------|
| `./bin/gate-live baseball` (all phases) | **Yes** (derive in scope) |
| `./bin/gate-live baseball --phase derive` | **Yes** |
| `./bin/gate-live baseball --phase m2` | **No** |
| `./bin/gate-live baseball --phase derive --no-fresh-derive` | **No** (+ warning if cache exists) |
| `./bin/gate-live crm` | **No** |

## Verification

```text
./bin/ci-local                              # 611 smoke passed
uv run pytest tests/test_live_gate_runner_unit.py -q  # 16 passed
./bin/gate-live --list                      # baseball fresh_derive_before_gate: yes
```

## For Grok + Paul

- Operators no longer need `--fresh-derive` for routine baseball derive gates.
- `--fresh-derive` kept as force-on override; `--no-fresh-derive` for cache-hit experiments.
- `prompts/cursor/next/` empty after this slice.

## Suggested commit message

```
feat(gate-live): default fresh-derive for baseball derive phase
```
