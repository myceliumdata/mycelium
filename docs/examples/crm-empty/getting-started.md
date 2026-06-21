# Empty CRM — getting started

Same CRM MVR as [`crm-seeded`](../crm-seeded/getting-started.md) but **no seed rows** — registry starts empty. Shared setup: [../getting-started.md](../getting-started.md).

**Walkthrough:** [explore/growth-from-zero.md](explore/growth-from-zero.md)

---

## Bootstrap

```bash
./bin/refresh-example-network crm-empty --yes
```

Root: `~/mycelium-networks/crm-empty`. Entity count **0** after refresh.

---

## `.env` keys

Same as CRM when requesting researched attributes (`OPENAI_API_KEY` + search provider key).

---

## Live gate

`./bin/gate-live crm-empty` — 5 scenarios; auto-refresh wipes root each run.