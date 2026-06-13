# Program 2 — Polish backlog (post Slice 3)

**Status:** Complete (June 2026) — P1–P7 polish shipped locally  
**Cursor prompt:** `prompts/cursor/done/2026-06-13-2500-attribute-provenance-program2-polish/`  
**Program:** [`attribute-provenance-program2.md`](attribute-provenance-program2.md)

---

## Purpose

Non-blocking nits from Grok review of Program 2 Slices 1–3. One polish pass after Program 2 ships — **do not** block Program 3 kickoff, but run before delivery push if possible.

---

## Backlog

| # | Source | Nit | Polish action |
|---|--------|-----|----------------|
| P1 | Slice 3 review | Research prompt: peer block can insert before operator deference | Fix insert order: disambiguation → **operator** → peer → payload; add smoke test |
| P2 | Slice 2 review | `_bind_field_versions` duplicates specialist load in `query_provenance` | Shared read helper; introspection + provenance call it |
| P3 | Slice 1 review | `write_bind_fields` appends version when value unchanged | Skip no-op append when current version value matches; test |
| P4 | Slice 1 review | Multi-specialist writes not atomic (name/employer → two saves) | Best-effort: snapshot before multi-category saves, rollback prior on failure; test with mocked second-save failure |
| P5 | Slice 2 review | `employer` skipped in admin bind status when empty | Show all `mvr.bind_fields` rows (value `None` ok); test empty employer row present |
| P6 | Slice 1 review | `CRM_MVR_FIELD_CATEGORY` hardcoded in bootstrap only | Module docstring + footnote in `attribute-provenance-program2.md` |
| P7 | Slice 1 review | Duplicate bind returns existing row without specialist backfill | Document hard-cutover in `onboarding.md` or CRM README (no lazy migration) |

**Explicitly deferred (not this slice):**

- Extra `mvr.bind_fields` denormalized on entity row beyond `name`/`employer` (schema growth — Program 3+)
- Admin operator edit UI (Program 3)
- `payment_required` smoke (M10 backlog)

---

## Exit criteria

- [x] P1–P7 addressed
- [x] `./bin/ci-local` green
- [x] No Program 3 scope creep

---

*Last updated: June 2026 (Program 2 Slice 1–3 review nits)*