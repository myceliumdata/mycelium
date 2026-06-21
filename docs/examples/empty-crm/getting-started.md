# Empty CRM — getting started

Same CRM MVR as [`crm`](../crm/getting-started.md) but **no seed rows** — registry starts empty. Shared setup: [../getting-started.md](../getting-started.md).

**Walkthrough:** [explore/growth-from-zero.md](explore/growth-from-zero.md)

---

## Bootstrap

```bash
./bin/refresh-example-network empty-crm --yes
```

Root: `~/mycelium-networks/empty-crm`. Entity count **0** after refresh.

---

## `.env` keys

Same as CRM when requesting researched attributes (`OPENAI_API_KEY` + search provider key).

---

## Live gate

`./bin/gate-live empty-crm` — 5 scenarios; auto-refresh wipes root each run.