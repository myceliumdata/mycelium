# Metering implementation — Slice 10

**Status:** **Ready for Cursor** — Slice 9 locked; single implementation slice  
**Detail:** [`entity-metering-implementation.md`](entity-metering-implementation.md)  
**Cursor prompt:** `prompts/cursor/next/2026-06-09-2100-entity-metering-implementation.md`  
**Design:** [`entity-metering-design-phase9.md`](entity-metering-design-phase9.md)

---

## Paul direction (June 2026)

One slice if feasible. Split only if graph routing forces it (10a production / 10b consumption).

---

## Locked implementation choices (from Q9 + Q10 resolution)

| Topic | Choice |
|-------|--------|
| Stub strictness | Strict gate when `metering.enabled`; bypass via env + disabled default |
| Quote persistence | `quotes.json` on disk |
| Auto-accept | `MYCELIUM_AUTO_ACCEPT_QUOTES=1` |
| Deliverable | Full v1 stub (outcome + quote + gate + stores + tests) |

---

## Non-goals

Payment provider, HTTP 402, wallet, rebate schema (Q9j-B), async quotes (Q9f-B).