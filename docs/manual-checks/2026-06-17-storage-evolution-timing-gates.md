# Storage evolution — timing gates (manual)

**Program:** [`docs/plans/storage-evolution-program.md`](../plans/storage-evolution-program.md)  
**Owner:** Paul + Grok (not Cursor)  
**Benchmark:** Baseball example network refresh (Lahman bootstrap + warehouse ingest)

---

## Summary (posterity — June 2026)

| Test | Commit era | `real` (s) | Status | Headline |
|------|------------|------------|--------|----------|
| **Baseline** | Pre slice 2 | **12,600** (~3.5 h) | Recorded (Paul wall-clock) | JSON specialists + per-row entity JSON flush |
| **Test 3** | Post slice 2 (`179e80d`) | **~8,100** estimated | **Unreliable** — run never finished; extrapolated at ~25% | Do not use for decisions |
| **Test 5** | Post slice 4 (`c898036`+) | **~16,200** estimated (~4.5 h) | **Abandoned** — killed in progress; no `time -p` final | ~No gain vs baseline; slice 4 not the big win |
| **Test 6** | Post incremental (`c5e5bce`+) | **1,202** (~20 min) | **Recorded** | ~10× vs baseline; still dominated by field-index rebuilds |
| **Test 7** | Post alias skip rebuild (`f45b65c`+) | **555** (~9 min) | **Recorded** | **2.2×** vs test 6; **~23×** vs baseline; further bootstrap perf **deferred** (Paul, June 2026) |

**Takeaway:** Lahman bootstrap is **not** “50k INSERTs.” Warehouse ingest is **~2 s**. The bind loop is ~58k identity operations. Incremental specialist writes (test 6) and alias-only index skip (test 7) removed the worst quadratic costs; **~24k new-player `save_entity` rebuilds remain O(n²)** — acceptable for now; no more optimization slices queued.

See [Lessons learned](#lessons-learned-posterity-june-2026) and [`docs/plans/storage-evolution-program.md`](../plans/storage-evolution-program.md) § Post-mortem.

---

## Environment

Use a **dedicated benchmark root** so runs are comparable and do not disturb a live network:

```bash
export BENCHMARK_ROOT=/tmp/mycelium-baseball-benchmark-test6   # fresh root per test
```

Ensure Lahman seed is available (framework fetches on refresh when configured — see `093f4a0` fetch commit). First run may download seed; note that in results.

**Command (all timing tests):**

```bash
/usr/bin/time -p ./bin/refresh-example-network baseball \
  --root "$BENCHMARK_ROOT" --yes --no-default
```

Record **real**, **user**, **sys** from `time -p` output. Stderr progress (post `9052f45`): `Retrieving data…`, `Processing records (x/y)…`, `Cleaning up…`; silence with `MYCELIUM_BOOTSTRAP_PROGRESS=0`.

---

## What the benchmark actually does

| Phase | Scale | Typical time (measured) |
|-------|--------|-------------------------|
| Git seed fetch + CSV → `lahman.sqlite` | ~128k appearance rows ingested | **~2–3 s** |
| Team grain bootstrap | ~241 distinct team labels | **&lt; 1 min** |
| Player loop | **~57,627** `(playerID, name, team)` rows from Appearances | **Hours** (pre-incremental) |
| — new players (first sight of `playerID`) | **~24,011** → `write_bind_fields` → 2 specialists | Full-table SQLite rewrite per bind (pre-`c5e5bce`) |
| — alias rows (same `playerID`, new team) | **~33,616** → `add_bind_alias` only | No specialist write; **no field-index rebuild** post test 7 (`f45b65c`) |
| Deferred entity flush | 1× per grain at handler end | **Seconds** |

“50k records in seconds” applies only to **warehouse ingest**, not the bind loop.

---

## Baseline (pre slice 2) — **recorded**

**When:** After slice 1 (`optimize_storage` threshold policy); **before** slice 2 (`minisql_v1` specialist migration). SpecialistAgent + Lahman bootstrap shipped; entity registry still per-row JSON flush.

| Run | Date | real (s) | user (s) | sys (s) | Notes |
|-----|------|----------|----------|---------|-------|
| **Baseline** | 2026-06-16 | **12,600** (~**3.5 h**) | — | — | Paul wall-clock. `--root /tmp/mycelium-baseball-benchmark --yes --no-default`. Dominant cost: `LahmanSeedHandler` player loop (~57.6k player–team bind rows) — each `save_entity` rewrites full `entities/player.json` + specialist bind storage. Team grain (241) finished in first minute; warehouse ingest ~26 MB at start. |

---

## Timing test 3 — after slice 2 approved

**When:** `2026-06-17-2100-specialist-minisql-v1-migrate` reviewed **Approved** and committed locally.

**What changed:** Specialist category storage can migrate to `minisql_v1` when record count crosses threshold. Entity registry I/O is **unchanged** — expect **modest** improvement at best until entity work is addressed.

| Run | Date | real (s) | user (s) | sys (s) | Notes |
|-----|------|----------|----------|---------|-------|
| **Test 3** | 2026-06-16 | **8,100** (~**2 h 15 m**) **estimated only** | — | — | Post slice 2 (`179e80d`). Extrapolated from run in progress (~25% player binds, ~6.6/s). **Run never completed; estimate is optimistic** — rate slows as specialist table grows (O(n²)). Treat as invalid for comparison. |

**Gate:** Proceeded to slice 4 (reasonable); test 3 should have been run to completion or not extrapolated early.

---

## Timing test 5 — after slice 4 approved

**When:** `2026-06-17-2300-entity-registry-storage-evolution` reviewed **Approved** and committed.

**What changed:** Deferred bootstrap save (one flush per grain) + entity `minisql_v1` migration at threshold. Program doc called this the “primary” baseball perf slice — **retrospectively overstated** (see lessons).

| Run | Date | real (s) | user (s) | sys (s) | Notes |
|-----|------|----------|----------|---------|-------|
| **Test 5** | 2026-06-16 | **~16,200** (~**4.5 h**) **estimated** | — | — | Post slice 4, **pre-incremental** (`c5e5bce`). `--root /tmp/mycelium-baseball-benchmark`. Started ~21:45; **abandoned** ~46 min in at ~10,277/24,011 specialist entities (~18% of quadratic specialist work done). Projected total ~4–4.5 h — **no meaningful improvement vs baseline**. `entities/player.json` not on disk until cleanup (deferred flush — expected). |

**Proxy snapshot at abandonment (~46 min elapsed):**

- Demographic `entity_records`: **10,277**
- CPU ~93% on bind loop
- Quadratic model: `(10277/24011)² ≈ 18%` of specialist rewrite work complete despite **~43%** of new players written

**Gate:** Slice 4 alone insufficient for demo readiness; incremental specialist writes required (test 6).

---

## Timing test 6 — after incremental specialist writes approved

**When:** `2026-06-17-2340-specialist-minisql-incremental-writes` reviewed **Approved** and committed (`c5e5bce`).

**What changed:** Specialist `minisql_v1` `write_fields` upserts **one entity** per bind (no full-table `DELETE`/`INSERT`). Progress reporting on stderr (`9052f45` / `2f9d673`). Expect **large** improvement vs test 5 (target: hours → minutes; record actual).

| Run | Date | real (s) | user (s) | sys (s) | Notes |
|-----|------|----------|----------|---------|-------|
| **Test 6** | 2026-06-17 | **1,202.19** (~**20 min**) | 1,142.45 | 42.09 | Post incremental (`c5e5bce`+). `--root /tmp/mycelium-baseball-benchmark --yes --no-default` (wiped + refreshed). 57,627 player binds; **23,777** entities committed. Incremental specialists delivered step change; **not demo-fast** — profile shows `build_field_indexes` still ~97% of bind-loop CPU. Morning slice: alias-only skip rebuild. |

**Follow-up perf (optional, post–test 6):** skip `_rebuild_field_indexes()` on alias-only `add_bind_alias` — shipped test 7 (`f45b65c`).

---

## Timing test 7 — after alias-only field-index skip approved

**When:** `2026-06-18-0900-bootstrap-perf-profile-driven` reviewed **Approved** and committed (`f45b65c`).

**What changed:** `add_bind_alias` updates `bind_index` only during deferred bootstrap; skips full `build_field_indexes` scan when `entity.bind_values` unchanged. ~33k alias rows no longer trigger rebuild; ~24k new-player `save_entity` paths still rebuild once per row (remaining O(n²) CPU).

| Run | Date | real (s) | user (s) | sys (s) | Notes |
|-----|------|----------|----------|---------|-------|
| **Test 7** | 2026-06-18 | **555.38** (~**9 min**) | 495.03 | 38.33 | Post alias skip (`f45b65c`). `--root /tmp/mycelium-baseball-benchmark --yes --no-default` (wiped + refreshed). 57,627 player binds; **23,777** entities committed. **2.16× faster** than test 6 (1,202 s → 555 s). **~22.7× faster** than baseline. Still not O(n); **Paul: defer further bootstrap optimization** — clarity over incremental index engineering. |

**Gate:** Good enough for baseball example work; incremental field-index update for new-player path is backlog only if load time blocks demo.

---

## Timing test 8 — regression after `source_keys` (slice 1900)

**When:** Post `ff8f4e0` (`2026-06-17-1900-registry-source-keys-alias-index`).

**What changed:** Lahman handler calls `set_source_keys` on every new team (~241) and player (~24k). `set_source_keys` and `add_bind_alias` each invoked `_save()` with default full `_rebuild_source_key_index()` — O(n) scan per row on top of test 7's remaining ~24k `save_entity` field-index rebuilds. ~57k extra full source-key scans ≈ **5.3×** regression vs test 7.

| Run | Date | real (s) | user (s) | sys (s) | Notes |
|-----|------|----------|----------|---------|-------|
| **Test 8 (regression)** | 2026-06-17 | **2,946.32** (~**49 min**) | 2,769.21 | 55.22 | Post `source_keys` (`ff8f4e0`). Same command/root as test 7. 57,627 player binds; **23,777** entities committed. |

**Fix:** `c96c5e2` — `set_source_keys` incrementally updates `source_key_index` and calls `_save(rebuild_field_indexes=False, rebuild_source_key_index=False)`; `add_bind_alias` skips source-key rebuild too. `commit_deferred_save` still does one full rebuild at grain flush.

| Run | Date | real (s) | user (s) | sys (s) | Notes |
|-----|------|----------|----------|---------|-------|
| **Test 8b** | 2026-06-17 | **1,398.87** (~**23 min**) | 1,287.77 | 44.84 | Post `c96c5e2`. Same command/root. 57,627 player binds; **23,777** entities committed. **2.11× faster** than test 8 (2,946 s). Still **2.52× slower** than test 7 (555 s). |

**Remaining gap vs test 7 (test 8b):** `save_entity` still ran full `_rebuild_source_key_index()` on every new player (~24k). **Fixed** in slice `2026-06-18-0800` — bind-only `save_entity` skips source-key rebuild; pending **Test 8c** confirmation.

| Run | Date | real (s) | user (s) | sys (s) | Notes |
|-----|------|----------|----------|---------|-------|
| **Test 8c** | *pending Paul re-run* | *pending* | *pending* | *pending* | Post `save_entity` source-key skip (slice `2026-06-18-0800`). Same command/root as test 7/8/8b. Expect **~555 s real** (test 7 ballpark, ± variance). |

---

## Lessons learned (posterity — June 2026)

### 1. `minisql_v1` ≠ incremental (slice 2)

Slice 2 moved specialists from JSON **files** to SQLite but kept **document semantics**: each `save_payload` did `DELETE FROM field_records` + `DELETE FROM entity_records` + re-INSERT **all** rows. Lahman bootstrap: ~24k new players × 2 categories → **O(n²)** SQLite + JSON parse work. Slice 2 review noted “full replace — follow-up” but did not block or queue the fix before timing gates. **Fixed in `c5e5bce` (test 6).**

### 2. Slice 4 deferred flush ≠ loop cheap

Deferred entity save removed **~58k rewrites** of growing `entities/player.json` (~17 MB at end). Each `save_entity` / `add_bind_alias` during deferral called `_rebuild_field_indexes()` — full scan of all entities in memory. ~58k iterations × growing entity count ≈ **O(n²) CPU** on the registry side. **Fixed for aliases in test 7** (`f45b65c`); ~24k new-player rebuilds remain. Test 6 → test 7: **2.2×**; baseline → test 7: **~23×**. **Slice 1900** reintroduced O(n²) via per-row `_rebuild_source_key_index()` on `set_source_keys` (~24k) and `add_bind_alias` (~33k) — test 8 regression (**2,946 s**). **`c96c5e2`** fixed set/alias paths (**1,399 s**, 2.1×); **`save_entity` still rebuilds source-key index ~24k×** — explains remaining 2.5× gap vs test 7 (**555 s**).

### 3. Dominant costs (pre-incremental)

| Cost | Order | Affected tests |
|------|--------|----------------|
| Specialist full-table rewrite per new player | O(n²) disk/CPU | Baseline, 3, 5 |
| Entity JSON flush per row | O(n²) disk | Baseline, 3 |
| Entity index rebuild per row (deferred) | O(n²) CPU | 5 |
| Warehouse ingest | O(n) | All (~2 s) |

### 4. Measurement pitfalls

- **Do not extrapolate** Lahman progress from early player count or bind rate — specialist cost grows with table size.
- Use **`time -p` real** on a **completed** run with a **fresh `--root`**.
- Test 5 on pre-incremental code is historical only; **test 6 is the meaningful gate.**

### 5. Incremental write granularity (`c5e5bce`)

Per-entity upsert still `DELETE FROM field_records WHERE entity_id = ?` then re-inserts **all fields on that entity** (entity-scoped replace, not single-field patch). Cost per bind is O(fields on that entity) — fine for bootstrap (1–2 bind fields). See `docs/architecture.md` § `minisql_v1` storage.

### 6. Review/process

- Storage evolution program labeled slice 4 “primary perf slice” — accurate for **entity I/O design**, not for **wall-clock** until specialists were incremental.
- Grok + Paul: queue incremental specialist slice **before** declaring timing gates on slice 4.

---

## Sanity after each timing run

```bash
./bin/ci-local
```

Confirm `tests/test_lahman_seed_handler.py` and CRM capstones still green in the working tree used for the program.