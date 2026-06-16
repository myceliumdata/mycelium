# Baseball example (experimental)

Lahman second-network example. **Not** wired into `mycelium query` yet.

## Bootstrap (framework)

`network.json` declares the same framework handler as CRM until a Lahman pack handler ships:

```json
"bootstrap": {
  "module": "network.bootstrap.handlers.default_seed",
  "handler": "DefaultSeedHandler"
}
```

There is no `seed.json` in this example today, so refresh runs the handler but imports **0** registry rows. The long-term path is a **network-pack handler** under `bootstrap_handlers/` (e.g. `LahmanSeedHandler`) declared in `network.json` with `"module": "bootstrap_handlers.lahman_seed"`. See [`docs/architecture.md`](../../../docs/architecture.md) § Seed bootstrap.

`refresh-example-network baseball` copies `bootstrap_handlers/` from this example when present (directory not shipped yet).

## Prerequisites (standalone experiment)

- Lahman 2025 CSV zip at `~/mycelium-networks/baseball/seed/lahman_1871-2025_csv.zip` (or extracted folder)
- `uv sync` at repo root

## Bootstrap experiment (v0 — legacy spike)

Standalone script, **not** the formal bootstrap path. Disposition TBD.

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