# Baseball cold start — bootstrap and open problems

**Date:** 2026-06-16  
**Participants:** Paul + Grok/Cursor  
**Status:** Design exploration  
**Related:** [`baseball-example-program.md`](../baseball-example-program.md)

---

## Cold start (Paul’s framing)

Unlike CRM (small seed → research extended attrs), baseball bootstrap:

1. Create **two MVRs** (player + team) and associated **registries**
2. Create **ontology** — same mechanism as CRM (`network create` / creation prompt → categories + specialists)
3. **Point orchestrator at data source** (Lahman zip/URL + docs)
4. Tell it to **“sort yourself out”** — ingest, discover table roles, route to specialists, organize storage

**Empirical question:** orchestrator sees pitching stats → which specialist? That specialist → what storage/derivation strategy?

**Deferred:** JSON `storage.json` at Lahman volume — unwieldy; warehouse (SQLite/DuckDB) is the bulk path; address JSON limits separately.

---

## How this differs from CRM bootstrap

| CRM | Baseball |
|-----|----------|
| `seed.json` `people[]` → `entities.json` | Lahman zip → **warehouse** + agent ingest |
| Specialists research **web** attrs | Specialists **own tabular domains** + derivations |
| Single MVR | Two MVRs / two registries |
| Ontology from creation prompt | Same prompt mechanism; tables may **reshape** ontology after ingest |
| `refresh-example-network` copies seed | Need **data-source handoff** story (URL, ingest specialist) |

---

## Other problems on the board

1. **Framework:** multi-MVR, multi-registry, multi-alias player bind index in one network
2. **Ingest protocol:** what “point at source” means in API/CLI/admin
3. **Supervisor:** grain (player vs team) + operation (read / join / derive) + multi-specialist merge
4. **Scope:** year/season/stint not identity — query step 2
5. **LLM aliases:** `Yanks`, `465` — see [`2026-06-16-llm-alias-resolution.md`](2026-06-16-llm-alias-resolution.md)
6. **Provenance + retention:** agent decides cache vs one-shot (later)
7. **Schema pass:** unzip Lahman; complete ER diagram
8. **Hosting:** 40MB zip not in git; Box not bot-fetchable
9. **Cold start v0:** likely **hybrid** — scripted warehouse load first, agent autonomy for ontology/specialist behavior second

---

*Archived June 2026.*