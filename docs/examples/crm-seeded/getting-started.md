# CRM (seeded) — getting started

15-person seed; single **`person`** record type; `query_allowed` growth. Shared setup: [../getting-started.md](../getting-started.md).

**Exploration walkthroughs:** [explore/README.md](explore/README.md)

---

## Bootstrap

```bash
./bin/refresh-example-network crm-seeded --yes
```

Default root: `~/mycelium-networks/crm-seeded`.

Before demos: refresh wipes stale specialist research — **restart MCP** afterward.

---

## `.env` keys

| Feature | Variables |
|---------|-----------|
| Synchronous research (`email`, …) | `OPENAI_API_KEY` + active search provider key |
| Fuzzy bind suggestions | None (framework) |
| Lazy alias expansion | `OPENAI_API_KEY` (on `bootstrap_only` networks; CRM uses fuzzy first) |

---

## First queries

```bash
uv run mycelium query --network crm-seeded \
  --lookup-json '{"name":"Nichanan Kesonpat","employer":"1k(x)"}'
uv run mycelium query --network crm-seeded --delivery-id d_…
```

---

## MCP

```json
"env": { "MYCELIUM_NETWORK": "crm-seeded" }
```

Fixtures: [`examples/networks/crm-seeded/queries/`](../../../examples/networks/crm-seeded/queries/).

---

## Regression

| Gate | Command |
|------|---------|
| Fast E2E | `./bin/smoke-crm-seeded-e2e` |
| Live gate (7 scenarios) | `./bin/gate-live crm-seeded` |

---

## References

- [`examples/networks/crm-seeded/README.md`](../../../examples/networks/crm-seeded/README.md)