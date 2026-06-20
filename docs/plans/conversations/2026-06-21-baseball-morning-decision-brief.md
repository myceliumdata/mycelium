# Baseball morning decision brief (2026-06-22)

**For Paul** — skim in ~15 minutes, tick choices, tell Grok your picks. Unblocks: derivative audit, training-wheels sign-off, bio specialist slice.

Related: [`2026-06-21-baseball-bio-research-specialist.md`](2026-06-21-baseball-bio-research-specialist.md), [`TODO.md`](../../TODO.md) Next up.

---

## Part A — Derivative stats currently under test

### What “derivative” means here

| Kind | Mechanism | Provenance shape | Example attrs |
|------|-----------|------------------|---------------|
| **Manifest warehouse** | SQL / compose on Lahman sqlite | `computation.inline` + `parameters.lahman.playerID` | `career_hr`, `career_era`, `birth_date` |
| **LLM derive-on-miss** | Python codegen + sandbox (no Tavily) | inline Python + optional `model` | `career_avg`, `ops` |
| **Product specialist** | Cross-table join in pack code | inline + scope params | `roster`, `franchise_teams` |

### Live gate inventory (27 scenarios)

| Scenario | Attr(s) | Player/team | Kind | Anchor / expect | Notes |
|----------|---------|-------------|------|-----------------|-------|
| bb-m2-01 | `career_hr`, `birth_date` | Aaron | manifest | 755, 1934-02-05 | Multi-specialist |
| bb-m2-02 | `career_rbi`, `career_hits` | Aaron | manifest | 2297, 3771 | |
| bb-m2-03 | 6 attrs | Aaron | mixed | hr + bio | Fan-out |
| bb-m2-04 | `bats`, `throws`, `birth_city` | Aaron | manifest | R, R, Mobile | |
| bb-bio-01 | `height`, `weight`, `birth_country` | Aaron | manifest | 72, 180, USA | |
| bb-bio-02 | `final_game`, `death_date` | Aaron | manifest | 1976-10-03, 2021-01-22 | |
| bb-derive-01 | `career_avg` | Aaron | **LLM derive** | ≈ 0.305 | Needs API keys |
| bb-derive-02 | `ops` | Aaron | **LLM derive** | ≈ 0.928 | Free-form label |
| bb-derive-03 | `batting_average` | Aaron | derive + **intent cache** | same as career_avg | Depends on 01 |
| bb-pitch-01 | `career_wins`, `career_strikeouts` | Aaron | manifest | 0, 0 | Zero pitching rows |
| bb-pitch-02 | `career_wins`, `career_strikeouts` | Nolan Ryan | manifest | 324, 5714 | |
| bb-pitch-03 | `career_era` | Nolan Ryan | manifest **rate recipe** | ≈ 3.194 | `career_era_weighted`, not LLM |
| bb-multi-01 | `career_hr`, `career_wins` | Aaron | mixed | 755, 0 | |
| bb-field-01 | `career_games`, `career_putouts` | Aaron | manifest **Fielding** | **3020**, **7436** | Fixed `da5b006` — not Batting G (3298) |
| bb-roster-01 | `roster` | 1957 BRO | product | contains Duke Snider | Scoped cache |
| bb-franchise-01 | `franchise_teams` | Brooklyn Dodgers | product | JSON label list | |
| bb-team-01/02 | `season_wins`, `season_losses` | Dodgers | manifest + scope | 84, 70 | |
| bb-scope-01 | `career_hr` + bogus year | Aaron | manifest | 755 ignores scope | career_sum |

### Quick audit questions (tick when reviewed)

- [ ] Every **manifest** anchor was discovered from the correct Lahman table/convention (fielding lesson applied everywhere).
- [ ] **LLM derive** attrs (`career_avg`, `ops`) are intentionally not manifest aliases (miss path is the point).
- [ ] **career_era** stays manifest — enabling pitching `derive_on_miss` later must not steal it (regression called out in `2400` slice).
- [ ] Product attrs (`roster`, `franchise_teams`) are not wired through warehouse graph bases (by design).

**Paul note:** _______________________________________________

---

## Part B — Training wheels: what’s off vs still on

M3 “training wheels” = `derive_candidates` whitelist. **Removed in M4** for batting.

### Off (production policy today)

| Wheel | Status |
|-------|--------|
| `derive_candidates` whitelist | **Removed** — any batting manifest miss can derive |
| Batting domain gate | `derive_on_miss: true` in `warehouse_domains.json` |
| Free-form labels | `ops` in ontology routes to batting without alias |

### Still on (intentional guardrails — confirm these stay)

| Guardrail | What it does | Example |
|-----------|--------------|---------|
| **Domain flag** | Only batting has `derive_on_miss` | Pitching `career_whip` → N/A today, not derive |
| **Semantic review** | LLM rejects implausible derive values before cache | M3c review prompt on `ops` |
| **Sandbox** | Derive code can only use `query_warehouse()` | No network/file I/O in derive |
| **Intent normalization** | Synonyms map to slug before cache | `batting_average` → `career_batting_average` |
| **Gate fresh derive** | `gate-live` clears batting cache before derive phase | Ensures real LLM path, not stale cache |
| **Env keys** | Derive scenarios skip without `OPENAI_API_KEY` | Not a code cap — operator must set keys |

### Training-wheels sign-off (pick one)

- [ ] **A — Signed off:** Batting derive is “wheels off”; remaining rows are safety rails, not training wheels.
- [ ] **B — Not yet:** Enable pitching/fielding `derive_on_miss` (`2400` slice) before calling wheels off globally.
- [ ] **C — Other:** _______________________________________________

---

## Part C — Bio specialist: 8 decisions with examples

**Locked already (no need to re-debate):**

- Bio uses **warehouse first** (Lahman `People`).
- **No** `derive_on_miss` on bio (no sqlite codegen for “college attended”).
- **Yes** Tavily path for facts outside manifest.

---

### Q1 — Framework shape

**User story:** Client asks for `birth_date` + `hall_of_fame_year` on Hank Aaron in one step-1.

| Option | Behavior | Pros | Cons |
|--------|----------|------|------|
| **A — `WarehouseResearchPlayerSpecialist` in `src/`** | One `BioSpecialist` class: warehouse loop, then `run_field_research` for remaining misses | Matches M14 hierarchy; second network inherits | New framework tier to test |
| **B — Pack-only: `BioSpecialist.run()` override** | Same flow, logic only in `bio_specialist.py` | Fastest slice | Duplicates CRM factory template; violates Paul lock |
| **C — Split categories `bio` + `bio_web`** | Warehouse attrs → `bio_specialist`; web attrs → generated research specialist | Clean separation | Two agents, routing/ontology split; awkward combined queries |

**Example step-1:**

```bash
uv run mycelium query --network baseball \
  --lookup-json '{"player":"Hank Aaron"}' \
  --requested-attributes birth_date,hall_of_fame_year
```

| Option | Step-2 result |
|--------|----------------|
| A | One specialist, one contrib: `birth_date` from People, `hall_of_fame_year` from Tavily |
| C | Two specialists fan-out; assembler merges (like `bb-m2-01` today) |

**Grok lean:** **A** — framework base + thin `BioSpecialist`.

**Paul pick:** [ ] A  [ ] B  [ ] C

---

### Q2 — When does Tavily run?

| Option | Rule | Example: `hall_of_fame_year` | Example: typo `brith_date` |
|--------|------|------------------------------|------------------------------|
| **A — `research_on_miss: true`** | Any bio label not in `warehouse_domains.json` aliases → research after warehouse N/A | Tavily runs | Probably N/A (not in ontology) |
| **B — Manifest allowlist** | Only listed `research_labels: [...]` get Tavily | Runs if listed | No research |
| **C — Client flag only** | Research only if `EntityQuery.research: true` (new field) | No run unless flag | No run |

**CRM today:** generated specialists research on cache miss when keys set — closest to **A**.

**Risk of A:** Client sends garbage label → Tavily spend. Mitigation: ontology must route label to `bio` first.

**Grok lean:** **A** for v1 (parity with CRM); add allowlist later if cost bites.

**Paul pick:** [ ] A  [ ] B  [ ] C  Allowlist if B: _______________

---

### Q3 — Live gate guinea pig(s)

| Candidate | Sample query | Expected (Aaron) | Gate difficulty |
|-----------|--------------|------------------|-----------------|
| **`hall_of_fame_year`** | `requested_attributes: [hall_of_fame_year]` | Lahman `HallOfFame.yearid` = **`1982`** (election) — not ceremony year | Anchor semantics matter (see Q8) |
| **`primary_nickname`** | `requested_attributes: [primary_nickname]` | `"Hammer"` (normalize?) | Fuzzy string match |
| **`college_attended`** | could be Lahman `CollegePlaying` later | `"None"` or school name | Table exists in sqlite already |

**Synonym scenario (optional, like bb-derive-03):**

```text
hall_of_fame_induction_year → intent slug hall_of_fame_year (cache hit)
```

**Grok lean:** Gate **01 = `hall_of_fame_year` only** for v1; skip nickname until normalization story is clear.

**Paul pick:**

- [ ] `hall_of_fame_year` only
- [ ] + `primary_nickname`
- [ ] + synonym scenario
- [ ] Other: _______________

---

### Q4 — Ontology / routing

Today `hall_of_fame_year` is **not** in `categories.json` or `attribute_map` — step-1 won’t route it to `bio_specialist` until added.

**Example fix (hand-add):**

```json
// categories.json bio.examples +=
"hall_of_fame_year"

// attribute_map +=
"hall_of_fame_year": "bio"
```

| Option | Work |
|--------|------|
| **A — Hand-add** guinea pig(s) only | 2 lines per attr; fine for gate |
| **B — Ontology generator pass** | Refresh `categories.json` from manifest + “research bio” list |
| **C — Supervisor classify only** | No map entry; rely on LLM classification each query | Slower, less deterministic |

**Grok lean:** **A** for slice; **B** as follow-on.

**Paul pick:** [ ] A  [ ] B  [ ] C

---

### Q5 — Mixed provenance in one deliver

**Query:** `birth_date` + `hall_of_fame_year` with `provenance: true`.

| Field | Provenance flavor |
|-------|-------------------|
| `birth_date` | `computation.inline` with `people_compose`; `parameters.columns` |
| `hall_of_fame_year` | `sources[]` with Tavily URLs; research metadata |

**Today:** `bb-m2-01` already mixes batting + bio provenance in one response — different specialists, one assembled `results[]`.

| Option | Policy |
|--------|--------|
| **A — Allow mix** | Per-attribute provenance type in same entity (current assembler behavior) |
| **B — Reject mix** | Research attrs must be separate queries |
| **C — Strip research provenance** | Return value only, no URLs on bio research v1 |

**Grok lean:** **A** — matches computation-centric + research coexistence in architecture whys.

**Paul pick:** [ ] A  [ ] B  [ ] C

---

### Q6 — Latency / cost

| Option | Step-2 UX | CRM analog |
|--------|----------|------------|
| **A — Sync Tavily** (default) | 10–40s on first miss; cache hit fast | `email` research |
| **B — Pending** | Step-2 returns `pending` for research fields; client polls | Not implemented |
| **C — Sync with budget** | Max N Tavily calls per deliver | New work |

**Example first hit:**

```text
Step-1: hall_of_fame_year only → step-2 waits for Tavily (~30s)
Step-2 repeat: reads cache → instant
```

**Grok lean:** **A** for v1 (reuse `run_field_research`).

**Paul pick:** [ ] A  [ ] B  [ ] C

---

### Q7 — Slice ordering

| Option | Rationale |
|--------|-----------|
| **A — Bio research first (`2410`)** | Unblocks “follow-up bio questions” product story; independent of derive |
| **B — Multi-domain derive first (`2400`)** | WHIP/K/9 gate story; framework `domain=` fix benefits all derive |
| **C — Parallel** | Two Cursor agents (if you run parallel) |

**Grok lean:** **A** if bio is tomorrow’s focus; **B** if you want derivative stats expansion first.

**Paul pick:** [ ] A  [ ] B  [ ] C

---

### Q8 — Warehouse vs research boundary

Lahman sqlite **already has** (M13 ingest, not in `warehouse_domains.json`):

- `HallOfFame` — induction year, vote %, …
- `CollegePlaying` — schools per player

| Option | `hall_of_fame_year` policy |
|--------|--------------------------|
| **A — Research v1, manifest later** | Tavily now; add `people_join` / HOF alias in a later slice |
| **B — Manifest first** | Add HOF alias before enabling bio research — research only for truly un-ingested facts |
| **C — Research only forever** | Some facts never get manifest aliases (narrative, nickname) |

**Concrete check:**

```bash
sqlite3 ~/mycelium-networks/baseball/warehouse/lahman.sqlite \
  "SELECT yearid FROM HallOfFame WHERE playerID='aaronha01' AND inducted='Y' LIMIT 1;"
# Expect: 1982 (HOF election year) — NOT 1999 induction ceremony year; anchor semantics matter!
```

**Important:** “Hall of Fame year” is ambiguous — **election year (1982)** vs **induction ceremony (1999)**. Pick anchor semantics before gate.

**Grok lean:** **A** for slice velocity + gate on research path; document election vs induction in anchor; **B** as fast follow-on if you want HOF from sqlite without Tavily.

**Paul pick:** [ ] A  [ ] B  [ ] C  
**HOF anchor means:** [ ] election year  [ ] induction year  [ ] other: _______

---

## Part D — One-page answer sheet (copy to Grok)

```text
DERIVATIVE AUDIT: done [ ]  notes: ___________
TRAINING WHEELS:  A / B / C
BIO Q1:  A / B / C
BIO Q2:  A / B / C
BIO Q3:  hall_of_fame_year / +nickname / +synonym
BIO Q4:  A / B / C
BIO Q5:  A / B / C
BIO Q6:  A / B / C
BIO Q7:  A / B / C
BIO Q8:  A / B / C  HOF anchor: election / induction
```

After picks → Grok updates conversation lock + flips `2410` slice to **READY** for Cursor.

---

## Part E — Suggested CLI smoke (tomorrow, optional)

After decisions, before Cursor:

```bash
# Confirm HOF data exists locally (for Q8)
sqlite3 ~/mycelium-networks/baseball/warehouse/lahman.sqlite \
  ".tables" | tr ' ' '\n' | grep -i hall

# Current bio path still works
./bin/gate-live baseball --phase m2

# Full sign-off regression
./bin/gate-live baseball
```