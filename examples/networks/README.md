# Example networks

Committed reference networks under `examples/networks/`. Each ships `network.json`, `guide.md`, and bootstrap assets; runtime state (`entities/`, `warehouse/`, `agents/`, checkpoints) lives under your live root after refresh.

**Runnable operator docs** (shared `.env`, two-step protocol, feature walkthroughs): [`docs/examples/`](../../docs/examples/README.md).

| Network | When to use | Bootstrap | Query model |
|---------|-------------|-----------|-------------|
| [`crm/`](crm/) | Default demo; 15-person seed; growth + fuzzy lookup | `seed.json` → `DefaultSeedHandler` | Single record type `person`; `query_allowed` |
| [`empty-crm/`](empty-crm/) | Growth-from-zero; no seed rows | Handler runs; 0 entities | Same MVR as CRM; first row on step-2 deliver |
| [`crm-metering/`](crm-metering/) | Quote / metering negotiation demos | Same seed shape as CRM | `metering.enabled: true`; payment mock |
| [`baseball/`](baseball/) | Lahman warehouse + multi-record-type (player + team) | `LahmanSeedHandler` + git seed | `bootstrap_only`; warehouse stats + derive |

## Refresh and query

```bash
./bin/refresh-example-network <name> --yes
uv run mycelium query --network <name> --lookup-json '{...}'
```

Default live roots: `~/mycelium-networks/<name>` (see `networks.json` after register).

**Pack-only sync** (no re-bootstrap): `./bin/refresh-example-network <name> --sync-only` — copies committed `guide.md`, `network.json`, `bootstrap_handlers/`, ontology pack, etc.

## Regression gates

| Gate | Scope |
|------|--------|
| `./bin/smoke-crm-e2e` | CRM fixture refresh + inline scenarios + pytest smoke |
| `./bin/smoke-baseball-e2e` | Minimal Lahman fixture; player + team queries; mocked derive |
| `./bin/gate-live <name>` | Real `~/mycelium-networks/<name>` + `.env`; never CI |

Live gate program: [`docs/manual-checks/2026-06-20-live-gate-program.md`](../../docs/manual-checks/2026-06-20-live-gate-program.md).

## MCP `health_check`

Each example may declare `health_ping.lookup` in `network.json` — bind-field keys for a known row used by MCP `health_check` step-1 + step-2 ping. Networks without a ping (empty CRM before growth) report `ping_query: skipped`.

## README checklist (operators)

**Prefer [`docs/examples/<network>/`](../../docs/examples/README.md)** for getting started and exploration walkthroughs (CLI, MCP, expected output). Pack READMEs here cover maintainer layout, bootstrap internals, and `guide.md` editing.