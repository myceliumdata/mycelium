# Baseball example (experimental)

Lahman second-network bootstrap experiment. **Not** wired into `mycelium query` yet.

## Prerequisites

- Lahman 2025 CSV zip at `~/mycelium-networks/baseball/seed/lahman_1871-2025_csv.zip` (or extracted folder)
- `uv sync` at repo root

## Bootstrap experiment (v0)

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