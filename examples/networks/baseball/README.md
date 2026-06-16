# Baseball example (experimental)

Lahman second-network example. **Not** wired into `mycelium query` yet.

## Bootstrap (pack handler)

`network.json` declares the Lahman pack handler:

```json
"bootstrap": {
  "module": "bootstrap_handlers.lahman_seed",
  "handler": "LahmanSeedHandler"
}
```

**Seed layout** (not committed to git): place Lahman CSVs under `<network_root>/seed/` as one of:

- `lahman_1871-2025_csv.zip` (extracted idempotently to `seed/lahman_1871-2025_csv/`)
- extracted folder `seed/lahman_1871-2025_csv/`
- flat `seed/*.csv`

`refresh-example-network baseball` copies `bootstrap_handlers/` from this example.

When seed data is present, bootstrap:

1. Ingests CSVs → `<network_root>/warehouse/lahman.sqlite`
2. Commits distinct `Teams.name` labels → `entities/team.json` (`bind_fields: ["name"]`)
3. Commits player rows from Appearances (one uuid per Lahman `playerID`, multiple bind keys for multi-team aliases) → `entities/player.json`

The baseball example copies CRM sample `categories.json` until a baseball ontology exists. Bind field `team` maps to the `professional` category (same as CRM `employer`).

No seed → **0** entities (`handler_id: lahman_seed`).

## Prerequisites (standalone experiment)

- Lahman 2025 CSV zip at `~/mycelium-networks/baseball/seed/lahman_1871-2025_csv.zip` (or extracted folder)
- `uv sync` at repo root

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
