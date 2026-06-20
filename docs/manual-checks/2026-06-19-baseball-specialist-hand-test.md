# Baseball specialist hand test — what should work

**Status:** Ready for Paul (June 2026)  
**Scope:** Identity routing + warehouse specialists through **M4b** (`career_hr`, `career_rbi`, `career_hits`, `career_avg` derive, intent synonym dedup, `birth_date`, `bats` when column present; registry bind provenance).
**Pull vs compute map (while testing):** [§ Warehouse pull vs compute](#warehouse-pull-vs-compute--reference) below.  
**Deeper identity/routing matrix:** [`2026-06-18-baseball-query-hand-test-plan.md`](2026-06-18-baseball-query-hand-test-plan.md)

Use **Claude + MCP** (`query_entity`, `describe_network`, `health_check`) or `./bin/baseball-query` with the same JSON.

**Automated regression:** `./bin/gate-live baseball` (opt-in; deployed root + `.env`; derive cache auto-clears). Reload Lahman first when pack specialists change: `./bin/refresh-example-network baseball --yes` or `--sync-only`. See [`2026-06-20-live-gate-program.md`](2026-06-20-live-gate-program.md).

**CLI:** Step 2 must use `--network baseball` (same as step 1); stderr prints a copy-paste hint after step 1.

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

**Legend:** ✅ works now · ⏳ later stub / recipe

### Registry / identity (bootstrap, not warehouse specialists)

| Attribute | Type | Source | Status |
|-----------|------|--------|--------|
| `player` | Pull | People display name at bootstrap | ✅ |
| `debut_team` | Pull | Earliest debut season ⋈ Teams | ✅ |
| `debut_year` | Pull | People / Appearances | ✅ |
| `team` | Pull | Teams canonical label (team record type) | ✅ |

Bind-field provenance: `actor.kind` is **`registry`** or **`seed_bootstrap`** (not `research`). If an old factory stub left `research` versions, delete `agents/player_identity/storage.json` and re-deliver.

### Bio (`People`, grain `playerID`)

| Attribute | Type | Lahman | Status |
|-----------|------|--------|--------|
| `birth_date` | Compute (compose) | `birthYear` + `birthMonth` + `birthDay` → `YYYY-MM-DD` | ✅ Aaron → `1934-02-05` |
| `bats` | Pull | `bats` | ✅ when `People.bats` present |
| `throws` | Pull | `throws` | ✅ when column present |
| `birth_city` | Pull | `birthCity` | ✅ when column present |
| `birth_country` | Pull | `birthCountry` | ✅ Aaron → `USA`; live gate `bb-bio-01` |
| `height` | Pull | `height` | ✅ Aaron → **72**; live gate `bb-bio-01` |
| `weight` | Pull | `weight` | ✅ Aaron → **180**; live gate `bb-bio-01` |
| `debut` | Pull | `debut` | ✅ when column present (may be empty → `N/A`) |
| `final_game` | Pull | `finalGame` | ✅ Aaron → `1976-10-03` |
| `death_date` | Compute (compose) | death Y/M/D columns | ✅ Aaron → `2021-01-22` |

### Batting (`Batting`, grain player-year-stint-team)

**`career_sum`** = `SUM(column) GROUP BY playerID` across all stints (manifest-driven).

| Attribute | Type | Lahman col | Status |
|-----------|------|------------|--------|
| `career_hr` | Compute (`career_sum`) | `HR` | ✅ Aaron ≈ **755** |
| `career_rbi` | Compute (`career_sum`) | `RBI` | ✅ |
| `career_hits` | Compute (`career_sum`) | `H` | ✅ |
| `career_sb` | Compute (`career_sum`) | `SB` | ⏳ alias not in manifest yet |
| `career_avg` | Compute (derive) | `SUM(H) / SUM(AB)` via LLM codegen + sandbox (M3) | ✅ Aaron ≈ **0.305** on full Lahman; fixture smoke **0.500** |
| `home_runs`, `rbi`, `at_bats`, `games` | Pull or compute | season-scoped row vs career SUM | ✅ M9 scope on step 1 (`yearID`) |
| `ops` | Compute (derive on miss, M4) | free-form label via LLM codegen | ✅ fixture smoke **0.900** (mocked); live optional |
| `batting_average` | Compute (derive on miss) | synonym of career rate — intent slug `career_batting_average` (M4b) | ✅ Aaron **0.305**; cache hit after `career_avg` |

### Pitching (`Pitching`) — `pitching_specialist` (M5)

| Attribute | Type | Lahman col | Status |
|-----------|------|------------|--------|
| `career_wins`, `career_losses`, `career_strikeouts`, `career_saves` | Compute (`career_sum`) | `W`, `L`, `SO`, `SV` | ✅ smoke + live gate `bb-pitch-01` / `bb-pitch-02` |
| `career_era` | Compute (rate) | innings-weighted `9*ER/IP` | ✅ smoke **3.000** fixture; live gate `bb-pitch-03` (Nolan Ryan ≈ **3.194**) |
| `era` | Compute (rate) | season-scoped | ⏳ optional alias (career_era ships) |
| `wins`, `strikeouts`, `walks`, `games_pitched` | Pull (season) | one Pitching row | ⏳ optional season aliases |

### Team season (`Teams`, grain year + team) — `team_season_specialist` (M6)

| Attribute | Type | Lahman col | Status |
|-----------|------|------------|--------|
| `season_wins`, `season_losses`, `finish_rank` | Pull (`team_latest_column` or `season_column` with scope) | `W`, `L`, `Rank` | ✅ smoke + live gate `bb-team-01` / `bb-team-02` |
| `park`, `runs_scored`, `runs_allowed` | Pull | same-name cols | ✅ manifest aliases |
| `attendance` | Pull | `Teams` col when present | ⏳ optional alias (not in manifest) |

Pass `scope: {"yearID": "1957"}` on step 1 for season-scoped team stats (M9).

### Not warehouse (research / emergent)

| Examples | Why |
|----------|-----|
| Web bio enrichment | Research cache path (clear specialist storage if you expect warehouse) |
| Franchise lineage, career teams list | Cross-table emergent specialists |
| OPS+, WAR, custom mashups | No Lahman column; external source or recipe |

**Hand-test anchors (full Lahman):** `career_hr` ≈ 755, `career_rbi` ≈ 2297, `career_hits` ≈ 3771, `career_avg` ≈ **0.305**, `birth_date` = `1934-02-05` for Hank Aaron (`aaronha01`).

---

## M2 extended gate (live Lahman)

Use partial lookup `{"player": "Hank Aaron"}` if unique on your root. Always step 1 → step 2 with `delivery_id`. Set `provenance: true` on step 1 when checking lineage.

| # | What | Step 1 `requested_attributes` | Expect step 2 |
|---|------|----------------------------------|---------------|
| 0 | Sync pack | `./bin/refresh-example-network baseball --sync-only` | Specialists + manifest updated |
| 1 | Warehouse provenance refresh | `["career_hr", "birth_date"]` | M2b inline (`career_sum`, `people_birth_date`); `parameters.warehouse` |
| 2 | New career stats | `["career_rbi", "career_hits"]` | **2297**, **3771**; `parameters.attribute` + batting `column` |
| 3 | Six-attr multi-specialist | `["debut_team", "debut_year", "career_hr", "career_rbi", "career_hits", "birth_date"]` | All anchors; bind `registry` current; warehouse dataset + computation |
| 4 | Bio raw columns | `["bats", "throws", "birth_city"]` | `R`, `R`, `Mobile` (typical); `people_column` inline |
| 5 | Cache hit | Repeat **#3** without clearing storage | Same values; provenance version ids / timestamps unchanged |
| 6 | Manifest (optional) | `describe_network` | `warehouse_manifest.present`; aliases on disk in `warehouse_manifest.json` |
| 7 | Negative | `{"lookup": {"player": "XYZZY"}}` | `not_found` — no crash |

**Step 1 example (#3):**

```json
{
  "lookup": {"player": "Hank Aaron"},
  "requested_attributes": ["debut_team", "debut_year", "career_hr", "career_rbi", "career_hits", "birth_date"],
  "provenance": true
}
```

---

## M3 gate — `career_avg` derive (live Lahman)

**Requires:** `OPENAI_API_KEY` in framework `.env` (computation codegen uses `MYCELIUM_COMPUTATION_CODEGEN_MODEL`, default `gpt-4o-mini`).

**Clear stale cache** if you tested before M3 (sticky `N/A`):

```bash
rm -f ~/mycelium-networks/baseball/agents/batting/storage.json
./bin/refresh-example-network baseball --sync-only
# restart MCP / Claude session if query_entity was already running
```

| # | What | Expect |
|---|------|--------|
| M3-1 | First deliver | `career_avg` ≈ **0.305** (three decimals, leading zero) |
| M3-2 | Provenance | `computation.inline` contains `query_warehouse`; `parameters.warehouse`, `lahman.playerID`, `attribute: career_avg` |
| M3-3 | Cache hit | Second step 1+2 without clearing storage — same value; no new LLM call (version id unchanged) |
| M3-4 | M2 regression | `career_hr` still **755** — manifest alias path, no LLM |
| M3b-1 | Derive retry | On bad generated SQL, specialist retries silently (up to 5); operator sees `derive career_avg attempt N failed` in graph `audit_log` and `QueryResponse.debug` (`operator_audit=`) |
| M3c-1 | Semantic review | Derive uses full manifest context + LLM review after successful execution; implausible values (e.g. `0.000` from SQL int division) retry silently — clear batting `storage.json` if a bad value was cached |
| M4-1 | Free-form derive (`ops`) | Manifest miss on batting domain → M3c pipeline (no `derive_candidates` whitelist); mocked CI **0.900**; clear batting cache if stale |
| M4b-1 | Intent dedup | ✅ **CLEAR** 2026-06-19 — clear batting cache + `intent_map.json`; `career_avg` then `batting_average` → **0.305**, same timestamp, `intent_slug: career_batting_average`; gate doc [`2026-06-19-baseball-m4b-intent-normalization-gate.md`](2026-06-19-baseball-m4b-intent-normalization-gate.md) |

**Step 1** (partial lookup OK if Aaron is unique on your root):

```json
{
  "lookup": {"player": "Hank Aaron"},
  "requested_attributes": ["career_avg"],
  "provenance": true
}
```

**Step 2:**

```json
{
  "delivery_id": "<from step 1>"
}
```

**CLI equivalent:**

```bash
uv run mycelium query --network baseball \
  --lookup-json '{"lookup":{"player":"Hank Aaron"},"requested_attributes":["career_avg"],"provenance":true}'
uv run mycelium query --network baseball --delivery-id d_…
```

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
| S4 | Provenance shape | either | `parameters` includes `lahman.playerID`, `warehouse`, `attribute`, and batting `column` when applicable |
| S5 | Provenance inline quality | either | Inline is actual Python source of convention functions (`inspect.getsource`) |
| S6 | Multi-attr | all three specialists | `requested_attributes: ["debut_team", "career_hr", "birth_date"]` + `provenance: true` — bind `registry`/`seed_bootstrap`, warehouse `parameters.warehouse` |
| S7 | Pitching + team | `pitching_specialist`, `team_season_specialist` | Live gate `bb-pitch-*`, `bb-team-01`, `bb-multi-01` (Nolan Ryan pitching + Brooklyn Dodgers season wins) |

**Automated regression:** `./bin/gate-live baseball` runs catalog scenarios including `bb-bio-01`, `bb-pitch-03`, and M5–M6 pitching/team phases — prefer over hand-copy for routine checks.

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
| R4 | Unknown bio attr (e.g. `nickname`) | Graceful `N/A` — not in manifest |

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
| `career_sb` | Batting alias not in manifest yet |
| `era` (season-scoped), `wins`, `strikeouts`, `walks`, `games_pitched` | Optional season-scoped pitching aliases (not in manifest) |
| `attendance` | Optional team_season alias (not in manifest) |
| Career team list via query API | Identity is debut bind only — use warehouse SQL (identity doc § H) |
| CRM attrs (`email`, `employer`, …) | Wrong network / stub categories replaced on baseball root |
| `record_type` on `EntityQuery` | Removed — routing is lookup-key shape only |
| Perfect `health_check` ping on baseball | CRM-hardcoded ping may show `degraded` |

---

## Suggested session order (~20–30 min)

**M2 complete path:** [M2 extended gate](#m2-extended-gate-live-lahman) **#0 → #3 → #5** (minimum); add **#2**, **#4**, **#6–#7** as time allows.

**Legacy M1 smoke path:**

1. `describe_network` + `health_check`
2. Resolve Aaron once; note debut bind + `id`
3. **S2 `birth_date`** — compose, check provenance inline
4. **S1 `career_hr`** — aggregate, check provenance inline
5. **S3** — repeat each; confirm cache
6. Spot-check **ID2** team lookup and **N1** legacy keys
7. Optional: Ty Cobb or another player for ID1 variety

---

## Provenance — what “good” looks like

For each warehouse attr with `provenance: true`:

- **`sources[]`** — dataset pin (`kind: dataset`, `id: lahman`, version / `retrieved_from` from seed)
- **`computation.inline`** — runnable Python that matches what the specialist executed
- **`parameters`** — `lahman.playerID`, `warehouse` (relative path), `attribute`, and batting `column` when applicable
- **`actor.specialist`** — `batting_specialist`, `bio_specialist`, or `player_identity_specialist` (bind: `actor.kind` `registry` / `seed_bootstrap`)

This is **computation-centric** lineage ([design doc](../plans/conversations/2026-06-18-computation-centric-provenance.md)) — not table/column citations.

---

## Notes

- **Stale specialist cache:** Cached `N/A` or old provenance inline persists until storage is cleared — specialists do not retry cached `na`. After M2b/M2c sync, if new attrs stay `N/A` or warehouse provenance lacks `parameters.warehouse`, remove the relevant file and re-deliver:
  - `agents/batting/storage.json` — pre-M2b `career_rbi` / `career_hits` na; old `career_hr` inline
  - `agents/bio/storage.json` — old `birth_date()` inline; pre-M2b bio `N/A`
  - `agents/player_identity/storage.json` — factory `research` on bind attrs (current version should be `registry` after M2c deliver)
- **Stale bind provenance:** If `debut_team` / `debut_year` **current** version still shows `research`, clear `agents/player_identity/storage.json` and re-deliver (pack specialist appends `registry` version).
- **Fixture vs live bind:** Smoke tests use Brooklyn Dodgers / 1957 for a one-row fixture. Full Lahman Aaron uses his real debut franchise/year — always discover on your root.
- **CLI alternative:** `./bin/baseball-query '<json>'` — same payloads as MCP `query_entity`.
- **Parent gates:** Identity ship gate [`2026-06-17-baseball-identity-ship-gate.md`](2026-06-17-baseball-identity-ship-gate.md); timing [`2026-06-17-storage-evolution-timing-gates.md`](2026-06-17-storage-evolution-timing-gates.md).