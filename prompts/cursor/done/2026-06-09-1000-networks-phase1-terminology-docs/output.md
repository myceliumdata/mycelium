# networks-phase1-terminology-docs — Output

## Claim

Moved `prompts/cursor/next/2026-06-07-1000-networks-phase1-terminology-docs.md` → `prompts/cursor/in-progress/2026-06-09-1000-networks-phase1-terminology-docs/prompt.md`.

## Summary

Doc-only slice: documented the **networks product model** before runtime changes. No `src/` logic beyond one-line classification seed copy.

### Files updated

| File | Changes |
|------|---------|
| `docs/architecture.md` | Overview disambiguation; new **Networks** section (framework vs network root, selection order, MCP-per-network, terminology link, `prototype` tag) |
| `README.md` | Framework-first intro; transitional `data/`; `examples/networks/crm/` forthcoming; parallel MCP JSON example; `prototype` tag |
| `docs/plans/networks-terminology.md` | Status + Phase 1 done; resolved open question #5 |
| `docs/full-code-walkthrough.md` | One roadmap paragraph |
| `src/agents/classification/engine.py` | `_SEED_CATEGORIES` social description: “profiles” not “network profiles” |

## Grep audit

README contains: `framework`, `network root` (via `MYCELIUM_NETWORK_ROOT`), `default network`, MCP-per-network parallel example.

`docs/architecture.md` contains: `Networks` section with `network_root`, `framework`, `default network`, MCP-per-network.

## Verification

No tests required (docs only).

## Next slice

`2026-06-07-1100-networks-phase2-path-resolver.md` — network path resolver + CLI/MCP wiring.
