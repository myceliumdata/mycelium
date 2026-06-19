# Deep provenance — lineage expansion beyond computation envelope

**Date:** 2026-06-19  
**Participants:** Paul + Grok  
**Status:** Direction sketched; not implemented  
**Related:** [`2026-06-18-computation-centric-provenance.md`](2026-06-18-computation-centric-provenance.md), [`computation-centric-provenance.md`](../../architecture/whys/computation-centric-provenance.md), baseball M3 `career_avg` manual gate

---

## Problem

`provenance: true` on step 1 returns a **computation-centric** version per attribute — what we ship today:

| Field | What it answers |
|-------|-----------------|
| `sources[]` | Which **dataset snapshot** (or web URL, chain state) was available |
| `computation` | **What program** produced `value` |
| `parameters` | **Runtime inputs** to that program (`lahman.playerID`, warehouse path, scope, …) |

That is necessary but not sufficient when the client needs to audit **which facts** the program consumed.

### Example — Hank Aaron `career_avg` (live Lahman, June 2026)

Shallow provenance (actual MCP response):

- `value`: `0.305`
- `sources[]`: `lahman@v2025.1` dataset pin
- `computation.inline`: Python fetching `SUM(H)` and `SUM(AB)` for `playerID`, dividing in Python
- `parameters`: `aaronha01`, `warehouse/lahman.sqlite`, `attribute: career_avg`

**Missing for deep audit:** the **Batting rows** (or per-season `H`/`AB` tuples) that summed to 3771 hits and 12364 AB. A skeptical agent cannot verify the aggregate without re-querying the warehouse or trusting the specialist cache.

Same gap for:

- **Manifest aggregates** (`career_hr` = `SUM(HR)`) — which seasons/rows contributed?
- **Research attrs** — which passages on a page supported the extracted value?
- **Future cross-domain derives** — which warehouse slices from multiple tables were joined?

---

## Locked direction (Paul, June 2026)

We need the ability to **request deep provenance** at query time — lineage of **data used to compute the final result**, not only the program that ran.

**Distinct layers:**

| Layer | Name (draft) | Content |
|-------|----------------|---------|
| 0 | Value only | `results[]` — default |
| 1 | Shallow | Today’s `provenance: true` — computation envelope |
| 2 | Deep | **Input facts** the computation depended on |

Deep is **opt-in** — token and payload cost can be large (full career batting log).

---

## Request shape (draft — not implemented)

Step 1 flag on `EntityQuery` (exact name TBD):

- `provenance: true` — shallow (unchanged)
- `deep_provenance: true` or `provenance_depth: "inputs"` — on step 2 deliver, expand lineage for requested attributes

Alternative: `provenance: { "depth": "inputs" }` object — defer until API review.

Step-2 deliver hydrates scope from step 1; deep expansion applies to attrs in scope.

---

## Response shape (draft)

Extend existing `versioned_provenance_v1` rather than a second provenance dialect.

Option A — nested on the version:

```json
{
  "value": "0.305",
  "sources": [{ "kind": "dataset", "id": "lahman", "version": "v2025.1" }],
  "computation": { "language": "python", "inline": "…" },
  "parameters": { "lahman.playerID": "aaronha01", "warehouse": "warehouse/lahman.sqlite" },
  "inputs": [
    {
      "kind": "warehouse_rows",
      "table": "Batting",
      "grain": ["playerID", "yearID", "stint", "teamID"],
      "rows": [
        { "yearID": 1954, "teamID": "ML1", "H": 131, "AB": 468 },
        "…"
      ]
    }
  ]
}
```

Option B — references instead of inline rows (`row_refs[]`, content hashes, season-level aggregates only).

Option C — lazy expansion via follow-up MCP tool (`expand_provenance(version_id, depth=inputs)`) — avoids bloating every deliver.

**Open:** which option for v1; caps (max rows, max bytes); redaction policy.

---

## Implementation strategies (open)

| Strategy | Pros | Cons |
|----------|------|------|
| **Record at compute time** | Deliver is fast; faithful to what ran | Storage bloat; derive sandbox must emit citations |
| **Re-query on deep request** | Thin cache; always fresh against warehouse | May not match exact rows if warehouse refreshed; extra SQL on deliver |
| **Hybrid** | Store aggregate breakdown (per-season sums) at compute; row detail on demand | Two code paths |

Warehouse specialists and derive sandbox today **do not** capture row-level inputs. Any v1 likely starts with **re-query** for deterministic SQL (manifest conventions + known `parameters`) and **record-at-research-time** for web paths.

---

## Guinea pig

1. Aaron `career_avg` — deep response includes per-season `H`, `AB` (or row list) that reconcile to `0.305`.
2. Aaron `career_hr` — deep response shows per-season `HR` or row refs summing to 755.
3. CRM research field (later) — snippets or structured extract refs, not URL only.

---

## Non-goals (for first slice)

- Re-execution from provenance (replay) — remains future work per computation-centric note.
- Full 27-table Lahman dump in every response.
- Row-level refs for all regulated domains — optional extension later.

---

## TODO

Tracked in [`TODO.md`](../../../TODO.md) → **Deep provenance (request-time lineage expansion)**.

Distill into program doc + slice when prioritized; likely after baseball M3 program settles and admin provenance UI can display nested inputs.

---

*Archived June 2026.*