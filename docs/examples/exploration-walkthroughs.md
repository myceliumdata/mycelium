# Exploration walkthroughs

**Exploration walkthroughs** are short, feature-focused guides: run one query path end-to-end and see what framework capability it demonstrates.

Each walkthrough lives under `docs/examples/<network>/explore/` and follows the same shape:

| Section | Purpose |
|---------|---------|
| **What this demonstrates** | One feature (framework or network-specific) |
| **Prerequisites** | Refresh command, `.env` keys, prior steps |
| **How to test — CLI** | Copy-paste `uv run mycelium query …` |
| **How to test — MCP** | JSON for `query_entity` (same fields as CLI) |
| **Expected output** | `outcome`, key fields, approximate values |
| **Learn more** | Architecture, design conversations, live gate scenarios |

Walkthroughs are **ordered by feature**, not by tutorial difficulty. Start with [getting-started.md](getting-started.md) for shared setup, then pick features from each network's [explore/README.md](README.md) index.

**Not a substitute for live gate** — `./bin/gate-live <network>` runs automated regression on a deployed root. Walkthroughs are for human exploration and onboarding.