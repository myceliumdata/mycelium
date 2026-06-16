# Canonical team & city names — discovery strategy

**Date:** 2026-06-16  
**Participants:** Paul + Grok/Cursor  
**Status:** Design proposal  
**Related:** [`2026-06-16-llm-alias-resolution.md`](2026-06-16-llm-alias-resolution.md), [`2026-06-16-team-vs-franchise-grain.md`](2026-06-16-team-vs-franchise-grain.md)

---

## Problem

Fan-facing team grain needs **canonical** city + name, but clients (and data) use variants:

| Kind | Examples |
|------|----------|
| Team | Brooklyn Dodgers / LA Dodgers / Los Angeles Dodgers / Dodgers |
| City | New York / NY / NYC |

Hardcoded alias tables per network do not scale; franchise table is the wrong primary organizer.

---

## Canonical form (locked)

- **Full canonical name** only for team MVR/display (e.g. `Los Angeles Dodgers`) — not separate city + nickname fields.

## Discovery (not framework-hardcoded)

**Do not** bake “read Lahman `Teams.name`” into Mycelium core. Baseball **bootstrap specialists** explore ingested sources per **`guide.md` policy** and propose registry rows.

*Illustration only (Lahman 2025):* distinct season team label strings might yield ~241 fan-team candidates including `Brooklyn Dodgers` and `Los Angeles Dodgers` — the specialist discovers that; framework provides `distinct_values` + propose-registry tools.

Nickname-only (**Dodgers**) is **ambiguous** → `lookup_suggested`, not one canonical.

See [`2026-06-16-canonical-names-bootstrap-specialists.md`](2026-06-16-canonical-names-bootstrap-specialists.md).

---

## Layered discovery (recommended)

### 1. Authority at ingest (one-time, agent + LLM)

After warehouse load, run an **enrichment pass** over distinct `Teams.name` (241 rows — cheap):

- **Input:** full Lahman name + readme/glossary + `guide.md` baseball context
- **Output per fan team:**
  - `canonical_name` (default: Lahman string unless clearly wrong)
  - `canonical_city` (parsed, expanded: `Los Angeles` not `LA`)
  - `canonical_nickname` (`Dodgers`, `Yankees`, …)
  - `aliases[]` (`LA Dodgers`, `Dodgers (Brooklyn era)` — **proposed**, human/agent review optional)

Store in warehouse **team_identity** table (not giant JSON) with provenance (“generated at ingest by …”).

**Local LLM** fits here; batch job, not per-query.

### 2. Runtime alias expansion (query-time)

Already locked: *“In the context of baseball teams, what could `Yanks` refer to?”* → canonical `New York Yankees` → step-1 retry.

Same for `NY` + `Yankees`, `LA` + `Dodgers` — **context includes list of canonical teams** (or top-k retrieval), not blind guess.

### 3. Never canonicalize nickname alone

| Lookup | Behavior |
|--------|----------|
| `{team: "Los Angeles Dodgers"}` | Exact (or fuzzy typo) |
| `{city: "Los Angeles", team: "Dodgers"}` | Exact fan team |
| `{team: "Dodgers"}` | **Incomplete** — suggest Brooklyn / Los Angeles / Newark with `suggested_lookup` |
| `{city: "NY", team: "Yankees"}` | LLM expand city → `New York` + match |

### 4. Emergent refinement

When clients push back (franchise dialogue, wrong split), agents **append aliases** or merge/split team identities — versioned provenance, not silent overwrite. Franchise specialist may link fan teams without collapsing default canon.

### 5. City normalization

- **Primary source:** parse from canonical `Teams.name` + **Parks.csv** `city`/`state` for ballpark cities
- **LLM batch:** expand abbreviations (`NY` → `New York`) with **US baseball context**; store `city_aliases[]` per canonical city
- **Do not** rely on a global geo database in v0 — network-scoped is enough

---

## What not to do (v0)

- Import `franchID` as team display name
- Single compound key `city|nickname` without alias index (same lesson as player name+team)
- Expect `SequenceMatcher` to bridge `LA` ↔ `Los Angeles`

---

## Open

- Team MVR fields: **full `canonical_name`** only vs **city + nickname** pair
- Who approves ingest-time LLM alias proposals (auto-accept vs operator gate)
- Deduping 241 Lahman names vs agent-created fan teams over time

---

*Archived June 2026.*