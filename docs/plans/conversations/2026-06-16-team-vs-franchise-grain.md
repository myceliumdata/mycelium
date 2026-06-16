# Team grain vs franchise — emergent organization

**Date:** 2026-06-16  
**Participants:** Paul + Grok/Cursor  
**Status:** Direction change — supersedes “team = TeamsFranchises” in schema pass  
**Related:** [`baseball-example-program.md`](../baseball-example-program.md)

---

## Problem

Lahman’s **`TeamsFranchises.franchID`** is the correct **historical/baseball-research** organization. It is a **poor primary grain** for Mycelium’s ontology and fan/agent mental models.

Most people think: **city + team name** — not franchise continuity.

- **Brooklyn Dodgers** (1957, `BRO`, `franchID=LAD`) vs **Los Angeles Dodgers** (1958+, `LAN`, same `franchID`) → **different teams** to normal humans
- Only “biggest geeks” treat them as one entity
- Atlanta Braves example is worse: Boston → Milwaukee → Atlanta, many renames — franchise link is non-obvious

---

## Paul’s direction (June 2026)

| Layer | Role |
|-------|------|
| **Primary team registry** | **Fan-facing team identity** — city + name (e.g. Brooklyn Dodgers, LA Dodgers as **separate** rows) |
| **Franchise** | **Interesting metadata** — Lahman `franchID`, lineage, moves; **franchise specialist**; not the default organizer |
| **Emergent organization** | Default answers use fan teams; client pushback → specialist offers re-aggregation |

**Example dialogue:**

1. Client: *“Over time, which team had the highest average RBIs?”*
2. Mycelium: ranked list by **fan team** (Brooklyn Dodgers and LA Dodgers separate)
3. Client: *“Wait — aren’t Brooklyn and LA Dodgers the same team?”*
4. **Franchise specialist:** explains `franchID` continuity; offers answer **by franchise** instead

This is **emergent data organization** — organization changes when query patterns and client needs surface, not guessed upfront in Lahman’s franchise table.

---

## Lahman mapping (reference)

Brooklyn → LA Dodgers (`franchID=LAD`):

- ≤1957: `BRO` — Brooklyn Dodgers  
- ≥1958: `LAN` — Los Angeles Dodgers  

Lahman is right; our **default ontology** should not equate these for ranking/display.

---

## Implications

- **Team MVR:** human **city + name** (or full display name), not `franchID`
- **Player MVR:** name + **fan team name** (still valid; “Dodgers” may need LLM + year context)
- **Cold start:** ingest Lahman as-is into warehouse; **team registry** built from distinct fan-facing identities agents/humans use — not raw `TeamsFranchises` import alone
- **Derivations:** default aggregates keyed by fan team; franchise-level aggregates on demand via specialist
- **Open:** how fan team entities are created (bootstrap from distinct `Teams.name` + city? agent over time?)

---

*Archived June 2026.*