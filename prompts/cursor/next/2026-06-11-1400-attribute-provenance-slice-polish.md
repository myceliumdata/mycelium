# Task: Program 1 — Attribute provenance polish (post Slice 3)

> **BLOCKED until Slice 3 approved** — Do not claim until `prompts/cursor/done/2026-06-11-1300-attribute-provenance-slice3/review.md` is **Approved**. Run **after** Slices 1–3; do not start if any open blocking fix slice exists.

**Read these first (mandatory):**
- `prompts/cursor/WORKFLOW.md`
- [`docs/plans/attribute-provenance-program1-polish.md`](../../docs/plans/attribute-provenance-program1-polish.md) — **nit backlog (P1–P6)**
- [`docs/plans/attribute-provenance-program1.md`](../../docs/plans/attribute-provenance-program1.md)

**Depends on:** Slices 1–3 complete and reviewed.

**Lane:** Hygiene + tests only. Do **not** edit `TODO.md`. No new features.

---

## Objective

Close non-blocking nits from Program 1 reviews. Tighten hard-cutover read paths; remove transitional flat v1 bridges where safe.

---

## Implement (P1–P5)

Work through rows in [`attribute-provenance-program1-polish.md`](../../docs/plans/attribute-provenance-program1-polish.md):

| # | Action |
|---|--------|
| **P1** | Document `ensure_versioned_for_write` flat-pending wrap; add smoke test for behavior |
| **P2** | Remove `entity_growth` flat `researched_at` fallback |
| **P3** | Remove duplicate `pending` branch in `_persist_field_version` (`research.py`) |
| **P4** | Add smoke test: P1-11 in-place pending retry preserves `started_at` |
| **P5** | Remove flat v1 fallbacks from `specialist_fields` read helpers (`current_value`, `field_has_value`, `current_status`, etc.) — versioned-only |

**P6–P10:** Slice 2/3 review rows in polish doc (P7–P10 from Slice 2; P6 from Slice 3 if any).

---

## Constraints

- Do not change versioned storage shape or P1-10/P1-11 semantics.
- Do not add `QueryResponse` / operator-write / Program 2 scope.
- If removing P5 fallbacks breaks tests, update fixtures to versioned-only (no reintroducing flat blobs).
- `./bin/ci-local` green.

---

## Governance (mandatory)

- **Do not edit `TODO.md`.**
- In `output.md`, add **"For Grok + Paul"**: mark Program 1 polish done; Program 1 complete.
- **No commit before review.**

---

## Deliverables

Move to `prompts/cursor/done/2026-06-11-1400-attribute-provenance-slice-polish/` with `prompt.md`, `output.md`, `./bin/ci-local` result.

---

## Review gate

Grok reviews → Program 1 closeout; then Program 2 design may start.