# Documentation examples

Illustrative JSON samples for Mycelium runtime artifacts. These files are **committed for reference only** — they are not copied into a `network_root` and are not loaded by the framework at startup.

## `sample-categories.json`

Shows the typical shape of **`<network_root>/categories.json`** after the classification engine seeds its cache (from embedded `_SEED_CATEGORIES` in `src/agents/classification/engine.py`).

| Property | Notes |
|----------|-------|
| `categories` | Six default domains (contact, social, relationships, demographic, professional, financial) |
| `attribute_map` | Known attribute → category lookups |
| `last_updated` | Fixed in this sample; runtime file updates on classification changes |

**Runtime policy:** `categories.json` lives under your active `network_root`, is **gitignored**, and is created on first classification use. It is **not** shipped in `examples/networks/crm/` and is **not** copied by `bin/refresh-example-network`.

See also: [architecture.md](../architecture.md) (classification + network layout).
