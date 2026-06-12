# Task: Program 1 — Attribute provenance polish (post Slice 3)

> **READY** — Slices 1–3 approved. Move to `in-progress/` before starting.

**Read these first (mandatory):**
- `prompts/cursor/WORKFLOW.md`
- [`docs/plans/attribute-provenance-program1-polish.md`](../../docs/plans/attribute-provenance-program1-polish.md) — **nit backlog (P1–P12)**
- [`docs/plans/attribute-provenance-program1.md`](../../docs/plans/attribute-provenance-program1.md)

**Depends on:** Slices 1–3 complete and reviewed.

**Lane:** Hygiene + tests only. Do **not** edit `TODO.md`. No new features.

---

## Objective

Close non-blocking nits from Program 1 reviews. Tighten hard-cutover read paths; remove transitional flat v1 bridges where safe.

---

## Implement (P1–P12)

Work through every row in [`attribute-provenance-program1-polish.md`](../../docs/plans/attribute-provenance-program1-polish.md):

| # | Source | Action |
|---|--------|--------|
| **P1** | Slice 1 | Document `ensure_versioned_for_write` flat-pending wrap; add smoke test |
| **P2** | Slice 1 | Remove `entity_growth` flat `researched_at` fallback |
| **P3** | Slice 1 | Remove duplicate `pending` branch in `_persist_field_version` (`research.py`) |
| **P4** | Slice 1 | Add smoke test: P1-11 in-place pending retry preserves `started_at` |
| **P5** | Slice 1 | Remove flat v1 fallbacks from `specialist_fields` read helpers — versioned-only |
| **P7** | Slice 2 | `_analyze_storage`: versioned-only counts or validate before count |
| **P8** | Slice 2 | Smoke test: flat v1 on entity drill-down fails loud (`build_network_status` / `/status`) |
| **P9** | Slice 2 | Remove dead no-op branch in `_entity_field_statuses` |
| **P10** | Slice 2 | Style admin `.version-history` (minimal CSS or reuse disclosure styles) |
| **P11** | Slice 3 | Replace private `CategoryTree._data` access in `query_provenance` or document |
| **P12** | Slice 3 | Multi-match provenance smoke test (`provenance.entities` length > 1) |

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