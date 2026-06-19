# Why computation-centric provenance

**Status:** Shipped for baseball M1–M2; CRM research migration ongoing  
**Mechanics:** [`architecture.md`](../../architecture.md) § Specialist I/O protocol · baseball hand-test: [`2026-06-19-baseball-specialist-hand-test.md`](../../manual-checks/2026-06-19-baseball-specialist-hand-test.md)

---

## The short answer

A `found` attribute version records **four separable things**:

| Field | Role |
|-------|------|
| **`sources[]`** | Raw **input material** (dataset snapshot, web page, chain state) — not the interpretation |
| **`computation`** | The **program that ran** to produce `value` from that material |
| **`parameters`** | Runtime input **values** (entity bridge keys, warehouse path, scope like `yearID`) |
| **`actor`** | Which specialist executed the pipeline |

A Tavily URL in `sources[]` is evidence the model read a page — not proof of how `linkedin` or `career_hr` was derived. Warehouse stats must not pretend URLs are domain truth.

---

## What problem we were solving

Legacy research provenance stored URLs and implied “the LLM figured it out.” That fails auditors and agents who need to:

- Reconcile conflicting values across versions
- Know whether a stat came from Lahman v2025.1 or a blog post
- Compare marginal cost of recompute vs trusting cache
- Debug wrong answers (wrong LinkedIn post vs wrong SQL)

Same gap would appear for Lahman aggregates if we only cited `Batting.csv` without recording the aggregation logic.

---

## `sources[]` kinds

**Dataset (slow-moving ground truth):**

```json
{
  "kind": "dataset",
  "id": "lahman",
  "version": "v2025.1",
  "retrieved_from": "https://github.com/myceliumdata/lahman-seed.git",
  "ref": "v2025.1"
}
```

Pins the **ingested snapshot**, not the local SQLite path. Annual refresh → new dataset version on new `versions[]` entries.

**Web (ephemeral pages):**

```json
{
  "kind": "web",
  "url": "https://…",
  "fetched_at": "2026-06-18T…"
}
```

Extraction logic belongs in `computation`, not in the URL alone.

**Chain state (future):** block height / state root at computation time — same envelope, different cadence.

---

## `computation`

Records what actually executed — inline source for short programs, URI + `entrypoint` + optional `content_hash` for committed specialist code:

```json
{
  "language": "python",
  "uri": "specialists/batting_specialist.py",
  "entrypoint": "career_hr",
  "content_hash": "sha256:…"
}
```

`content_hash` is integrity over artifact bytes at run time — not a substitute for storing `inline` when that *is* what ran.

M3+ derive path may use sandbox-generated `inline` on first miss; cache subsequent delivers from specialist storage.

---

## `parameters`

Auditors need **values**, not schema documentation:

```json
{
  "lahman.playerID": "aaronha01",
  "warehouse": "warehouse/lahman.sqlite",
  "attribute": "career_hr",
  "column": "HR"
}
```

- Entity bridge: namespaced source keys from registry
- Infrastructure: warehouse path, scope (`yearID`, `teamID`) when relevant
- SQL table/column names stay inside `computation` — not required in provenance envelope

Secrets never appear in provenance; env names only if needed.

---

## Same envelope everywhere

Warehouse read, web bio extraction, career sum, future LLM-generated derive, and operator correction all use `versioned_provenance_v1` with the same shape. Clients and admin UI learn one audit model.

CRM research versions gradually adopt `computation` (extraction prompt / tool chain) instead of URL-only implication.

---

## What we deliberately did not do

| Alternative | Why we rejected it |
|-------------|-------------------|
| URL as answer | Hides extraction and aggregation logic |
| Per-network provenance shapes | Fragments admin and MCP clients |
| Store SQL in `sources[]` | Conflates material with program |
| Re-execution from provenance in v1 | Audit record only; replay is future work |
| API keys in `parameters` | Security leak in version history |

---

## Related

- Warehouse resolve path: [warehouse-factory-stack.md](warehouse-factory-stack.md)
- Storage truth layer: [three-layer-storage-model.md](three-layer-storage-model.md)