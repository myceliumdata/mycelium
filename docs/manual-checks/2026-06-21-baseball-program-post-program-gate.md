# Manual checks — Baseball example program post-program gate

**Status:** ✅ **CLEAR** — Paul sign-off **2026-06-21** (program); **v1 extension 2026-06-21** (34/34 live gate, all search providers)

**Context:** Baseball example program M1–M14 + bootstrap perf (`2280`) + polish capstone (`2350`). Follow-on slices **`2400`** (multi-domain derive) and **`2410`** (bio research) shipped same program window. Live gate catalog: **34** scenarios.

**Prereqs:** Framework repo; `uv sync`; live root `~/mycelium-networks/baseball`; `.env` keys per phase (derive, bio research).

**Exploration docs:** [`docs/examples/baseball/`](../examples/baseball/getting-started.md)

---

## What the program proves

- **Player + team** record types on generic framework (debut bind, MVR, `bootstrap_only`)
- **Warehouse factory** — manifest domains (batting, pitching, bio, fielding, team_season), computation-centric provenance
- **Product specialists** — roster (scope-aware cache), franchise
- **Derive-on-miss** — batting, pitching, fielding LLM codegen + sandbox; M4b intent cache
- **Bio research** — `research_on_miss` + `WarehouseResearchStatSpecialist` (`primary_nickname`)
- **Pluggable web search** — `SEARCH_PROVIDER` tavily | exa | brave (Paul validated all providers on live gates)
- **Framework middle tier** — `WarehousePlayerStatSpecialist` / `WarehouseTeamStatSpecialist` / `WarehouseResearchStatSpecialist`
- **Live gate** — `./bin/gate-live baseball` on real Lahman (not CI); unified auto-refresh

---

## Pre-flight

```bash
cd /path/to/mycelium
./bin/ci-local
```

**Pass:** smoke green (669+ at v1 extension).

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

**Pass (Paul, 2026-06-21):** **34/34** scenarios on optimized Lahman root.

| Phase | Keys |
|-------|------|
| `derive` | `OPENAI_API_KEY`, `MYCELIUM_COMPUTATION_CODEGEN_MODEL`, `MYCELIUM_INTENT_NORMALIZATION_MODEL` |
| `bio_research` | `OPENAI_API_KEY`, active search provider key (`SEARCH_PROVIDER` + `TAVILY_API_KEY` / `EXA_API_KEY` / `BRAVE_SEARCH_API_KEY`) |

Paul re-validated **all four example networks** with Tavily, Exa, and Brave search providers (2026-06-21).

**Anchor fix at initial sign-off:** `bb-field-01` — Fielding sums (commit `da5b006`).

---

## Check 3 — Operator smoke (fast path)

```bash
./bin/smoke-baseball-e2e --with-pytest
```

**Pass:** minimal fixture + specialist smokes green without live root.

---

## Deferred (not v1 blockers)

| Item | Notes |
|------|--------|
| `bin/smoke-baseball-e2e --full` | Timing-scale Lahman smoke; live gate covers real root |
| Website / public demo | [`TODO.md`](../../TODO.md) — `mycelium-website` |
| Peer-aware analytic orchestration | Design locked; v1.1 |
| `bb-bio-research-02` synonym gate | Follow-on |

---

## References

- Program design: [`docs/plans/baseball-example-program.md`](../plans/baseball-example-program.md)
- Live gate ops: [`2026-06-20-live-gate-program.md`](2026-06-20-live-gate-program.md)
- Specialist hierarchy: [`docs/architecture/whys/specialist-class-hierarchy.md`](../architecture/whys/specialist-class-hierarchy.md)
- Cursor slices: `prompts/cursor/done/2026-06-20-*`, `2026-06-21-2400`, `2026-06-21-2410`, `2026-06-21-2500`, `2026-06-21-2510`