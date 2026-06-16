# Network bootstrap specialist — CRM seed path

## Summary

Introduced a formal **network bootstrap phase** under `src/network/bootstrap/`. CRM seed import behavior is unchanged; all orchestration now flows through `run_network_bootstrap(paths)`.

## Package layout

| Module | Role |
|--------|------|
| `bootstrap/run.py` | `run_network_bootstrap` — paths, MVR categories, registry reset, handler invoke |
| `bootstrap/context.py` | `BootstrapContext`, `BootstrapResult` |
| `bootstrap/handlers/default_seed.py` | CRM `seed.json` import (`load_seed_people`, `import_seed_rows`, `DefaultSeedHandler`) |
| `bootstrap/handlers/resolve.py` | Default vs `<network_root>/specialists/bootstrap_specialist.py` override |
| `network/seed_import.py` | Thin wrappers preserving stable public API |

## Call chain

```
create / refresh / test helpers
  → bootstrap_seed_at_paths(paths)
  → run_network_bootstrap(paths) → BootstrapResult
  → resolve_handler → default_seed | override
```

Override hook: `specialists/bootstrap_specialist.py` with `run_bootstrap(ctx: BootstrapContext) -> BootstrapResult`.

## Tests

New `tests/test_network_bootstrap.py` (8 smoke tests): CRM 15 entities, missing seed, invalid JSON, missing employer, idempotency, override hook, delegation.

## Docs

- `docs/architecture.md` § Seed bootstrap updated
- `examples/networks/crm/README.md` — one-line cross-ref to `network.bootstrap`

## Verification

```bash
./bin/ci-local
# CI local: all steps passed.
# 413 passed, 92 deselected
```

Program 2 bootstrap matrix and example network capstones unchanged.

## For Grok + Paul

- **Baseball slice next:** extend `network/bootstrap/handlers/` with a warehouse handler implementing the same `BootstrapHandler` contract — do not scatter logic in refresh/create.
- Update `docs/plans/baseball-example-program.md` slice map to reference bootstrap module (Grok doc pass after approval).
- Suggested commit:

```
feat(network): formal bootstrap phase with CRM default seed handler

Introduce run_network_bootstrap() and relocate seed import into
src/network/bootstrap/. bootstrap_seed_at_paths delegates to the new
entry point; optional network override hook for future baseball cold start.
```

- Do **not** commit from this slice deliverable.
