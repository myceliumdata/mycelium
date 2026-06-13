# MVR redesign — EntityQuery examples

**Canonical program spec:** [`mvr-redesign-program.md`](mvr-redesign-program.md)  
**Runtime today:** target two-step protocol (`id` / `lookup` → `delivery_id`) on CLI, MCP, and admin since M9.

These examples show the **locked target** two-step protocol.

---

## Step 1 — Resolve by lookup

**Request:**

```json
{
  "lookup": { "employer": "IBM" },
  "requested_attributes": ["linkedin"],
  "provenance": false
}
```

**Response** (`metering.enabled: false`):

```json
{
  "outcome": "lookup_resolved",
  "total_matches": 237,
  "results": [],
  "delivery": {
    "delivery_id": "d_8f3c2a1b…",
    "expires_at": "2026-06-13T10:05:00+00:00"
  },
  "quote": null,
  "message": "Resolved 237 matches for lookup.",
  "debug": {}
}
```

**Response** (`metering.enabled: true`, delivery and/or research billable):

```json
{
  "outcome": "quote_required",
  "total_matches": 237,
  "results": [],
  "delivery": {
    "delivery_id": "d_8f3c2a1b…",
    "expires_at": "2026-06-13T10:05:00+00:00"
  },
  "quote": {
    "quote_id": "q_4e2d9c…",
    "workload": {
      "delivery_id": "d_8f3c2a1b…",
      "requested_attributes": ["linkedin"],
      "provenance": false
    },
    "line_items": [],
    "total_usd": 0.0
  }
}
```

---

## Step 1 — Resolve by id

**Request:**

```json
{
  "id": "3c3daf80-5e10-411e-8961-3e8d0f3421d4"
}
```

**Response:** same shape as lookup resolve — `total_matches: 1`, `delivery_id`, empty `results[]`. Unknown or expired id → `not_found` (no `delivery_id`).

---

## Step 2 — Deliver

**Request** (metering off):

```json
{
  "delivery_id": "d_8f3c2a1b…"
}
```

**Request** (metering on, after quote accepted / paid):

```json
{
  "delivery_id": "d_8f3c2a1b…",
  "quote_id": "q_4e2d9c…"
}
```

`requested_attributes` and `provenance` are **not** sent on step 2 — they were bound on step 1 into `delivery_id` / quote workload.

**Response:**

```json
{
  "outcome": "assembled",
  "results": [
    {
      "id": "3c3daf80-5e10-411e-8961-3e8d0f3421d4",
      "name": "Jane Example",
      "employer": "IBM",
      "linkedin": "https://linkedin.com/in/jane"
    }
  ],
  "provenance": null,
  "message": "Found record for Jane Example."
}
```

When step 1 bound `provenance: true`, step 2 may include `QueryResponse.provenance` with version history for requested extended attributes (see Program 1 spec).

Batch: N matches from step 1 → step 2 returns N rows in `results[]`; metering scales ≈ N singles.

---

## Create (0 matches, full MVR)

**Step 1 request:**

```json
{
  "lookup": { "name": "Paul Murphy", "employer": "Acme Corp" },
  "requested_attributes": ["email"]
}
```

When no row matches and `lookup` contains the full MVR field set, the network may create a provisional entity on the deliver path (slice M7). Partial lookup with 0 matches → `not_found` only (no create).

---

## Removed fields (target)

| Removed | Replacement |
|---------|-------------|
| `entity_key` | `id` or `lookup.name` (and other MVR fields) |
| `binding` | fields inside `lookup` on step 1 |
| `mvr.name_source` | `name` is a normal indexed MVR field |

---

*Last updated: June 2026 (MVR redesign M1)*
