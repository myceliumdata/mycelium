# Cursor queue

**Program:** Storage evolution (specialist → entity) — [`docs/plans/storage-evolution-program.md`](../../docs/plans/storage-evolution-program.md)

**Active (`next/`):** *(empty — bootstrap perf deferred; no optimization slice queued)*

**Last approved:** [`done/2026-06-18-0900-bootstrap-perf-profile-driven/`](done/2026-06-18-0900-bootstrap-perf-profile-driven/) — **Approved** (commit below)

**Prior:** [`done/2026-06-17-2340-specialist-minisql-incremental-writes/`](done/2026-06-17-2340-specialist-minisql-incremental-writes/) — Approved (`c5e5bce`)

**Prior:** [`done/2026-06-17-2355-bootstrap-progress-reporting/`](done/2026-06-17-2355-bootstrap-progress-reporting/) — Approved (`2f9d673`)

**Manual gates (Paul + Grok):** [`docs/manual-checks/2026-06-17-storage-evolution-timing-gates.md`](../../docs/manual-checks/2026-06-17-storage-evolution-timing-gates.md)

| Test | Status |
|------|--------|
| Baseline (pre slice 2) | **12,600 s (~3.5 h)** recorded |
| Test 3 (post slice 2) | **~8,100 s (2 h 15 m) estimated** — update with `time -p` real when done |
| Test 5 (post slice 4) | **~4.5 h est., abandoned** — no gain vs baseline; see timing-gates doc |
| Test 6 (post incremental writes) | **1,202 s (~20 min)** recorded |
| Test 7 (post alias skip rebuild) | **555 s (~9 min)** recorded — **2.2×** vs test 6; further perf deferred |

**Design lock (Paul, June 2026):** Entity persistence = **`EntityStore`** + **`EntityRegistry` API unchanged**. Identity-agent refactor **deferred until full baseball example ships**.

**Prior:** [`done/2026-06-17-2100-specialist-minisql-v1-migrate/`](done/2026-06-17-2100-specialist-minisql-v1-migrate/) — Approved (`179e80d`)

**Git:** Local commits ahead of `origin`; no mid-program push until Paul asks.

---

## Cursor: when you finish a slice

1. `./bin/ci-local` green
2. `done/<slice>/` with `prompt.md` + `output.md`
3. Remove prompt from **`in-progress/`** and **`next/`**
4. **Do not commit or push**
5. Tell Paul **slice ready for review**