# Cursor queue

**Program:** Baseball identity — [`docs/plans/baseball-example-program.md`](../../docs/plans/baseball-example-program.md)

**Active (`next/`):** *empty*

**Paul (June 2026):** **Ship gate ✅ CLEAR (WIP)** — [`docs/manual-checks/2026-06-17-baseball-identity-ship-gate.md`](../../docs/manual-checks/2026-06-17-baseball-identity-ship-gate.md) signed off 2026-06-18. Identity + routing shipped; baseball example still WIP (stub categories, research attrs). **Push when Paul asks.**

**Recently landed (local, ahead of `origin`):**

| Slice | Commit | Notes |
|-------|--------|--------|
| 1000 bind_index fallback | `7ba6dfc` | Step-1 full MVR → `bind_index` for multi-team alias binds |
| 1100 strict grain routing | `bc73c23` | Lookup keys infer grain; fan-out + `EntityQuery.grain` removed |
| 1200 partial player lookup | `286811e` | `{player}` only delegates to single-grain resolver (CRM parity) |

**In progress / review:** none

**Manual gate findings (Paul, June 2026):**

- **Canonical team on deliver:** alias team in lookup (e.g. Milwaukee) → step 2 shows primary bind team (Atlanta). Registry-correct, UX TBD.
- **Q15:** `baseball-query` loads repo `.env` for lazy alias LLM (`OPENAI_API_KEY`).
- **Provenance:** works mechanically; baseball attrs today are CRM research lineage — re-examine with ontology ([`TODO.md`](../../TODO.md)).
- **MCP:** four servers via `uv run --directory …`; baseball `health_check` ping_query degraded expected.

**Design locked (routing):** Disjoint bind fields per grain — baseball `{player, team}` → player, `{team}` → team; partial `{player}` tries field index then incomplete (slice 1200, CRM parity). See [`docs/query-grain-router.md`](../../docs/query-grain-router.md). **Paul:** re-bootstrap only if root still has pre-1100 `{name, team}` keys.

**Git:** Local commits ahead of `origin`; no push until Paul asks.

---

## Cursor: when you finish a slice

1. `./bin/ci-local` green
2. `done/<slice>/` with `prompt.md` + `output.md`
3. Remove prompt from **`in-progress/`** and **`next/`**
4. **Do not commit or push**
5. Tell Paul **slice ready for review**