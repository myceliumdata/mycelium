# Why multi-record-type routing (and fan team vs franchise)

**Status:** Shipped (baseball slices 1000–1800, June 2026)  
**Mechanics:** [`query-record-type-router.md`](../../query-record-type-router.md) · [`baseball-example-program.md`](../../plans/baseball-example-program.md)

---

## The short answer

One network may host **multiple registry record types** (baseball: `player` and `team`). Step 1 infers record type from **lookup key shape** — not `EntityQuery.record_type`, not fan-out across grains, not a disambiguation LLM.

Each record type declares disjoint `bind_fields` in `network.json`. The client sends keys that match exactly one type’s field set (or a strict subset for partial lookup).

**Team vs franchise:** default organization uses **fan-facing city + name** (Brooklyn Dodgers ≠ Los Angeles Dodgers). Lahman `franchID` is research metadata surfaced by a future **franchise specialist** when clients push back — emergent organization, not upfront franchise-as-primary-key.

---

## What problem we were solving

| Early approach | Failure |
|----------------|---------|
| `EntityQuery.grain` client override | Callers must know internal ontology; easy to mis-route |
| Multi-grain fan-out | One lookup hits player *and* team stores; ambiguous merges |
| Grain-disambiguation LLM | Hot-path LLM for routing; brittle and costly |
| Lahman `franchID` as team MVR | Fan questions (“best Dodgers season”) disagree with geek franchise model |

Baseball needs two registries in **one** network without complicating CRM’s single `person` type.

---

## Record-type routing rules

`infer_record_type_from_lookup()` (`network/mvr.py`):

1. Normalize lookup keys
2. Find record types whose `bind_fields` set **equals** the lookup key set exactly → route
3. **Zero matches** — if keys are strict subset of one type’s bind fields → partial path on that type; else `not_found`
4. **Two+ exact matches** — should not occur with disjoint bind field names

| Baseball lookup keys | Record type |
|---------------------|-------------|
| `player` + `debut_team` + `debut_year` | `player` (full MVR) |
| `player` only (partial) | `player` |
| `team` only | `team` |
| `{player, team}` legacy | `not_found` (`team` not a player bind field) |

`id`-only step 1 searches **all** record-type stores (`resolve_id_all_record_types`).

`DeliveryScope.record_type` is frozen at `delivery_id` issue time — step 2 loads the matching registry.

---

## `new_records` policy per type

| Value | Partial 0-hit | Full MVR 0-hit |
|-------|---------------|----------------|
| `query_allowed` (CRM `person`) | fuzzy → `lookup_suggested`, else `lookup_incomplete` | fuzzy → suggest, else `create_pending` |
| `bootstrap_only` (baseball) | fuzzy → LLM alias → resolve / not_found | never `create_pending` |

Baseball players and teams are populated at bootstrap; visiting agents resolve and query — they do not create registry rows via public query.

---

## Identity layers (player example)

| Layer | Role |
|-------|------|
| **MVR** | `player` + `debut_team` + `debut_year` — human lookup / disambiguation |
| **`id`** | uuid4 — shortcut after first resolve |
| **Source keys** | `lahman.playerID` — warehouse joins, bootstrap dedup; not default `results[]` |
| **Field aliases** | `Dodgers` → canonical team name (LLM on `bootstrap_only` 0-hit) |
| **Career teams** | Warehouse facts — not extra player `bind_index` keys |

One uuid per `lahman.playerID`; debut bind chosen at bootstrap (earliest debut season). Multi-team careers do not multiply player registry rows.

---

## Fan team vs franchise (emergent organization)

Lahman `TeamsFranchises.franchID` is correct for **baseball research history**. It is a poor **default grain** for how people ask questions.

| Human mental model | Lahman franchise model |
|--------------------|------------------------|
| Brooklyn Dodgers (1957) and LA Dodgers (1958+) are **different teams** | Same `franchID=LAD` |
| “Which team had highest average RBIs over time?” → rank **fan teams** | Franchise aggregation is opt-in |

**Target dialogue:**

1. Client asks career ranking by team → answers use fan-facing team entities
2. Client: “Aren’t Brooklyn and LA Dodgers the same franchise?”
3. **Franchise specialist** (deferred) explains continuity; offers re-aggregation by `franchID`

Organization **changes when query patterns surface** — not guessed entirely from `TeamsFranchises` at bootstrap.

**Team MVR:** single `team` bind — full canonical city+name label (e.g. `Brooklyn Dodgers`). `teamID` / `franchID` stay in warehouse provenance.

---

## What we deliberately did not do

| Alternative | Why we rejected it |
|-------------|-------------------|
| Client `record_type` on `EntityQuery` | Leaks manifest knowledge; duplicate of key-shape inference |
| Fan-out resolve | Ambiguous `total_matches`; breaks batch quoting |
| `franchID` as team bind field | Wrong default for fan queries and LLM aliases |
| Appearance-driven player bind explosion | One primary debut bind per player at bootstrap |
| Query-time team/player creation | `bootstrap_only` — registry is curated at load |

---

## Related

- MVR vs lookup: [identity-lookup-and-mvr.md](identity-lookup-and-mvr.md)
- Warehouse stats after resolve: [warehouse-factory-stack.md](warehouse-factory-stack.md)
- Source keys in provenance: [computation-centric-provenance.md](computation-centric-provenance.md)