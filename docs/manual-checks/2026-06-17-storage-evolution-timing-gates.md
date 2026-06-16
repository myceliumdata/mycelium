# Storage evolution — timing gates (manual)

**Program:** [`docs/plans/storage-evolution-program.md`](../plans/storage-evolution-program.md)  
**Owner:** Paul + Grok (not Cursor)  
**Benchmark:** Baseball example network refresh (Lahman bootstrap + warehouse ingest)

---

## Environment

Use a **dedicated benchmark root** so runs are comparable and do not disturb a live network:

```bash
export BENCHMARK_ROOT=/tmp/mycelium-baseball-benchmark
```

Ensure Lahman seed is available (framework fetches on refresh when configured — see `093f4a0` fetch commit). First run may download seed; note that in results.

**Command (all timing tests):**

```bash
/usr/bin/time -p ./bin/refresh-example-network baseball \
  --root "$BENCHMARK_ROOT" --yes --no-default
```

Record **real**, **user**, **sys** from `time -p` output.

---

## Timing test 3 — after slice 2 approved

**When:** `2026-06-17-2100-specialist-minisql-v1-migrate` reviewed **Approved** and committed locally.

**What changed:** Specialist category storage can migrate to `minisql_v1` when record count crosses threshold. Entity registry I/O is **unchanged** — expect **modest** improvement at best until slice 4.

**Record in this table:**

| Run | Date | real (s) | user (s) | sys (s) | Notes |
|-----|------|----------|----------|---------|-------|
| Test 3 | | | | | Post slice 2 |

**Gate:** No blocking threshold — record numbers and proceed. If regression vs pre-program baseline is severe, investigate before releasing slice 4.

**After recording:** Grok or Paul moves `prompts/cursor/hold/2026-06-17-2300-entity-registry-storage-evolution.md` → `prompts/cursor/next/`.

---

## Timing test 5 — after slice 4 approved

**When:** `2026-06-17-2300-entity-registry-storage-evolution` reviewed **Approved** and committed locally.

**What changed:** Deferred bootstrap save (one flush per grain) + entity `minisql_v1` migration at threshold. This is the **primary** baseball bootstrap perf slice.

**Record in this table:**

| Run | Date | real (s) | user (s) | sys (s) | Notes |
|-----|------|----------|----------|---------|-------|
| Test 5 | | | | | Post slice 4 |

**Compare** to Test 3 (and optional pre-program baseline if captured).

**Gate:** Paul decides program push / baseball demo readiness from these numbers + `./bin/ci-local` + capstone tests.

---

## Baseline (pre slice 2) — **recorded**

**When:** After slice 1 (`optimize_storage` threshold policy); **before** slice 2 (`minisql_v1` specialist migration). SpecialistAgent + Lahman bootstrap shipped; entity registry still per-row JSON flush.

| Run | Date | real (s) | user (s) | sys (s) | Notes |
|-----|------|----------|----------|---------|-------|
| **Baseline** | 2026-06-16 | **12,600** (~**3.5 h**) | — | — | Paul wall-clock. `--root /tmp/mycelium-baseball-benchmark --yes --no-default`. Dominant cost: `LahmanSeedHandler` player loop (~57.6k player–team bind rows) — each `save_entity` rewrites full `entities/player.json` + specialist bind storage. Team grain (241) finished in first minute; warehouse ingest ~26 MB at start. |

**Compare test 3 and test 5 against this row.**

---

## Sanity after each timing run

```bash
./bin/ci-local
```

Confirm `tests/test_lahman_seed_handler.py` and CRM capstones still green in the working tree used for the program.