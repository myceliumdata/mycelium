# Baseball specialist hand test — what should work

**Status:** Ready for Paul (June 2026)  
**Scope:** Identity routing + warehouse specialists shipped through M1c + polish nits (`career_hr`, `birth_date`).  
**Pull vs compute map (while testing):** [§ Warehouse pull vs compute](#warehouse-pull-vs-compute--reference) below.  
**Deeper identity/routing matrix:** [`2026-06-18-baseball-query-hand-test-plan.md`](2026-06-18-baseball-query-hand-test-plan.md)

Use **Claude + MCP** (`query_entity`, `describe_network`, `health_check`) or `./bin/baseball-query` with the same JSON.

---

## Before you start

1. **Live root** with full Lahman bootstrap (not the minimal smoke fixture).
2. **Sync pack changes** without re-bootstrap (~seconds):

   ```bash
   ./bin/refresh-example-network baseball --sync-only
   ```

3. **Point MCP** at the root (`MYCELIUM_NETWORK_ROOT` or registered network name in `networks.json`). Default: `~/mycelium-networks/baseball`.

4. **Discover Hank Aaron’s debut bind** on your root (full Lahman is usually Milwaukee Braves / 1954 — not the Brooklyn 1957 rows in smoke fixtures):

   Ask Claude to run `query_entity` with partial lookup `{"lookup": {"player": "Hank Aaron"}}` and read `debut_team` / `debut_year` from step 2, **or** use the discovery snippet in the identity hand-test doc § setup.

---

## MCP tools (quick reference)

| Tool | Use for |
|------|---------|
| `query_entity` | All queries below — step 1 JSON, then step 2 `{"delivery_id": "d_…"}` |
| `describe_network` | Confirms baseball ontology, record types, routing hints |
| `health_check` | Registry/storage reachable (`ping_query` may still show `degraded` on baseball — known WIP) |

**Two-step pattern:** Step 1 with `lookup` (+ optional `requested_attributes`) → `lookup_resolved` + `delivery_id`. Step 2 with only `delivery_id` → `found` / `assembled` + `results[]`.

---

## Warehouse pull vs compute — reference

Quick map while testing: **pull** = read a stored warehouse value (one row/column); **compute** = Python over warehouse rows (aggregate, compose, or formula). Both specialist paths record `computation.inline` in provenance — the distinction is whether the answer is already stored vs derived.

**Legend:** ✅ works now · 🔜 M2b (manifest generic resolver) · ⏳ later stub / recipe

### Registry / identity (bootstrap, not warehouse specialists)

| Attribute | Type | Source | Status |
|-----------|------|--------|--------|
| `player` | Pull | People display name at bootstrap | ✅ |
| `debut_team` | Pull | Earliest debut season ⋈ Teams | ✅ |
| `debut_year` | Pull | People / Appearances | ✅ |
| `team` | Pull | Teams canonical label (team record type) | ✅ |

Bind-field provenance fix is **M2c** — values are correct today; lineage may still look like research until then.

### Bio (`People`, grain `playerID`)

| Attribute | Type | Lahman | Status |
|-----------|------|--------|--------|
| `birth_date` | Compute (compose) | `birthYear` + `birthMonth` + `birthDay` → `YYYY-MM-DD` | ✅ Aaron → `1934-02-05` |
| `bats` | Pull | `bats` | ⏳ → 🔜 |
| `throws` | Pull | `throws` | ⏳ → 🔜 |
| `birth_city` | Pull | `birthCity` | ⏳ → 🔜 |
| `birth_country` | Pull | `birthCountry` | ⏳ → 🔜 |
| `height` | Pull | `height` | ⏳ → 🔜 |
| `weight` | Pull | `weight` | ⏳ → 🔜 |
| `debut` | Pull | `debut` | ⏳ → 🔜 |
| `final_game` | Pull | `finalGame` | ⏳ → 🔜 |
| `death_date` | Compute (compose) | death Y/M/D columns | ⏳ |

### Batting (`Batting`, grain player-year-stint-team)

**`career_sum`** = `SUM(column) GROUP BY playerID` across all stints (hard-coded per attr today; generic in M2b).

| Attribute | Type | Lahman col | Status |
|-----------|------|------------|--------|
| `career_hr` | Compute (`career_sum`) | `HR` | ✅ Aaron ≈ **755** |
| `career_rbi` | Compute (`career_sum`) | `RBI` | ⏳ → 🔜 |
| `career_hits` | Compute (`career_sum`) | `H` | ⏳ → 🔜 |
| `career_sb` | Compute (`career_sum`) | `SB` | ⏳ |
| `career_avg` | Compute (rate) | `SUM(H) / SUM(AB)` | ⏳ M2b → `N/A` |
| `home_runs`, `rbi`, `at_bats`, `games` | Pull or compute | season-scoped row vs career SUM | ⏳ scope TBD |
| `ops`, `batting_average` | Compute (recipe) | multi-column / season rate | ⏳ |

### Pitching (`Pitching`) — specialist stub

| Attribute | Type | Lahman col | Status |
|-----------|------|------------|--------|
| `career_wins`, `career_losses`, `career_strikeouts`, `career_saves` | Compute (`career_sum`) | `W`, `L`, `SO`, `SV` | ⏳ |
| `career_era`, `era` | Compute (rate) | innings-weighted formula | ⏳ |
| `wins`, `strikeouts`, `walks`, `games_pitched` | Pull (season) | one Pitching row | ⏳ |

### Team season (`Teams`, grain year + team) — specialist stub

| Attribute | Type | Lahman col | Status |
|-----------|------|------------|--------|
| `season_wins`, `season_losses`, `finish_rank` | Pull | `W`, `L`, `Rank` | ⏳ |
| `park`, `attendance`, `runs_scored`, `runs_allowed` | Pull | same-name cols | ⏳ |

Needs team record + season in query — not player specialist path.

### Not warehouse (research / emergent)

| Examples | Why |
|----------|-----|
| Web bio enrichment | Research cache path (clear specialist storage if you expect warehouse) |
| Franchise lineage, career teams list | Cross-table emergent specialists |
| OPS+, WAR, custom mashups | No Lahman column; external source or recipe |

**Hand-test anchors (full Lahman):** `career_hr` ≈ 755, `birth_date` = `1934-02-05` for Hank Aaron (`aaronha01`).

---

## Should work ✅

### Infrastructure

| # | What | Expect |
|---|------|--------|
| I1 | `describe_network` | JSON mentions player/team record types, debut bind keys, baseball specialists |
| I2 | `health_check` | Mostly ok; storage/graph reachable |
| I3 | Warehouse file exists | `warehouse/lahman.sqlite` under network root |

### Identity (unchanged from identity gate)

| # | What | Expect |
|---|------|--------|
| ID1 | Full debut bind → step 2 identity only | `found`; `player`, `debut_team`, `debut_year`, stable `id` |
| ID2 | `{team: "Brooklyn Dodgers"}` (or any canonical Lahman team name) | `lookup_resolved` → step 2 `team` only |
| ID3 | `{player: "Hank Aaron"}` alone | `lookup_resolved` if unique on your root |
| ID4 | Unknown player name | `not_found`; no `create_on_deliver` |
| ID5 | Same `delivery_id` twice | Both deliver; same identity values |
| ID6 | `{"id": "<player uuid>"}` step 1 | `lookup_resolved` → step 2 same uuid |

### Warehouse specialists (new — M1b / M1c)

Use Aaron’s **real** debut bind from your root. Set `provenance: true` on step 1 when you want lineage in step 2.

| # | Attribute | Specialist | Expect step 2 |
|---|-----------|------------|---------------|
| S1 | `career_hr` | `batting_specialist` | Numeric career home runs from Lahman `Batting` (Aaron ≈ **755** on full Lahman) |
| S2 | `birth_date` | `bio_specialist` | `YYYY-MM-DD` from `People` (Aaron → **`1934-02-05`**) |
| S3 | Cache | either | Second deliver (new step 1+2) returns same values without recompute errors |
| S4 | Provenance shape | either | `provenance.entities[0].attributes.<attr>.versions[0]` has `sources[0].kind == "dataset"`, `sources[0].id == "lahman"`, non-empty `computation.inline`, `parameters["lahman.playerID"] == "aaronha01"` |
| S5 | Provenance inline quality | either | Inline is actual Python source of `career_hr()` / `birth_date()` (post-polish: matches executed logic via `inspect.getsource`) |

**Copy-paste query packs** (swap debut bind for your root):

- `examples/networks/baseball/queries/03-career-hr.json`
- `examples/networks/baseball/queries/04-birth-date.json`

Example step-1 shape (fill in your debut bind):

```json
{
  "lookup": {
    "player": "Hank Aaron",
    "debut_team": "<from your root>",
    "debut_year": "<from your root>"
  },
  "requested_attributes": ["career_hr"],
  "provenance": true
}
```

Repeat with `"requested_attributes": ["birth_date"]`.

### Routing / ontology (M1a)

| # | What | Expect |
|---|------|--------|
| R1 | `career_hr` debug / routing | Step 2 touches `batting_specialist` (not CRM `professional_specialist`) |
| R2 | `birth_date` debug / routing | Step 2 touches `bio_specialist` |
| R3 | Unsupported batting attr (e.g. `home_runs` alone) | Graceful `N/A` or non-found — not a crash |
| R4 | Unsupported bio attr (e.g. `height`) | Graceful `N/A` — no web research yet |

### Negative / regression (should still fail cleanly)

| # | What | Expect |
|---|------|--------|
| N1 | `{"lookup": {"name": "Hank Aaron", …}}` old keys | `not_found` |
| N2 | `{"lookup": {"player": "Hank Aaron", "team": "…"}}` legacy bind | `not_found` |
| N3 | Wrong debut year on full bind | `not_found` |
| N4 | Step 2 with raw uuid instead of `delivery_id` | Error / `not_found` |

---

## Should NOT work yet ❌

Don’t fail the build on these — they’re explicitly out of scope:

| What | Why |
|------|-----|
| `height`, `bats`, `throws`, `birth_city`, … | Bio specialist returns `N/A` until **M2b** (see [pull vs compute](#warehouse-pull-vs-compute--reference)) |
| `career_rbi`, `career_hits` | Batting `career_sum` until **M2b** |
| `career_avg`, `ops` | Rate recipes — M2b returns `N/A` |
| `career_wins`, `era`, pitching stats | `pitching_specialist` stub |
| `season_wins`, team season attrs | `team_season_specialist` stub |
| Career team list via query API | Identity is debut bind only — use warehouse SQL (identity doc § H) |
| CRM attrs (`email`, `employer`, …) | Wrong network / stub categories replaced on baseball root |
| `record_type` on `EntityQuery` | Removed — routing is lookup-key shape only |
| Perfect `health_check` ping on baseball | CRM-hardcoded ping may show `degraded` |

---

## Suggested session order (~20–30 min)

1. `describe_network` + `health_check`
2. Resolve Aaron once; note debut bind + `id`
3. **S2 `birth_date`** — raw read, check provenance inline
4. **S1 `career_hr`** — aggregate, check provenance inline
5. **S3** — repeat each; confirm cache
6. Spot-check **ID2** team lookup and **N1** legacy keys
7. Optional: Ty Cobb or another player for ID1 variety

---

## Provenance — what “good” looks like

For each warehouse attr with `provenance: true`:

- **`sources[]`** — dataset pin (`kind: dataset`, `id: lahman`, version / `retrieved_from` from seed)
- **`computation.inline`** — runnable Python that matches what the specialist executed
- **`parameters`** — at least `lahman.playerID` for the resolved entity
- **`actor.specialist`** — `batting_specialist` or `bio_specialist`

This is **computation-centric** lineage ([design doc](../plans/conversations/2026-06-18-computation-centric-provenance.md)) — not table/column citations.

---

## Notes

- **Fixture vs live bind:** Smoke tests use Brooklyn Dodgers / 1957 for a one-row fixture. Full Lahman Aaron uses his real debut franchise/year — always discover on your root.
- **CLI alternative:** `./bin/baseball-query '<json>'` — same payloads as MCP `query_entity`.
- **Parent gates:** Identity ship gate [`2026-06-17-baseball-identity-ship-gate.md`](2026-06-17-baseball-identity-ship-gate.md); timing [`2026-06-17-storage-evolution-timing-gates.md`](2026-06-17-storage-evolution-timing-gates.md).