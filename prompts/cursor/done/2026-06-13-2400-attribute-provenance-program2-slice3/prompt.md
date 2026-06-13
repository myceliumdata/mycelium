# Task: Program 2 — MVR / entity storage Slice 3 (polish)

> **READY** — Move to `in-progress/` before starting.

**Read these first (mandatory):**
- `prompts/cursor/WORKFLOW.md`
- [`docs/plans/attribute-provenance-program2.md`](../../docs/plans/attribute-provenance-program2.md) — program context + locked decisions (especially P2-6)
- [`docs/plans/attribute-provenance-program2-slice3.md`](../../docs/plans/attribute-provenance-program2-slice3.md) — **locked spec**
- [`docs/plans/attribute-provenance-and-storage.md`](../../docs/plans/attribute-provenance-and-storage.md) — three-layer model
- [`src/agents/attribute_write.py`](../../src/agents/attribute_write.py) — unified write (Slice 1)
- [`src/tools/research.py`](../../src/tools/research.py) — `build_research_prompts`

**Prerequisite:** Slice 2 approved — see [`done/2026-06-13-2300-attribute-provenance-program2-slice2/review.md`](../done/2026-06-13-2300-attribute-provenance-program2-slice2/review.md) (Approved).

**Lane:** Cursor implements code + tests only. Do **not** edit `TODO.md`. No admin operator edit UI (Program 3).

---

## Objective

Close Program 2: fully dynamic `mvr.bind_fields` on create-on-deliver, **research operator deference** in prompts, post-ship docs and hygiene.

**Locked (P2-6):** Research **may** append a new version when current is `actor: operator`; prompt must **defer** to operator value unless evidence is very strong.

---

## Implement

Follow [`attribute-provenance-program2-slice3.md`](../../docs/plans/attribute-provenance-program2-slice3.md) exactly:

### 1 — Dynamic bind fields

- `src/agents/target_deliver.py` — `bind_provisional_from_scope`: iterate `load_mvr().bind_fields`, collect values from scope lookup, pass to `ensure_entity_bind_fields` (no name/employer-only assumptions in the path).
- `src/agents/attribute_write.py` — where feasible, generalize cache/index helpers for arbitrary bind fields (Slice 1 nits N3: `_apply_cache_field` / `make_bind_key` still CRM-shaped — document limits or extend if low risk).
- Tests: create-on-deliver with scope lookup covering all `mvr.bind_fields`.

### 2 — Research operator deference

- `src/tools/research.py` / `build_research_prompts`: when target field’s **current** version has `actor.kind == "operator"`, inject template block with value, `at`, optional `note`.
- New `research/_operator_deference.j2` (or extend existing system template).
- Instruction: prefer keeping operator value; override only with very strong evidence; if uncertain return `na`.
- **No write-time block** — research may still append `v2`.
- Tests: fixture with operator version → prompt contains operator value; research append still works.

### 3 — Optional smoke

- Target-path `payment_required` test if low cost (deferred from M10); skip if flaky.

### 4 — Docs

- `examples/networks/crm/README.md` — MVR values in specialist storage after Program 2.
- `docs/onboarding.md` — one line on taxonomy-owned bind fields.
- `docs/plans/next-chunk-prep.md` — Program 2 complete pointer.
- `docs/plans/attribute-provenance-and-storage.md` — mark Program 2 read/write surfaces done.

### 5 — Hygiene

- Grep living docs for stale “registry-owned MVR only” / `bind_versions` references; fix or remove.
- `storage_strategy.json` consistency across example network refresh if drift found.

---

## Constraints

- **Do not touch:** admin operator edit endpoints (Program 3), `query_provenance.py` / introspection read paths (Slice 2 — unless hygiene-only comment fixes).
- **No** `bind_versions[]` on entity row.
- Keep **`./bin/ci-local` green**

---

## Deliverables

Move this file to `prompts/cursor/done/2026-06-13-2400-attribute-provenance-program2-slice3/` with:
- `prompt.md` (copy of this file)
- `output.md` — summary + **For Grok + Paul** section
- Run `./bin/ci-local` and record result in `output.md`

---

## Review gate

Grok reviews before Program 3 kickoff. Optional Paul manual gate checklist after this slice.