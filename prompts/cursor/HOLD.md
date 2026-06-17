# Cursor queue

**Program:** Baseball identity — [`docs/plans/baseball-example-program.md`](../../docs/plans/baseball-example-program.md)

**Active (`next/`):**

| Slice | Prompt |
|-------|--------|
| 1200 partial player lookup | [`next/2026-06-18-1200-baseball-partial-player-lookup.md`](next/2026-06-18-1200-baseball-partial-player-lookup.md) — CRM parity for `{player}` on multi-grain routing |

**Paul (June 2026):** **Ship gate** — [`docs/manual-checks/2026-06-17-baseball-identity-ship-gate.md`](../../docs/manual-checks/2026-06-17-baseball-identity-ship-gate.md). Run after **Test 8c**; identity-only (no ontology/specialists). Push when gate **CLEAR**.

**Recently landed (local, ahead of `origin`):**

| Slice | Commit | Notes |
|-------|--------|--------|
| 1000 bind_index fallback | `7ba6dfc` | Step-1 full MVR → `bind_index` for multi-team alias binds |
| 1100 strict grain routing | `bc73c23` | Lookup keys infer grain; fan-out + `EntityQuery.grain` removed |

**In progress / review:** none

**Design locked (routing):** Disjoint bind fields per grain — baseball `{player, team}` → player, `{team}` → team; `infer_grain_from_lookup` (see [`docs/query-grain-router.md`](../../docs/query-grain-router.md)). `DeliveryScope.grain` on step 2. Closed grains: lazy field aliases on 0-hit. **Pending 1200:** partial `{player}` tries field index (CRM parity) before `lookup_incomplete`. **Paul:** re-bootstrap only if root still has pre-1100 `{name, team}` keys.

**Git:** Local commits ahead of `origin`; no push until Paul asks.

---

## Cursor: when you finish a slice

1. `./bin/ci-local` green
2. `done/<slice>/` with `prompt.md` + `output.md`
3. Remove prompt from **`in-progress/`** and **`next/`**
4. **Do not commit or push**
5. Tell Paul **slice ready for review**