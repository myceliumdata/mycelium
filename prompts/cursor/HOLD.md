# Cursor queue

**Program:** Baseball identity — [`docs/plans/baseball-example-program.md`](../../docs/plans/baseball-example-program.md)

**Active (`next/`):** *empty*

**Paul (June 2026):** **Ship gate ✅ CLEAR (WIP)** — [`docs/manual-checks/2026-06-17-baseball-identity-ship-gate.md`](../../docs/manual-checks/2026-06-17-baseball-identity-ship-gate.md) signed off 2026-06-18. Identity + routing shipped; baseball example still WIP (stub categories, research attrs). **Push when Paul asks.**

**Recently landed (local, ahead of `origin`):**

| Slice | Commit | Notes |
|-------|--------|--------|
| 1000 bind_index fallback | `7ba6dfc` | Step-1 full MVR → `bind_index` when field index misses (superseded for baseball by 1800 debut bind) |
| 1100 strict record-type routing | `bc73c23` | Lookup keys infer record type; fan-out + `EntityQuery.grain` removed |
| 1200 partial player lookup | `286811e` | `{player}` only delegates to single-record-type resolver (CRM parity) |
| 1800 record_type + debut bind | `8ccd389` | `mvr.record_types`, `new_records`; baseball `player`+`debut_team`+`debut_year` |

**In progress / review:** none

**Manual gate findings (Paul, June 2026):**

- **Player identity:** one debut bind per `lahman.playerID` at bootstrap (slice 1800); career teams live in warehouse, not `bind_index`.
- **Q15:** `baseball-query` loads repo `.env` for lazy alias LLM (`OPENAI_API_KEY`).
- **Provenance:** works mechanically; baseball attrs today are CRM research lineage — re-examine with ontology ([`TODO.md`](../../TODO.md)).
- **MCP:** four servers via `uv run --directory …`; baseball `health_check` ping_query degraded expected.

**Design locked (routing):** Disjoint bind fields per record type — baseball `{player, debut_team, debut_year}` → player, `{team}` → team; partial `{player}` resolves on field index or `not_found` when `bootstrap_only` (slice 1200/1800). See [`docs/query-record-type-router.md`](../../docs/query-record-type-router.md). **Paul:** re-bootstrap full Lahman roots after slice 1800 (old `player`+`team` entity stores incompatible).

**Git:** Local commits ahead of `origin`; no push until Paul asks.

---

## Cursor: when you finish a slice

1. `./bin/ci-local` green
2. `done/<slice>/` with `prompt.md` + `output.md`
3. Remove prompt from **`in-progress/`** and **`next/`**
4. **Do not commit or push**
5. Tell Paul **slice ready for review**