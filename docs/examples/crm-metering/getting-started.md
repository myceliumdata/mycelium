# CRM metering — getting started

CRM seed + **metering.enabled** — quote before researched deliver. Shared setup: [../getting-started.md](../getting-started.md).

**Walkthrough:** [explore/quote-and-deliver.md](explore/quote-and-deliver.md)

---

## Bootstrap

```bash
./bin/refresh-example-network crm-metering --yes
```

Root: `~/mycelium-networks/crm-metering`.

---

## `.env` keys

`OPENAI_API_KEY` + active search provider key (email research on deliver).

---

## MCP fixtures

[`examples/networks/crm-metering/queries/`](../../../examples/networks/crm-metering/queries/)

---

## Live gate

`./bin/gate-live crm-metering` — 4 scenarios.