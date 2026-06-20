# Computation-centric provenance — sources vs what ran

**Date:** 2026-06-18  
**Participants:** Paul + Grok  
**Status:** Direction locked for M1 baseball; not implemented  
**Related:** [`2026-06-14-data-factory-origin.md`](2026-06-14-data-factory-origin.md), [`baseball-example-program.md`](../baseball-example-program.md), [`architecture.md`](../../architecture.md) § Specialist I/O protocol

---

## Problem

Today’s research provenance is weak: a `found` version stores **URLs in `sources[]`** and implies the LLM “figured it out.” The URL is **input material**, not the answer. We do not record **what ran** over that material to extract or compute the returned value.

Same gap for Lahman warehouse stats: we have not shipped stat specialists yet; when we do, provenance must not pretend Tavily URLs are domain truth.

---

## Locked direction (Paul, June 2026)

Every `found` attribute version — warehouse read, web bio, aggregate, or future financial derivative — uses the **same envelope** inside existing `versioned_provenance_v1` (`versions[]`, `current_version_id`):

| Field | Role |
|-------|------|
| **`sources[]`** | Raw **input material** available to the computation (not the interpretation) |
| **`computation`** | The **actual program** that produced `value` from that material |
| **`parameters`** | Inputs passed to that program (entity `source_keys`, scope, block height, search query, …) |
| **`actor`** | Which specialist (or pipeline) ran it |

**Not required in provenance:** SQL table/column names — that detail lives inside `computation` if needed at all.

**Secrets:** Never store API keys or credentials in provenance; parameters may reference env/config names only.

**Re-execution:** Out of scope for this note — provenance is an audit record.

---

## `sources[]` kinds (draft)

### Dataset (slow-moving ground truth — Lahman)

Pins the **ingested snapshot**, not the local SQLite path:

```json
{
  "kind": "dataset",
  "id": "lahman",
  "version": "v2025.1",
  "retrieved_from": "https://github.com/myceliumdata/lahman-seed.git",
  "ref": "v2025.1"
}
```

Aligns with `seed.source.json` / bootstrap fetch. Annual refresh → new dataset version on new versions.

**Dataset manifest (deferred, not v1):** Network-level catalog so provenance cites `lahman@v2025.1` by id and the framework resolves `retrieved_from` once — reduces bloat. See `TODO.md`.

### Web (ephemeral pages — supplemental bio, etc.)

```json
{
  "kind": "web",
  "url": "https://…",
  "fetched_at": "2026-06-18T…"
}
```

URL is source data; extraction logic belongs in `computation`.

### Chain state (fast-moving — future)

Not annual dataset versioning. Pin state at computation time:

```json
{
  "kind": "chain_state",
  "chain_id": 1,
  "block": 18234567,
  "state_root": "0x…"
}
```

Same provenance philosophy; different source cadence and refresh policy.

---

## `computation`

Stores **what actually ran** — Paul: executable strings are fine (Python, bash, Go, Lisp, …).

**Short — inline:**

```json
{
  "language": "python",
  "inline": "<exact source that was executed>"
}
```

**Long — URI + content hash:**

```json
{
  "language": "python",
  "uri": "specialists/batting_specialist.py",
  "entrypoint": "career_hr",
  "content_hash": "sha256:…"
}
```

### What is `content_hash`?

Digest of the **computation artifact bytes at run time** — the canonical definition of “this code”:

| Case | Hash over |
|------|-----------|
| `inline` only | UTF-8 bytes of `inline` (optional; redundant if full text stored) |
| `uri` | File contents at `uri` when the version was written (typically SHA-256) |
| `uri` + `entrypoint` | Whole module file unless we later split recipe files — then hash that file |

Purpose: integrity — fetched code from `uri` can be checked against what ran. Not a substitute for storing `inline` when that *is* what ran.

M1 may use specialist module path + `entrypoint` without hash until we wire hashing; hash is the v1.1 polish for URI indirection.

---

## `parameters`

Registry bridge without warehouse schema in provenance:

```json
{
  "parameters": {
    "lahman.playerID": "aaronha01"
  },
  "scope": {}
}
```

`source_keys` on `RegistryEntity` are set at bootstrap; provenance records which keys the computation consumed. Season/team scope (e.g. `yearID`) goes in `scope` when query context, not MVR.

---

## Example versions

### Lahman career HR (computed)

```json
{
  "id": "v1",
  "at": "2026-06-18T…",
  "status": "found",
  "value": "755",
  "actor": {
    "kind": "specialist",
    "category": "batting",
    "specialist": "batting_specialist"
  },
  "sources": [
    {
      "kind": "dataset",
      "id": "lahman",
      "version": "v2025.1",
      "retrieved_from": "https://github.com/myceliumdata/lahman-seed.git",
      "ref": "v2025.1"
    }
  ],
  "computation": {
    "language": "python",
    "inline": "…"
  },
  "parameters": {
    "lahman.playerID": "aaronha01"
  }
}
```

### Web supplemental bio (researched)

```json
{
  "id": "v1",
  "at": "2026-06-18T…",
  "status": "found",
  "value": "Mobile, Alabama",
  "actor": {
    "kind": "specialist",
    "category": "bio",
    "specialist": "bio_specialist"
  },
  "sources": [
    {
      "kind": "web",
      "url": "https://…",
      "fetched_at": "2026-06-18T…"
    }
  ],
  "computation": {
    "language": "python",
    "inline": "…"
  },
  "parameters": {
    "lahman.playerID": "aaronha01",
    "field": "birth_city"
  }
}
```

LLM-heavy paths: `computation` may include prompt template + model id / hash — still “what ran,” not URL-only.

---

## Contrast with today’s research path

| Today | Target |
|-------|--------|
| `sources: [{ url }]` required for `found` | `sources` = input material; `computation` required |
| `confidence` gate | Optional for deterministic dataset code |
| `actor.kind: research` | `actor.kind: specialist` (+ pipeline metadata as needed) |
| No extraction record | Full runner / script / module reference |

Framework: new write helper for computed versions (not `research.py` URL validator). Pass-through provenance API unchanged.

---

## Source-first networks + ontology (same session)

CRM cold start: empty → ontology invents categories → research fills data.

Baseball: warehouse + registries exist → ontology **routes** `requested_attributes` to specialists that read/derive from versioned datasets.

Ontology bootstrap (future): `guide.md` + domain readme + **warehouse introspection** (tables, columns, samples) → LLM → `categories.json`. Hybrid acceptable: committed baseball ontology for M1 + generator later.

`source_keys` on registry entities remain the join bridge (`lahman.playerID`); manifest declaration of expected keys per record type is a follow-on.

---

## M1 scope hint (24h ambition)

1. Baseball `categories.json` (committed in example pack — not CRM copy).
2. One warehouse-backed specialist (e.g. `career_hr` or `birth_date` from Lahman).
3. Version writer emitting `dataset` + `computation` + `parameters`.
4. One smoke / hand query with `provenance=true`.

Defer: dataset manifest, web bio with full extraction provenance, ontology LLM bootstrap, `content_hash` automation.

---

## Open (non-blocking)

- Forensic row-level refs for regulated domains — optional extension.
- Normalizing `sources[]` display in admin when `kind !== web`.
- Research path migration — record Tavily+LLM pipeline as `computation`.

---

*Archived June 2026.*