# Baseball example — getting started

Lahman warehouse + **player** and **team** record types. Shared clone/setup: [../getting-started.md](../getting-started.md).

**Exploration walkthroughs:** [explore/README.md](explore/README.md)

---

## Bootstrap

```bash
./bin/refresh-example-network baseball --yes
```

- Default root: `~/mycelium-networks/baseball`
- Full bootstrap: **~3–4 min** (27-table warehouse ingest + registries)
- Pack-only update: `./bin/refresh-example-network baseball --sync-only`

Seed source: [`myceliumdata/lahman-seed`](https://github.com/myceliumdata/lahman-seed) tag `v2025.1` (see `seed.source.json` in the example pack).

---

## `.env` keys (beyond shared framework)

| Feature | Variables |
|---------|-----------|
| Lazy nickname aliases (`Dodgers`, …) | `OPENAI_API_KEY` |
| Batting / pitching / fielding **derive** | `OPENAI_API_KEY`, `MYCELIUM_COMPUTATION_CODEGEN_MODEL` |
| Intent synonym dedup (M4b) | `MYCELIUM_INTENT_NORMALIZATION_MODEL` |
| Bio **research** on miss (`primary_nickname`) | `OPENAI_API_KEY` + active search provider key |

Search provider: `SEARCH_PROVIDER=tavily|exa|brave` with matching key ([`.env.example`](../../../.env.example)).

Admin UI (`./bin/restart-admin baseball`): use the **Record type** selector in Run query — **player** (player / debut team / debut year) or **team** (team name).

---

## First queries

```bash
# Player identity (step 1 → step 2)
uv run mycelium query --network baseball \
  --lookup-json '{"player":"Hank Aaron"}'
uv run mycelium query --network baseball --delivery-id d_…

# Warehouse stat + provenance (often one step 1 with attrs, then step 2)
uv run mycelium query --network baseball \
  --lookup-json '{"player":"Hank Aaron"}' \
  --requested-attributes career_hr --provenance
uv run mycelium query --network baseball --delivery-id d_…
```

---

## MCP

```json
"env": { "MYCELIUM_NETWORK": "baseball" }
```

`health_check` pings `{"player":"Hank Aaron"}` after bootstrap (`health_ping` in `network.json`).

Restart MCP after refresh. Lahman bootstrap is long — wait for refresh to finish before querying.

---

## Fast paths (no full Lahman)

| Goal | Command |
|------|---------|
| CI smoke (minimal fixture, mocked derive) | `./bin/smoke-baseball-e2e` |
| Live regression (**34** scenarios) | `./bin/gate-live baseball` |

Gate auto-refreshes the live root before scenarios. See [live gate program](../../manual-checks/2026-06-20-live-gate-program.md).

---

## References

- Pack README: [`examples/networks/baseball/README.md`](../../../examples/networks/baseball/README.md)
- Program design: [`docs/plans/baseball-example-program.md`](../../plans/baseball-example-program.md)
- v1 sign-off: [`docs/manual-checks/2026-06-21-baseball-program-post-program-gate.md`](../../manual-checks/2026-06-21-baseball-program-post-program-gate.md)