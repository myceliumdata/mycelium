# Why three-layer storage (canonical, indexes, protocol record)

**Status:** Shipped (Programs 1–2, June 2026)  
**Mechanics:** [`attribute-provenance-and-storage.md`](../../plans/attribute-provenance-and-storage.md) · [`architecture.md`](../../architecture.md) § Storage · § Specialist I/O protocol

---

## The short answer

Entity data is split into three layers with different jobs:

```text
1. Specialist storage     → canonical values + versioned provenance (source of truth)
2. Registry indexes       → bind_index, field indexes (derived, fast resolve)
3. Entity protocol record → id, validation_state, cached bind values, pointers
```

Framework code reads specialist data only through **dispatch snapshots**. It never parses internal `versions[]` layout except to pass provenance through on `provenance=true` responses.

---

## What problem we were solving

Paul Murphy LinkedIn was the motivating bug: wrong URL stored, no audit trail of *what changed, when, by whom, from which sources*. Flat overwrite on `entities.json` or specialist JSON made debugging and operator correction impossible.

At the same time, step-1 lookup cannot scan all specialist files per query — we need O(1) indexes on the registry.

| Single-layer approach | Failure |
|----------------------|---------|
| Everything in `entities.json` | No per-field version history; provenance bloat on registry |
| Everything in specialists only | Slow resolve; graph must open every category per lookup |
| Duplicate full copies | Drift when specialist and registry disagree |

The three-layer model separates **truth**, **search**, and **protocol state**.

---

## Layer 1 — Canonical attribute values

Location: `<network_root>/agents/<category>/storage.json` (or `storage.sqlite` after `minisql_v1` migration).

Each field (bind or extended) uses `versioned_provenance_v1`:

- `versions[]` — append-only history (`found`, `na`, `pending`, operator edits)
- `current_version_id` — hot-path read
- Per version: `value`, `status`, `at`, `sources[]`, `actor`, optional `computation` (baseball)

**All statuses get versions** — pending retries update in place; status changes append new versions.

Writes go through `dispatch_write_fields` / bind multi-write → then registry sync.

---

## Layer 2 — Search indexes

Location: on each entity document (`entities/<record_type>.json` or minisql entity store).

| Index | Role |
|-------|------|
| `bind_index` | Normalized composite bind key → `id` |
| Per-field indexes | Single-field lookup (e.g. `player` only) |
| `field_aliases` | Nickname → canonical value (LLM expansion on `bootstrap_only`) |

Indexes update **atomically** on every canonical write. Framework never infers bind matches by scanning specialist storage.

**Bind correction policy:** replace — remove old normalized keys, add new; do not retain old bind keys as aliases.

---

## Layer 3 — Entity protocol record

Each registry row holds:

- `id` (uuid4)
- Cached `bind_values` (denormalized current — **not** source of truth)
- `validation_state`, `field_states`, `source`, timestamps
- Summary pointers: `attr_sources`, `last_researched_at`

**`validation_state`** means “has this network accepted the bind as well-formed enough to research extended attrs?” — not real-world validity.

Protocol metadata drives the graph state machine; it is not a person fact.

---

## Read and write paths

**Write (any attr or bind):**

```text
attribute_write → specialist dispatch → versions[] append
                 → entity row cache + indexes update
```

**Read (query deliver):**

```text
build_context → dispatch_read_category_slice / read_fields
              → FieldSnapshot / FieldContextSnapshot
              → assemble_response
```

**Read (step-1 resolve):** registry indexes only — no specialist reads unless delivering.

---

## Why denormalized cache on the entity row

Specialist storage is authoritative, but returning bind fields on every response would require N specialist reads for identity-only delivers.

Cached `name` / `employer` (or baseball debut binds) on the entity row give fast identity assembly. On mismatch after a write bug, specialist `versions[]` wins — cache is rebuilt from dispatch returns.

---

## What we deliberately did not do

| Alternative | Why we rejected it |
|-------------|-------------------|
| `bind_versions[]` on entity row | Duplicates specialist history; Program 2 locked specialist ownership |
| Full citation lists on registry | Registry bloat; provenance lives in specialist versions |
| Framework reads `versions[]` directly | Breaks isolation; blocks storage format evolution |
| Old bind keys as aliases after correction | Hides identity changes; index ambiguity |

---

## Related

- Why specialists own the canonical layer: [specialist-owned-data.md](specialist-owned-data.md)
- Computation envelope for warehouse attrs: [computation-centric-provenance.md](computation-centric-provenance.md)