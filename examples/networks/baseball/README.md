# Baseball example (work in progress)

> **WIP (June 2026)** — Query path, warehouse stats, and derive pipeline ship on live Lahman; **bootstrap refresh timing** is still too slow for casual demo scale. Load optimization is ongoing ([`docs/manual-checks/2026-06-17-storage-evolution-timing-gates.md`](../../../docs/manual-checks/2026-06-17-storage-evolution-timing-gates.md)). Program status: [`docs/plans/baseball-example-program.md`](../../../docs/plans/baseball-example-program.md).

Lahman second-network example: **player** + **team** record types, warehouse specialists, and LLM derive on manifest miss.

## Quick start

From the framework repo root:

```bash
uv sync
./bin/refresh-example-network baseball --yes

# Step 1 — partial player lookup (copy delivery_id)
uv run mycelium query --network baseball \
  --lookup-json '{"player":"Hank Aaron"}'

# Step 2 — identity deliver
uv run mycelium query --network baseball --delivery-id d_…

# Step 1 — warehouse stat + provenance
uv run mycelium query --network baseball \
  --lookup-json '{"player":"Hank Aaron"}' \
  --requested-attributes career_hr --provenance
```

**Fast CI gate** (minimal fixture, mocked derive): `./bin/smoke-baseball-e2e`

**Live regression** (real `~/mycelium-networks/baseball`): `./bin/gate-live baseball` — derive cache auto-clears; full Lahman reload is manual before gate.

To push committed example changes (e.g. updated `guide.md`) into an **existing** live root without re-running Lahman bootstrap (~25 min):

```bash
./bin/refresh-example-network baseball --sync-only
```

Keeps `entities/`, `warehouse/`, `seed/`, specialists, and checkpoints; copies `guide.md`, `network.json`, `bootstrap_handlers/`, etc. from `examples/networks/baseball/`.

Refresh copies `network.json`, `bootstrap_handlers/`, and `guide.md`, then:

1. **Fetches** Lahman CSVs from [`myceliumdata/lahman-seed`](https://github.com/myceliumdata/lahman-seed) (`seed.source.json` pins tag `v2025.1`)
2. **Bootstraps** via `LahmanSeedHandler`: warehouse ingest + team/player record types

Default live root: `~/mycelium-networks/baseball` (registered in `networks.json`).

See [`docs/manual-checks/2026-06-20-live-gate-program.md`](../../../docs/manual-checks/2026-06-20-live-gate-program.md).

MCP: `describe_network` at connect; `health_check` uses `health_ping.lookup` in `network.json` (`{"player":"Hank Aaron"}`) after bootstrap.

## Step-1 lookup (operators)

Identity resolve uses the **framework** fuzzy matcher (same as CRM), then baseball-specific **lazy LLM aliases** on `bootstrap_only` team/player types. See [`docs/plans/fuzzy-lookup-policy.md`](../../../docs/plans/fuzzy-lookup-policy.md) § For operators.

| You typed | Typical outcome |
|-----------|-----------------|
| Typo (`Tie Cobb`) | `lookup_suggested` → retry with `Ty Cobb` |
| Exact (`Ty Cobb`, `Boston Red Sox`) | `lookup_resolved` |
| Prefix that matches first token of canonical name | `lookup_suggested` (if applicable) |
| Nickname (`Dodgers`, `Bronx Bombers`) — needs `OPENAI_API_KEY` on first hit | `lookup_resolved` (may multi-match); writes `field_aliases` |
| Mashup / unknown (`Washington Red Sox`, `XYZZY`) | `not_found` |

Nicknames are defined in [`guide.md`](guide.md) for the LLM; fuzzy handles typos only. No query-time entity creation.

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
3. Commits one player row per Lahman `playerID` with debut bind → `entities/player.json` (`bind_fields: ["player", "debut_team", "debut_year"]`)

Each committed row stores Lahman IDs in **`source_keys`** (`lahman.playerID`, `lahman.teamID`, optional `lahman.franchID`) for warehouse joins; public entity `id` stays uuid4.

- **Field aliases** (`add_field_alias`) — field-index nicknames on one bind field; multiple entities may share one alias (`"Dodgers"` → Brooklyn + LA). Bootstrap may seed some; **bootstrap-only query-time** expansion (`bind_alias_expansion`) can add more lazily without changing canonical bind values.

**Re-bootstrap required** after slice 1800 — old `player`+`team` entity stores are incompatible with debut bind shape.

## Committed ontology (M1a)

Refresh installs `examples/networks/baseball/categories.json` into the live root (`ontology_pack: baseball`). Bind fields and Lahman-shaped attributes route to baseball specialists — not CRM `professional_specialist`.

| Category | Specialist | Examples |
|----------|------------|----------|
| `player_identity` | `player_identity_specialist` | `player`, `debut_team`, `debut_year` |
| `team_identity` | `team_identity_specialist` | `team` |
| `bio` | `bio_specialist` | `birth_date`, `height`, `bats`, … |
| `batting` | `batting_specialist` | `career_hr`, `home_runs`, `rbi`, … |
| `pitching` | `pitching_specialist` | `career_wins`, `era`, `strikeouts`, … |
| `team_season` | `team_season_specialist` | `season_wins`, `park`, `attendance`, … |

**M1b (`career_hr`):** `batting_specialist` reads the Lahman warehouse on deliver and caches results with computation-centric provenance (`sources`, `computation.inline`, `parameters`). Other specialists remain stubs until follow-up slices.

```json
{
  "lookup": {
    "player": "Hank Aaron",
    "debut_team": "Brooklyn Dodgers",
    "debut_year": "1957"
  },
  "requested_attributes": ["career_hr"],
  "provenance": true
}
```

Then deliver with `delivery_id` from the step-1 response. See [`docs/plans/conversations/2026-06-18-computation-centric-provenance.md`](../../../docs/plans/conversations/2026-06-18-computation-centric-provenance.md).

**M1c (`birth_date`):** `bio_specialist` reads raw `People` birth columns on deliver (same provenance envelope). Example:

```json
{
  "lookup": {
    "player": "Hank Aaron",
    "debut_team": "Brooklyn Dodgers",
    "debut_year": "1957"
  },
  "requested_attributes": ["birth_date"],
  "provenance": true
}
```

See `queries/04-birth-date.json`.

## Hand testing

Operator gate and **warehouse pull vs compute** reference (what works now vs M2b vs later):

[`docs/manual-checks/2026-06-19-baseball-specialist-hand-test.md`](../../../docs/manual-checks/2026-06-19-baseball-specialist-hand-test.md#warehouse-pull-vs-compute--reference)

## Warehouse manifest (M2a)

After bootstrap or `--sync-only` refresh when `warehouse/lahman.sqlite` exists, the framework writes **`warehouse_manifest.json`** at the network root. It merges pack domain rules (`examples/networks/baseball/warehouse_domains.json`) with sqlite introspection (columns + row counts per domain table). **`describe_network`** includes a `warehouse_manifest` summary (dataset id, domains, tables); read the full file on disk for grains and conventions. Operators should not hand-edit the manifest — re-run bootstrap or sync to regenerate.

Existing live roots: run `./bin/refresh-example-network baseball --sync-only` to pick up ontology without re-running Lahman bootstrap.

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