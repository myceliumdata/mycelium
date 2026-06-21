# Baseball multi-domain derive + live gate (post-reload)

> **READY** — Baseball program **signed off** (2026-06-21, gate **27/27**, Test 10 bootstrap **~3.5 min**). Claim when Paul prioritizes multi-domain derive (after or parallel to `2410` bio research). **Do not edit `TODO.md`.**

## Objective

Enable manifest-driven **derive-on-miss** on **pitching** and **fielding** player domains, fix the framework to pass the correct domain into the derive pipeline, and add **live gate scenarios** with anchor values for baseball-meaningful derivative stats that are **not** manifest aliases.

Flipping `derive_on_miss` is easy; the product value is **credible guinea-pig stats** + gate coverage so regressions show up before demo.

**Paul lock:** Framework derive lives in `WarehousePlayerStatSpecialist`; pack only supplies `derive_resolve` via hooks. Do not duplicate derive loops in pack specialists.

Read: [`docs/architecture/whys/specialist-class-hierarchy.md`](../../../docs/architecture/whys/specialist-class-hierarchy.md), existing derive phase in [`tests/live/catalogs/baseball.yaml`](../../../tests/live/catalogs/baseball.yaml) (`bb-derive-01`–`03`).

---

## Prerequisites (verify before claiming)

- [x] Post-2280 / post-capstone full refresh complete on `~/mycelium-networks/baseball`
- [x] `./bin/gate-live baseball` → **27/27** (2026-06-21 program sign-off)
- [ ] `OPENAI_API_KEY` + `MYCELIUM_COMPUTATION_CODEGEN_MODEL` available for derive scenarios (same as batting derive phase)

---

## Baseball rationale (locked guinea pigs)

These are deliberate **miss-path** stats — do **not** add manifest aliases for them in this slice (that would bypass derive).

### Pitching domain — anchor player **Nolan Ryan** (`ryanno01`)

| Attribute | Why it matters | Lahman recipe (discovery SQL) | Gate style |
|-----------|----------------|-------------------------------|------------|
| **`career_whip`** | WHIP is the standard companion rate to ERA; scouts and broadcasters use it constantly | `(SUM(BB) + SUM(H)) / (SUM(IPouts) / 3)` on `Pitching` | `approx`, tolerance **0.01** |
| **`k_per_9`** | Strikeouts per 9 IP — Ryan’s hallmark; separates pitching domain from batting rates | `SUM(SO) * 9.0 / (SUM(IPouts) / 3)` | `approx`, tolerance **0.05** |
| **`career_innings_pitched`** | Famous counting derivative (Ryan ≈ 5386 IP); tests integer formatting, not just rates | `SUM(IPouts) / 3` | `approx`, tolerance **0.1** (or `equals` if you round to whole innings in discovery) |

**Regression:** `career_era` must **still** resolve via `career_era_weighted` manifest path (`bb-pitch-03`) — not LLM — after pitching `derive_on_miss: true`.

**Optional 4th (only if first three gate green):** `career_winning_percentage` = `W / (W+L)` as decimal string, tolerance 0.001.

### Fielding domain — anchor player **Hank Aaron** (`aaronha01`)

| Attribute | Why it matters | Lahman recipe | Gate style |
|-----------|----------------|---------------|------------|
| **`fielding_percentage`** | Classic `(PO + A) / (PO + A + E)`; outfielders have long careers — stable anchor on Aaron | Pool `PO`, `A`, `E` across all `Fielding` rows for `playerID` | `approx`, tolerance **0.0001** (4 decimal places is conventional) |

**Do not enable bio derive** in v1 — bio attrs are `people_column` / `people_compose` reads; there is no compelling LLM guinea pig that isn’t better as a manifest alias.

**Team domain:** out of scope (`WarehouseTeamStatSpecialist` has no derive v1).

---

## Blocking fix — framework domain parameter

Today `WarehousePlayerStatSpecialist.resolve_derive_on_miss()` calls `generate_and_run_derive(...)` **without** `domain=`. Pack `derive_resolve.generate_and_run_derive` defaults `domain="batting"`, so pitching/fielding derive would get **wrong warehouse context** in prompts.

**Fix (required):** pass `domain=self.domain` from `src/agents/specialists/warehouse_stat.py` into `generate_and_run_derive`. Add a **framework smoke test** (stub specialist, mocked derive module) asserting the domain argument.

**Pack hygiene:** Update `derive_resolve.py` module docstring / `_audit_line` so audit text is not hardcoded `batting_specialist` when domain ≠ batting (use domain or caller agent name if available).

---

## Implement

### 1 — Manifest (`warehouse_domains.json`)

Add to **pitching** and **fielding** domains only:

```json
"derive_on_miss": true
```

Leave **bio** without the flag. Leave **batting** unchanged.

### 2 — Ontology / routing

Ensure guinea-pig labels route to the correct specialist category (`pitching`, `fielding`) via existing ontology — same pattern as `ops` → batting. Add ontology entries only if missing.

### 3 — Live gate catalog (`tests/live/catalogs/baseball.yaml`)

Add scenarios (suggested IDs — adjust if collisions):

| ID | Phase | Player | Attributes | Notes |
|----|-------|--------|------------|-------|
| `bb-derive-04` | `derive` | `{{ anchors.pitcher_player }}` | `[career_whip]` | `skip_if_missing_env` like `bb-derive-01`; `provenance: true` |
| `bb-derive-05` | `derive` | `{{ anchors.pitcher_player }}` | `[k_per_9]` | rate drift helper |
| `bb-derive-06` | `derive` | `{{ anchors.pitcher_player }}` | `[career_innings_pitched]` | counting derivative |
| `bb-derive-07` | `derive` | `{{ anchors.player }}` | `[fielding_percentage]` | fielding domain |
| `bb-derive-08` | `derive` | `{{ anchors.pitcher_player }}` | `[whip]` | **Synonym / intent** cache hit after `bb-derive-04`; `depends_on: bb-derive-04`; `same_timestamp_as` + `intent_slug: career_whip` (mirror `bb-derive-03` batting pattern) |

**Do not weaken** existing `bb-pitch-03` (`career_era` manifest path).

Update `tests/test_live_gate_runner_unit.py` minimum scenario count and ensure `derive` phase still listed in `tests/live/networks.yaml` (add `derive_pitching` / `derive_fielding` sub-phases only if you need finer reporting — default: keep single `derive` phase).

### 4 — Anchors (`tests/live/anchors/baseball_aaron_lahman_v2025.json`)

**Discovery is mandatory** — run SQL against Paul’s live `warehouse/lahman.sqlite` on the reloaded root; do not guess Ryan/Aaron values from memory.

Add keys (names negotiable in `output.md`):

```json
"pitcher_career_whip": <discovered>,
"pitcher_k_per_9": <discovered>,
"pitcher_career_innings_pitched": <discovered>,
"fielding_percentage": <discovered>
```

Document discovery queries in `output.md`.

### 5 — Drift checks (`tests/live/gate_runner.py`)

Extend `discover_anchor_drift` for baseball:

- New pitcher derive attrs on `pitcher_player` (same pattern as `pitcher_career_era`)
- `fielding_percentage` on `player` (Aaron)
- Add new rate attrs to `RATE_DRIFT_ATTRS` where `rate_value_drift` applies (`career_whip`, `k_per_9`, `fielding_percentage`)

### 6 — Smoke tests (fixture + mocked derive)

| Test | Layer |
|------|--------|
| Framework domain passed to `generate_and_run_derive` | `tests/test_warehouse_stat_specialist.py` |
| Pitching derive on miss (mocked LLM) returns value when alias missing | `tests/test_baseball_pitching_specialist.py` or new `tests/test_baseball_pitching_derive.py` |
| Fielding derive on miss (mocked) | `tests/test_baseball_fielding_specialist.py` or sibling |
| `career_era` still manifest-resolved when `derive_on_miss` true on pitching | pitching smoke — no mock needed |

Reuse existing OPS/career_avg mock patterns from `tests/test_baseball_ops_derive.py`.

### 7 — Docs

- `docs/manual-checks/2026-06-19-baseball-specialist-hand-test.md` — add pitching/fielding derive rows under derive section
- `docs/manual-checks/2026-06-20-live-gate-program.md` — update baseball scenario count
- `examples/networks/baseball/README.md` — one paragraph: multi-domain derive via manifest flag

---

## Live gate (required)

Follow `prompts/cursor/WORKFLOW.md` §1: anchors from live discovery, drift checks, phases, `@pytest.mark.live_gate` only (never default CI).

Paul runs `./bin/gate-live baseball` after slice — target **32/32** (27 existing + 5 new) or document count in `output.md`.

---

## Constraints

- **No** new manifest aliases for guinea-pig attribute names (WHIP, K/9, fielding %, etc.)
- **No** `WarehouseTeamStatSpecialist` derive
- **No** bio `derive_on_miss`
- CRM unchanged
- `./bin/ci-local` must pass

---

## Output

Follow `prompts/cursor/WORKFLOW.md`. In `output.md` **For Grok + Paul**:

- Discovery SQL + computed anchor table
- Final live gate scenario count
- Confirm `bb-pitch-03` still manifest-only for `career_era`
- Note any intent_map entries created on live root during synonym scenario

Suggested commit message:

```
feat(baseball): multi-domain derive-on-miss + live gate (pitching, fielding)
```