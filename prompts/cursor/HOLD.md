# Cursor queue

**Active:** *(empty)*

**Last approved:** [`done/2026-06-14-1450-suggestion-suggested-lookup-rename/`](done/2026-06-14-1450-suggestion-suggested-lookup-rename/) — **Approved**

**Prior:** [`1440`](done/2026-06-14-1440-employer-fuzzy-suggestion-shape/) — Approved + polish nits (nits closed in 1450)

**Design:** [`docs/plans/fuzzy-lookup-policy.md`](../../docs/plans/fuzzy-lookup-policy.md) — alias/prefix upgrades still on TODO

**Process:** Program 2 manual gate. **Restart MCP** for `1430`–`1450`.

**Git:** **Shipped** `fc18486` to `origin/main` (2026-06-14). 52 commits (Program 2 + fuzzy lookup `1430`–`1450` + admin polish).

---

## Cursor: when you finish a slice

1. `./bin/ci-local` green
2. `done/<slice>/` with `prompt.md` + `output.md`
3. Remove prompt from **`in-progress/`** and **`next/`**
4. **Do not commit or push**
5. Tell Paul **slice ready for review**