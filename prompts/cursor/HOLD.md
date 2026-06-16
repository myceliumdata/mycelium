# Cursor queue

**Program:** Storage evolution (specialist → entity) — [`docs/plans/storage-evolution-program.md`](../../docs/plans/storage-evolution-program.md)

**Active (`next/`):**

1. `next/2026-06-17-1900-specialist-optimize-storage-check.md` — slice 1: threshold `optimize_storage()`
2. `next/2026-06-17-2100-specialist-minisql-v1-migrate.md` — slice 2: `minisql_v1` specialist migration

**Held until timing test 3 (Paul + Grok):**

- `hold/2026-06-17-2300-entity-registry-storage-evolution.md` — slice 4: entity store batch save + minisql

**Manual gates (Paul + Grok):** [`docs/manual-checks/2026-06-17-storage-evolution-timing-gates.md`](../../docs/manual-checks/2026-06-17-storage-evolution-timing-gates.md) — timing test 3 after slice 2; timing test 5 after slice 4.

**Last approved:** [`done/2026-06-17-1800-specialist-agent-class/`](done/2026-06-17-1800-specialist-agent-class/) — **Approved** (local commits `2a639d1`, `d29361b`)

**Prior shipped to `origin/main`:** Program 2 + fuzzy lookup `1430`–`1450` (`fc18486`, 2026-06-14)

**Git:** `main` is ahead of `origin` (SpecialistAgent + baseball Lahman work). No mid-program push until Paul asks.

---

## Cursor: when you finish a slice

1. `./bin/ci-local` green
2. `done/<slice>/` with `prompt.md` + `output.md`
3. Remove prompt from **`in-progress/`** and **`next/`**
4. **Do not commit or push**
5. Tell Paul **slice ready for review**