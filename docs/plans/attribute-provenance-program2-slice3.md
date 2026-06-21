# Program 2 — Slice 3: Polish (dynamic bind fields + research deference)

**Status:** Shipped
**Program:** [`attribute-provenance-program2.md`](attribute-provenance-program2.md)  
**Depends on:** Slices 1–2 approved  
**Cursor prompt:** `prompts/cursor/done/2026-06-13-2400-attribute-provenance-program2-slice3/`

---

## Objective

Generalize bind/create for arbitrary `mvr.bind_fields`, add **research operator deference** in prompts, close post-ship hygiene and docs.

---

## Implement

### 1 — `target_deliver.bind_provisional_from_scope`

- Fully dynamic: iterate `load_mvr().bind_fields`, read values from scope lookup, pass dict to unified write (no name/employer-only loop).

### 2 — Research operator deference

- `src/tools/research.py` / `build_research_prompts`: when current version for a target field has `actor.kind == "operator"`, inject template block (new `research/_operator_deference.j2` or extend system template) with value, `at`, `note`.
- Instruction: prefer keeping operator value unless evidence is very strong; if uncertain return `na`.
- **Allow** append of new research version (P2-6) — no write-time block.
- Tests: fixture operator version → prompt contains operator value; research can still append `v2`.

### 3 — Optional smoke

- Target-path `payment_required` test if low cost (deferred from M10); skip if flaky.

### 4 — Example networks + docs

- `examples/networks/crm-seeded/README.md` — note MVR storage in specialist files after Program 2.
- `docs/onboarding.md` — one line on taxonomy-owned bind fields.
- `next-chunk-prep.md` — Program 2 complete pointer.
- Program 2 manual gate doc (optional checklist) if Paul wants hands-on verification.

### 5 — Hygiene

- Grep for stale “registry-owned MVR only” / `bind_versions` references in living docs.
- `storage_strategy.json` consistency across example network refresh.

---

## Do NOT

- Admin operator edit UI (Program 3).
- `bind_versions[]` on entity row.

---

## Verification

`./bin/ci-local` green. Paul manual gate optional before Program 3 kickoff.