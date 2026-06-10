# CRM metering demo

Same investor CRM seed as the **`crm`** example, but **`metering.enabled: true`** so attribute research requires a priced commit (`quote_required` → `quote_id`).

Use this network to exercise negotiation on CLI, MCP, or admin UI. Payment settlement is **disabled** — retry with `quote_id` after a quote; no `pay_quote` step.

Paul Murphy @ Acme Corp + `email` is the canonical demo arc (see `README.md` and `bin/demo-metering-negotiation`).
