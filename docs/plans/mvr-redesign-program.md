# MVR redesign program — lookup, identity, delivery

**Status:** **Locked** (Paul + Grok, June 2026) — ready for Cursor slices  
**Blocks:** Program 2 (versioned bind storage) — run **after** this program  
**Breaking changes:** Yes — remove `entity_key`, `binding`, `name_source`; two-step lookup/delivery protocol

**Related:** [`mvr-best-practices.md`](mvr-best-practices.md), [`attribute-provenance-and-storage.md`](attribute-provenance-and-storage.md), `TODO.md`

---

## Objective

Separate three concerns that today are conflated in `network.json` `mvr` and `EntityQuery`:

| Concern | Meaning |
|---------|---------|
| **Identity** | Stable **`id` (UUID)** only — no non-UUID “entity key” |
| **Lookup** | Find candidate rows by **partial field match** (AND within `lookup`) |
| **MVR** | Per-network **minimum field set** to **create** a new entity and **run extended research** |

Introduce a **two-step delivery protocol** (like quotes): resolve → **`delivery_id`** → deliver records. **`requested_attributes` only on step 1** so quotes can bind scope before payment.

---

## Locked decisions

| # | Decision |
|---|----------|
| R1 | **Identity** = UUID (`EntityQuery.id`). No name/email as primary key. |
| R2 | **Input:** `id` **OR** `lookup` (never require both). **AND** within `lookup` map; **OR** between `id` vs `lookup`. |
| R3 | **MVR** = `network.json` `mvr.bind_fields[]` — designer-defined; enforced at **create** only. Every stored entity has complete MVR. |
| R4 | **Lookup** partial OK (e.g. `employer=IBM` → many matches). Not required to supply full MVR for search. |
| R5 | **Indexes:** one inverted index per MVR field on `entities.json`; optional compound index later (Program 2 / operator). |
| R6 | **Two-step delivery:** step 1 → `total_matches` + `delivery_id`; step 2 → `delivery_id` (+ `quote_id` if `metering.enabled`) → `results[]`. **No `deliver: true` flag.** |
| R7 | **`requested_attributes` only on step 1** — bound into `delivery_id` / quote workload; step 2 is tokens only. |
| R8 | **`metering.enabled`** is the only billing switch. No `meter_search`. Free networks deliver on `delivery_id` only. |
| R9 | **Batch:** N matches + attrs → quote/deliver/research **all N**; meter ≈ N singles. |
| R10 | **Create:** 0 matches + **full MVR in step-1 `lookup`** + attrs → provisional create → research. Partial lookup never creates. |
| R11 | **Invalid / unknown `id`:** `not_found`, no `delivery_id`. |
| R12 | **TTL:** `delivery_id` and `quote_id` both **5 minutes** (env-configurable, default 300s). |
| R13 | **Fuzzy:** keep today’s **suggestions** on miss; no widened index lookup in v1. |
| R14 | **Limits / pagination / abuse caps:** deferred (`safety_cap`, `max_results` later). |
| R15 | **Query any field:** future `TODO.md` item — out of scope. |

---

## Two-step protocol

### Step 1 — Resolve (lookup or id)

**Request** (examples):

```json
{
  "lookup": { "employer": "IBM" },
  "requested_attributes": ["linkedin"],
  "provenance": false
}
```

```json
{
  "id": "3c3daf80-5e10-411e-8961-3e8d0f3421d4"
}
```

**Response** (metering off, attrs or not):

```json
{
  "outcome": "lookup_resolved",
  "total_matches": 237,
  "results": [],
  "delivery": {
    "delivery_id": "d_…",
    "expires_at": "…"
  },
  "quote": null
}
```

**Response** (metering on, delivery and/or research billable):

```json
{
  "outcome": "quote_required",
  "total_matches": 237,
  "results": [],
  "delivery": { "delivery_id": "d_…", "expires_at": "…" },
  "quote": {
    "quote_id": "q_…",
    "workload": { "delivery_id": "d_…", "requested_attributes": ["linkedin"], … },
    "line_items": [ … ],
    "total_usd": …
  }
}
```

### Step 2 — Deliver

**Request** — tokens only (attrs already bound on `delivery_id`):

```json
{
  "delivery_id": "d_…",
  "quote_id": "q_…"
}
```

(`quote_id` omitted when `metering.enabled` is false.)

**Response:** `assembled` / `found` with full `results[]` (and `provenance` if requested on step 1). Batch = N rows.

### Outcomes

| Outcome | When |
|---------|------|
| `lookup_resolved` | Step 1; count + `delivery_id`; free delivery available |
| `quote_required` | Step 1; metering on; need `quote_id` + `delivery_id` to deliver |
| `not_found` | 0 matches, unknown `id`, or expired/invalid tokens |
| `assembled` / `found` | Step 2 delivery (and research when attrs bound) |

---

## `network.json` (MVR block)

```json
{
  "mvr": {
    "bind_fields": ["name", "employer"],
    "description": "CRM: display name + current employer to create a person and research extended attrs."
  },
  "metering": {
    "enabled": false
  }
}
```

**Removed:** `name_source` (name is a normal field in `lookup` / stored row).

---

## `EntityQuery` (target shape)

| Field | Step | Description |
|-------|------|-------------|
| `id` | 1 | UUID — resolve single entity (still returns `delivery_id`) |
| `lookup` | 1 | `{ field: value }` — AND match; keys ⊆ `mvr.bind_fields` |
| `requested_attributes` | 1 only | Extended attrs + optional `provenance` flag |
| `provenance` | 1 only | Bound into delivery scope |
| `delivery_id` | 2 | From step 1 |
| `quote_id` | 2 | When metering accepted |

**Removed:** `entity_key`, `binding`.

---

## Create flow (0 matches)

| Step-1 `lookup` | `requested_attributes` | Result |
|-----------------|------------------------|--------|
| Partial, 0 matches | any | `not_found` — no create |
| Full MVR, 0 matches | non-empty | Create provisional → `delivery_id` → validate → research on deliver |
| Full MVR, 0 matches | empty | `not_found` or `lookup_resolved` with create on deliver — **prefer create on deliver step when lookup is full MVR** (slice M7) |

---

## Implementation stores

| Store | TTL | Holds |
|-------|-----|-------|
| `DeliveryStore` | 5 min | `delivery_id` → `entity_ids[]`, lookup snapshot, `requested_attributes`, `provenance` |
| `QuoteStore` | **5 min** (change from 1h) | `quote_id` → workload referencing `delivery_id` |

Env: `MYCELIUM_DELIVERY_TTL_SEC`, `MYCELIUM_QUOTE_TTL_SEC` (default `300`).

---

## Slice map

| Slice | Cursor prompt (queued) | Scope |
|-------|------------------------|--------|
| **M1** | `2026-06-13-1000-mvr-redesign-slice-m1` | Docs: best practices, architecture sections, JSON schema notes in `describe_network`; no runtime behavior |
| **M2** | `mvr-redesign-slice-m2` | `DeliveryStore`, TTL 5m for delivery + quotes, `DeliveryScope` model, unit tests |
| **M3** | `mvr-redesign-slice-m3` | `EntityQuery` / `QueryResponse` models, outcomes (`lookup_resolved`), remove deprecated fields, validation |
| **M4** | `mvr-redesign-slice-m4` | Per-field indexes; lookup resolution (AND); step-1 graph path → count + `delivery_id` |
| **M5** | `mvr-redesign-slice-m5` | Step-2 deliver path (metering off): `delivery_id` → MVR `results[]` |
| **M6** | `mvr-redesign-slice-m6` | Metering: quote binds `delivery_id` + attrs; batch line items; step-2 with `quote_id` |
| **M7** | `mvr-redesign-slice-m7` | Create on 0 + full MVR; two-step for `id`; remove `name_source` / old resolution |
| **M8** | `mvr-redesign-slice-m8` | Batch deliver + research N entities; batch `provenance.entities[]` |
| **M9** | `mvr-redesign-slice-m9` | CLI, MCP, admin status, example JSON, README migration |
| **M10** | `mvr-redesign-slice-m10` | Polish, smoke tests, doc sync |

**Order:** M1 → M2 → … → M10 (review between slices per `prompts/cursor/WORKFLOW.md`).

---

## Explicit non-goals (this program)

- Program 2 versioned bind storage / `bind_versions[]`
- Query/search arbitrary extended fields
- Pagination cursors
- `safety_cap` / `max_results` enforcement
- Fuzzy index widening (suggestions only)
- Operator edit UI (Program 3)

---

## Verification

Each slice: `./bin/ci-local` green before review. Update `examples/networks/*/queries/` and MCP README for two-step flow in M9.

---

*Last updated: June 2026 (locked for implementation)*