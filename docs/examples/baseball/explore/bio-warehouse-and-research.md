# Bio — warehouse pull and research on miss

## What this demonstrates

**Hybrid bio domain:** manifest aliases read Lahman `People` / `HallOfFame` tables; unaliased labels with `research_on_miss: true` invoke **synchronous web research** via `WarehouseResearchStatSpecialist`.

## Prerequisites

```bash
OPENAI_API_KEY=…
SEARCH_PROVIDER=tavily   # or exa / brave
TAVILY_API_KEY=…         # or EXA_API_KEY / BRAVE_SEARCH_API_KEY
```

Bootstrapped baseball root. First research hit may take **tens of seconds**.

## How to test — CLI

```bash
# Warehouse pull — height (manifest)
uv run mycelium query --network baseball \
  --lookup-json '{"player":"Hank Aaron"}' \
  --requested-attributes height

# Warehouse compute — HOF election year (manifest recipe)
uv run mycelium query --network baseball \
  --lookup-json '{"player":"Hank Aaron"}' \
  --requested-attributes hall_of_fame_year

# Research on miss — primary nickname (web search)
uv run mycelium query --network baseball \
  --lookup-json '{"player":"Hank Aaron"}' \
  --requested-attributes primary_nickname
```

Step 2 after each step 1. Use a **fresh `thread_id`** on MCP for first research demo.

## How to test — MCP

```json
{
  "lookup": { "player": "Hank Aaron" },
  "requested_attributes": ["primary_nickname"],
  "thread_id": "bio-demo-1"
}
```

## Expected output

| Attribute | Source | Approximate value |
|-----------|--------|-------------------|
| `height` | Warehouse | **72** (inches) |
| `hall_of_fame_year` | Warehouse (HOF inducted=Y) | **1982** |
| `primary_nickname` | Research | **Hammer** or **Hammerin' Hank** (provider-dependent) |

`outcome`: `assembled` on step 2. Research attrs include web provenance in `versions[]`.

## Learn more

- [2026-06-21-baseball-bio-research-specialist.md](../../../plans/conversations/2026-06-21-baseball-bio-research-specialist.md)
- [specialist-research-phase1.md](../../../plans/specialist-research-phase1.md)
- Live gate: `bb-bio-01`, `bb-bio-03`, `bb-bio-research-01`