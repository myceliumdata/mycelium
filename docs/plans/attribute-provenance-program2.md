# Program 2 — MVR / entity storage (versioned bind fields)

**Status:** Locked (June 2026) — Slice 1 queued  
**Architecture:** [`attribute-provenance-and-storage.md`](attribute-provenance-and-storage.md)  
**Prerequisite:** Program 1 complete; MVR redesign M1–M10 shipped  
**Blocks:** Program 3 (operator edit + force re-research UI)

---

## Objective

Give **MVR bind fields** (`name`, `employer`, and future `mvr.bind_fields`) the same **versioned specialist storage** model as extended attributes, with a **single write API** that keeps specialist canonical values, entity-row cache, `bind_index`, and per-field indexes in sync.

**Out of scope (Program 3):** Admin edit UI, force re-research button, `pay_quote` expansion.

---

## Locked decisions (Paul + Grok, June 2026)

| # | Decision |
|---|----------|
| P2-1 | **No entity-level history** — no `bind_versions[]` on `entities.json`. Canonical history = specialist `versions[]` only. |
| P2-2 | **Entity row = cache + protocol** — current `name` / `employer`, `validation_state`, `field_states`, `bind_index`, in-memory field indexes; not a change log. |
| P2-3 | **Ownership from taxonomy** — each `mvr.bind_fields` entry must appear in `categories.json` `attribute_map` → category → `assigned_agent`. Fail loud if unmapped. |
| P2-4 | **Unified write API** — all bind/seed/create paths call one module; no direct registry field writes bypassing specialist versions + index updates. |
| P2-5 | **Index replace policy** — on bind-field correction, update `bind_index` and field indexes; **do not** retain old key aliases. |
| P2-6 | **Research vs operator** — **allow** research to append a new version (history preserved). When current version is `actor: operator`, research prompt includes **deference** (“human set this value; override only with very strong evidence”). No hard write-time block in Program 2. |
| P2-7 | **Hard cutover** — no migration of legacy registry-only MVR values into specialist storage on read; operators refresh networks or wipe storage (same posture as Program 1 flat v1). |
| P2-8 | **MVR post-ship indexes** — maintain existing `bind_index` + `field_index.py` per-field indexes atomically on every unified write (MVR redesign M4). |

---

## Three-layer model (unchanged intent)

```
Canonical (specialist storage)     → versions[] per field (incl. name, employer)
Indexes (entities.json derived)  → bind_index + per-field inverted indexes
Protocol record (entity row)     → id, validation, cache name/employer, summaries
```

---

## Taxonomy bootstrap (CRM)

`network.json` `mvr.bind_fields` defines **which fields are required to bind**.  
`categories.json` `attribute_map` defines **which specialist owns each field**.

CRM reference mappings (committed in `docs/examples/sample-categories.json` + example network refresh):

| Field | Category | Specialist |
|-------|----------|------------|
| `name` | `demographic` | `demographic_specialist` |
| `employer` | `professional` | `professional_specialist` |

Add `name` / `employer` to category **examples** so `attribute_map` is populated on `network create` and sample ontology copy paths.

At runtime, unified write resolves `(category, specialist)` via `ClassificationEngine` / `attribute_map` — not hardcoded Python maps.

---

## Unified write API (Slice 1)

New module (name TBD, e.g. `src/agents/attribute_write.py`):

| Responsibility | Detail |
|----------------|--------|
| Resolve owner | `attribute_map[mvr_field]` → category → storage path |
| Append version | `specialist_fields.append_version` with `actor`: `bind`, `seed_bootstrap`, `research`, `operator` |
| Update cache | Denormalized field values on `RegistryEntity` |
| Update indexes | `bind_index` + rebuild field indexes (or incremental update) |
| Persist | Atomic specialist save + `EntityRegistry._save` |

**Entry points to route (Slice 1):**

- `EntityRegistry.ensure_bound_entity` / `bind_provisional`
- `seed_import.import_seed_file` (via registry bind)
- `target_deliver.bind_provisional_from_scope` (step-2 create-on-deliver)

**Actor kinds (v1):** `bind`, `seed_bootstrap`, `research`, `operator` (operator **writes** ship in Program 3; schema + research deference in Program 2).

---

## Read surfaces (Slice 2)

| Surface | Change |
|---------|--------|
| Default `results[]` | Unchanged — still flat strings; hot path reads entity cache (kept in sync by write API) |
| `provenance=true` | Include **MVR/bind fields** from specialist `versions[]` (remove exclusion in `query_provenance.py`) |
| Admin `GET /status?entity=` | Version timeline for bind fields from specialist storage (not registry-only) |

---

## Research operator deference (Slice 3)

When building research prompts, if target field’s **current** version has `actor.kind == "operator"`, inject a template block (like peer specialist findings) with value, `at`, optional `note`, and instruction to override only with strong evidence. Research may still append a new version; no hard block.

---

## Slice map

| Slice | Spec | Cursor prompt | Scope |
|-------|------|---------------|--------|
| **1** | [`attribute-provenance-program2-slice1.md`](attribute-provenance-program2-slice1.md) | `2026-06-13-2200-attribute-provenance-program2-slice1` | Unified write; taxonomy bootstrap; route bind/seed/create paths; MVR in specialist storage |
| **2** | [`attribute-provenance-program2-slice2.md`](attribute-provenance-program2-slice2.md) | `2026-06-13-2300-attribute-provenance-program2-slice2` | `provenance=true` + admin for bind fields |
| **3** | [`attribute-provenance-program2-slice3.md`](attribute-provenance-program2-slice3.md) | `2026-06-13-2400-attribute-provenance-program2-slice3` | Generalize `bind_provisional_from_scope`; operator research deference prompt; docs + hygiene |

**Order:** 1 → 2 → 3 (each reviewed before the next).

---

## Explicit non-goals (Program 2)

- `bind_versions[]` on entity row
- Hard block preventing research from superseding operator versions
- Admin edit / force re-research endpoints (Program 3)
- Specialist-maintained secondary indices
- Full specialist invoke for MVR validation (inline `validate_entity` remains v1)

---

## Verification

Each slice: `./bin/ci-local` green before review. Slice 1+ uses versioned MVR fixtures in specialist storage for bind fields.

---

*Last updated: June 2026 (requirements locked; Slice 1 queued)*