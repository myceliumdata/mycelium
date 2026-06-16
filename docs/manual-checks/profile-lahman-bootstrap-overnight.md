# Lahman bootstrap profiling — overnight handoff (June 2026)

**Owner:** Grok (after Paul pastes test 6 `time -p` results)  
**Goal:** Measure where bind-loop time goes post-`c5e5bce` (incremental specialist upserts). **Profile before** queuing the next optimization slice.

---

## Paul pastes when run completes

From terminal running:

```bash
/usr/bin/time -p ./bin/refresh-example-network baseball \
  --root /tmp/mycelium-baseball-benchmark --yes --no-default
```

Record **real**, **user**, **sys** → Test 6 row in [`2026-06-17-storage-evolution-timing-gates.md`](2026-06-17-storage-evolution-timing-gates.md).

---

## Grok runs (same root, bootstrap only)

Warehouse + seed already on disk from refresh. Profile **handler only** (repeatable, no wipe):

```bash
cd /path/to/mycelium
chmod +x bin/profile-lahman-bootstrap
MYCELIUM_BOOTSTRAP_PROGRESS=0 ./bin/profile-lahman-bootstrap \
  /tmp/mycelium-baseball-benchmark \
  -o /tmp/lahman-bootstrap-test6.prof | tee /tmp/lahman-bootstrap-test6.txt
```

**Paste into this file** (Grok): top 15 cumulative lines + alias/index/write_fields tottime block.

### Overnight results (2026-06-17)

Profile completed on warm post–test 6 root. **`build_field_indexes` ≈ 97% of handler time** (4590 s / 4725 s cProfile). **23,844** `_rebuild_field_indexes` calls; **`add_bind_alias` 0 calls** (aliases already present — fresh run still hits ~33k alias path). Specialist upserts **~91 s** — not the bottleneck.

Slice § Profile results filled in `prompts/cursor/next/2026-06-18-0900-bootstrap-perf-profile-driven.md`. Raw: `/tmp/lahman-bootstrap-test6.txt`, `/tmp/lahman-bootstrap-test6.prof`.

---

## Decision rule for morning slice

| Principle | Detail |
|-----------|--------|
| **Clarity over cleverness** | No batch/SQL identity loader in this slice unless profile proves Python loop is noise |
| **Fix dopey work only** | e.g. rebuild indexes when `bind_index` alone changed |
| **One slice** | Smallest change that profile supports |

**Hypothesis (unconfirmed):** `add_bind_alias` → `save_entity` → `_rebuild_field_indexes()` on ~34k rows with unchanged `bind_values`.

**Queue:** `prompts/cursor/next/2026-06-18-0900-bootstrap-perf-profile-driven.md` — Grok fills § Profile results before Paul runs Cursor.