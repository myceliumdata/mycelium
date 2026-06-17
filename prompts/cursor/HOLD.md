# Cursor queue

**Program:** Baseball identity — [`docs/plans/baseball-example-program.md`](../../docs/plans/baseball-example-program.md)

**Active (`next/`):**

| Prompt | Scope |
|--------|--------|
| [`next/2026-06-18-0900-registry-source-keys-polish-nits.md`](next/2026-06-18-0900-registry-source-keys-polish-nits.md) | **LOW** — post-1900/2000/2100 polish + CI smoke P15 (P1–P15) |

**Paul (June 2026):** Test 8 bootstrap timing (post-1900) — record `real` when run completes; large regression → consider polish P4.

**In progress / review:** none — 1800 default-seed and 2100 query-grain-router committed locally

**Design locked (slice 3):** Fan-out + per-grain filter · 0-hit pipeline · LLM trigger A · outputs `chosen` / `chosen_grain` / `ambiguous` · 3c cross-grain suggest · optional `EntityQuery.grain` · `delivery.grain` · team queries use `name` key (docs)

**Git:** Local commits ahead of `origin`; no push until Paul asks.

---

## Cursor: when you finish a slice

1. `./bin/ci-local` green
2. `done/<slice>/` with `prompt.md` + `output.md`
3. Remove prompt from **`in-progress/`** and **`next/`**
4. **Do not commit or push**
5. Tell Paul **slice ready for review**