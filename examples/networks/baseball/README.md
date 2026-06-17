# Baseball example (work in progress)

> **WIP (June 2026)** — Bootstrap and warehouse ingest are usable; **query orchestration, derivatives, and performance are not production-ready.** Lahman refresh can take a long time on the identity-bind pass alone; load optimization is ongoing ([`docs/manual-checks/2026-06-17-storage-evolution-timing-gates.md`](../../../docs/manual-checks/2026-06-17-storage-evolution-timing-gates.md)). Do not treat this example as a finished demo until [`docs/plans/baseball-example-program.md`](../../../docs/plans/baseball-example-program.md) checklist advances.

Lahman second-network example. **Not** wired into `mycelium query` yet.

## Quick start

From the framework repo root:

```bash
uv sync
./bin/refresh-example-network baseball --yes
```

Refresh copies `network.json`, `bootstrap_handlers/`, and `guide.md`, then:

1. **Fetches** Lahman CSVs from [`myceliumdata/lahman-seed`](https://github.com/myceliumdata/lahman-seed) (`seed.source.json` pins tag `v2025.1`)
2. **Bootstraps** via `LahmanSeedHandler`: warehouse ingest + team/player entity grains

Default live root: `~/mycelium-networks/baseball` (registered in `networks.json`).

Long Lahman bootstraps print **phase progress on stderr** (`Retrieving data…`, `Processing records (x/y)…`, `Cleaning up…`). Set `MYCELIUM_BOOTSTRAP_PROGRESS=0` to silence; progress defaults to on when stderr is a TTY.

## Bootstrap (pack handler)

`network.json` declares the Lahman pack handler:

```json
"bootstrap": {
  "module": "bootstrap_handlers.lahman_seed",
  "handler": "LahmanSeedHandler"
}
```

Remote seed manifest (`seed.source.json`):

```json
{
  "type": "git",
  "repo": "https://github.com/myceliumdata/lahman-seed.git",
  "ref": "v2025.1",
  "source_path": "lahman_1871-2025_csv",
  "dest": "seed/lahman_1871-2025_csv"
}
```

After fetch, bootstrap:

1. Ingests CSVs → `<network_root>/warehouse/lahman.sqlite`
2. Commits distinct `Teams.name` labels → `entities/team.json` (`bind_fields: ["team"]`)
3. Commits player rows from Appearances (one uuid per Lahman `playerID`, multiple bind keys for multi-team aliases) → `entities/player.json` (`bind_fields: ["player", "team"]`)

Each committed row stores Lahman IDs in **`source_keys`** (`lahman.playerID`, `lahman.teamID`, optional `lahman.franchID`) for warehouse joins; public entity `id` stays uuid4.

- **Bind aliases** (`add_bind_alias`) — bootstrap-time alternate full player `(player, team)` tuples for one `playerID` (multi-team careers).
- **Field aliases** (`add_field_alias`) — field-index nicknames on one bind field; multiple entities may share one alias (`"Dodgers"` → Brooklyn + LA). Bootstrap may seed some; **closed-grain query-time** expansion (`bind_alias_expansion`) can add more lazily without changing canonical bind values.

The baseball example copies CRM sample `categories.json` until a baseball ontology exists. Bind field `team` maps to the `professional` category (same as CRM `employer`).

**Attribution:** Lahman data is copyright SABR / Sean Lahman (CC BY-SA 3.0). See the [lahman-seed](https://github.com/myceliumdata/lahman-seed) repository.

## Bootstrap experiment (v0 — legacy spike)

Standalone script, **not** the formal bootstrap path. Disposition unchanged.

Heuristic mode (no API key) — distinct season team labels → auto-committed `team_registry.json`:

```bash
uv run python examples/networks/baseball/bootstrap_experiment.py --no-llm
```

LLM mode — identity specialist proposes canon + aliases from schema sample + `guide.md`:

```bash
export OPENAI_API_KEY=...
uv run python examples/networks/baseball/bootstrap_experiment.py --llm
```

**Outputs** under `~/mycelium-networks/baseball/`:

| Path | Content |
|------|---------|
| `warehouse/lahman.sqlite` | Ingested People, Teams, Appearances, Batting, Pitching, TeamsFranchises |
| `bootstrap/team_registry.json` | Auto-committed team entities (uuid4), alias index, proposal |
| `bootstrap/bootstrap_report.json` | Run summary |

Design: [`docs/plans/baseball-example-program.md`](../../../docs/plans/baseball-example-program.md).