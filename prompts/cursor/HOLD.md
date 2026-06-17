# Cursor queue

**Program:** Baseball identity — [`docs/plans/baseball-example-program.md`](../../docs/plans/baseball-example-program.md)

**Active (`next/`):** *empty*

**Paul (June 2026):** **Ship gate** — [`docs/manual-checks/2026-06-17-baseball-identity-ship-gate.md`](../../docs/manual-checks/2026-06-17-baseball-identity-ship-gate.md). Run after **Test 8c**; identity-only (no ontology/specialists). Push when gate **CLEAR**.

**Recently landed (local, ahead of `origin`):**

| Slice | Commit | Notes |
|-------|--------|--------|
| 0800 bootstrap perf | `ff52422` | `save_entity` skips source-key rebuild |
| 0900 polish nits | `a546050` | Router/registry polish + MCP smoke P15 |

**In progress / review:** none

**Design locked (slice 3):** Fan-out + per-grain filter · 0-hit pipeline · LLM trigger A · outputs `chosen` / `chosen_grain` / `ambiguous` · 3c cross-grain suggest · optional `EntityQuery.grain` · `delivery.grain` · team queries use `name` key (docs)

**Git:** Local commits ahead of `origin`; no push until Paul asks.

---

## Cursor: when you finish a slice

1. `./bin/ci-local` green
2. `done/<slice>/` with `prompt.md` + `output.md`
3. Remove prompt from **`in-progress/`** and **`next/`**
4. **Do not commit or push**
5. Tell Paul **slice ready for review**