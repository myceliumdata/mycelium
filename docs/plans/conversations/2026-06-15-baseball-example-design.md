# Baseball example — early design notes (Paul + Grok/Cursor)

**Date:** 2026-06-15  
**Status:** Exploratory — not locked for implementation  
**Related:** [`mycelium_lahman_design_prompt.md`](../mycelium_lahman_design_prompt.md), [`2026-06-14-data-factory-origin.md`](2026-06-14-data-factory-origin.md)

---

## Scope

- **Network name:** `baseball`
- **Single network** (not multiple networks)
- **Dataset:** Lahman 1871–2025 CSVs (~40MB zip at `~/mycelium-networks/baseball/seed/lahman_1871-2025_csv.zip`)
- **Hosting:** TBD — prefer not to commit 40MB to git; SABR Box not bot-fetchable; may self-host

---

## Identity model (three layers)

| Layer | Role |
|-------|------|
| **MVR** | Human/agent lookup to find or create a registry row |
| **Registry `id`** | **uuid4** assigned on load (locked June 2026) — client shortcut after resolve |
| **Source keys** | Lahman `playerID`, `teamID`, etc. — provenance / re-import; not a parallel public API |

---

## Registry grains (two MVRs → two registries)

1. **Player** — biographical / career identity (`People` and attached stat tables)
2. **Team** — organization/franchise identity (not “team in one season” as a separate grain — Lahman `Teams` rows are per-year; **year** is query scope). Roster = players via fact-table joins.

Stat tables (`Batting`, `Pitching`, `Fielding`, `Appearances`, …) are **parallel** player-attached facts — none is privileged over the others.

---

## Player MVR (draft)

- **Not** birth year — fans know **names and teams**, not birthdays.
- **Draft MVR:** player name + team (fields and normalization TBD).
- **Team is a disambiguator, not a scope.** MVR identifies *which person*. If Aaron played for the Braves and the Red Sox, **`Aaron + Braves`** and **`Aaron + Red Sox`** must resolve to the **same** player row — any team he played for is valid for bind lookup when distinguishing homonyms.
- **Twist:** bind index cannot be a single `name|team` compound key if multiple teams per player are all valid aliases for the same uuid. Index design TBD (e.g. index each (name, team) pair seen in Lahman → same entity id).
- **Season / stint** scope is separate (query step 2 / derivation), not part of player or team identity.

---

## Router / factory

- Supervisor resolves **which registry / MVR** first, then operation (read / join / derive).
- Cross-specialist queries are normal (e.g. awards + pitching + aggregation).
- Derived artifacts: agents decide cache vs one-shot; retention economics deferred — see origin conversation (lifetime team BA series vs per-block blockchain data).

---

## ER diagram status

Incomplete until full CSV bundle is inspected in-repo or under `~/mycelium-networks/baseball/seed/` (unzipped). Paul to share / unzip for schema pass.

---

*Archived from design discussion, June 2026.*