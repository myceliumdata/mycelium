# Manual checks — Baseball example program post-program gate

**Status:** ✅ **CLEAR** (2026-06-21) — Paul program sign-off; live gate **27/27** on optimized Lahman root

**Context:** Baseball example program M1–M14 + bootstrap perf (`2280`) + polish capstone (`2350`). Framework warehouse stat hierarchy shipped; full 27-table warehouse ingest; live gate catalog at **27** scenarios.

**Prereqs:** Framework repo; `uv sync`; live root `~/mycelium-networks/baseball` refreshed with current `main`; `.env` keys for derive phase.

---

## What the program proves

- **Player + team** record types on generic framework (debut bind, MVR, `bootstrap_only`)
- **Warehouse factory** — manifest domains (batting, pitching, bio, fielding, team_season), computation-centric provenance
- **Product specialists** — roster (scope-aware cache), franchise
- **Derive-on-miss** — batting LLM codegen + sandbox (`career_avg`, `ops`, M4b intent cache)
- **Framework middle tier** — `WarehousePlayerStatSpecialist` / `WarehouseTeamStatSpecialist`; thin baseball pack subclasses
- **Live gate** — `./bin/gate-live baseball` on real Lahman (not CI)

---

## Pre-flight

```bash
cd /path/to/mycelium
./bin/ci-local
```

**Pass:** smoke green (648+ at sign-off).

---

## Check 1 — Bootstrap timing (demo viability)

```bash
time ./bin/refresh-example-network baseball --yes --no-default
```

**Pass (Paul, 2026-06-21):** **3m 34s** wall clock post-`2280` deferred index rebuild + `player_debut` (23,596 player binds; 23,837 entities). Pre-optimization baseline on same machine: **29m 11s**. Recorded as **Test 10** in [`2026-06-17-storage-evolution-timing-gates.md`](2026-06-17-storage-evolution-timing-gates.md).

---

## Check 2 — Live gate (required sign-off)

```bash
./bin/gate-live baseball
```

**Pass:** **27/27** scenarios (Paul, 2026-06-21). Derive phase needs `OPENAI_API_KEY`, `MYCELIUM_COMPUTATION_CODEGEN_MODEL`, `MYCELIUM_INTENT_NORMALIZATION_MODEL`.

**Anchor fix at sign-off:** `bb-field-01` — `fielder_career_games` / `fielder_career_putouts` corrected to Lahman **Fielding** sums (3020 / 7436), not Batting `G` (3298). Commit `da5b006`.

---

## Check 3 — Operator smoke (fast path)

```bash
./bin/smoke-baseball-e2e --with-pytest
```

**Pass:** minimal fixture + specialist smokes green without live root.

---

## Deferred (not program blockers)

| Item | Notes |
|------|--------|
| Multi-domain derive (pitching/fielding `derive_on_miss`) | Queued: `prompts/cursor/next/2026-06-21-2400-baseball-multi-domain-derive-live-gate.md` |
| Bio + Tavily research hybrid | Queued: `prompts/cursor/next/2026-06-21-2410-baseball-bio-research-specialist.md` |
| `bin/smoke-baseball-e2e --full` | Timing-scale Lahman smoke; live gate covers real root |
| Website / public demo | [`TODO.md`](../../TODO.md) — queue in `mycelium-website` |

---

## References

- Program design: [`docs/plans/baseball-example-program.md`](../plans/baseball-example-program.md)
- Live gate ops: [`2026-06-20-live-gate-program.md`](2026-06-20-live-gate-program.md)
- Specialist hierarchy: [`docs/architecture/whys/specialist-class-hierarchy.md`](../architecture/whys/specialist-class-hierarchy.md)
- Cursor slices: `prompts/cursor/done/2026-06-20-*` (M9–M14, 2280, 2350)