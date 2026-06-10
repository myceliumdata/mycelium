# Seed elimination phase — slice map (14–18)

**Status:** Queued for Cursor (June 2026) — prompts in `prompts/cursor/next/2026-06-10-1400` … `1800`  
**Depends on:** Slice 13 (uuid4 + `entities.json` persistence)  
**Goal:** Remove runtime reads of `seed.json`; bootstrap import only when file exists.

---

## Principle

| Layer | Role |
|-------|------|
| **`seed.json`** (optional, committed) | Static bootstrap **fixture** — not read at query time |
| **`refresh-example-network`** | Copies example files; if `seed.json` present → import into `entities.json` |
| **`entities.json`** | Runtime canonical entity store |
| **Resolution** | Registry only |

---

## Slice 14 — Bootstrap import

**Spec:** [`entity-seed-elimination-slice14.md`](entity-seed-elimination-slice14.md)

- `network/seed_import.py` — `import_seed_file(path) -> int`
- `refresh_example_network` calls import when `root/seed.json` exists
- `create_network` imports after copying seed (optional `--seed`)

---

## Slice 15 — Registry-only resolution

**Spec:** [`entity-seed-elimination-slice15.md`](entity-seed-elimination-slice15.md)

- Remove seed branch from `resolve_entity` / `resolve_entity_for_lookup`
- Suggestions scan `entities.json`
- `lookup_entities_by_key` helper on registry

---

## Slice 16 — Context + runtime

**Spec:** [`entity-seed-elimination-slice16.md`](entity-seed-elimination-slice16.md)

- `ContextBuilder` resolves bind rows from registry by id
- Remove seed from `refresh_runtime_from_disk`, admin bootstrap
- Simplify `research_gate` (all matches are registry rows)

---

## Slice 17 — Delete runtime seed module

**Spec:** [`entity-seed-elimination-slice17.md`](entity-seed-elimination-slice17.md)

- Delete `agents/seed.py`
- Remove legacy `mycelium seed` CLI subcommand
- `storage/core.py` — drop SQLite seed_from_file seed coupling
- Test fixture helper `import_seed_file` replaces `get_seed_data`

---

## Slice 18 — Admin UI + docs

**Spec:** [`entity-seed-elimination-slice18.md`](entity-seed-elimination-slice18.md)

- Admin overview: **Entities** count only (remove Seed line)
- API: deprecate `seed_people_count` → use `registry_entity_count`
- README / architecture / MCP policy strings

---

## Exit criteria (phase)

- [ ] No `agents.seed` imports in `src/`
- [ ] `refresh-example-network crm` populates `entities.json` from seed fixture
- [ ] Empty network (no seed.json) works — Paul Murphy bind arc
- [ ] Full `pytest` green
- [ ] Admin UI shows entities, not seed