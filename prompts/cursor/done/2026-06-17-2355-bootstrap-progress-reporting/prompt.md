# Bootstrap progress reporting (stderr phases + x/y)

> **READY** — Claim per `prompts/cursor/WORKFLOW.md` (move to `in-progress/` before starting).

**Context:** Baseball `refresh-example-network` runs for **hours** on the Lahman bind loop (~58k player–team rows). Warehouse ingest is **seconds**; the slow phase is identity/bind work with no operator feedback. Paul asked for visible progress during long bootstraps — **without** reverting deferred entity saves or other storage-evolution wins.

**Goal:** Emit **three high-level phases** on **stderr** during refresh/bootstrap:

1. **Retrieving data** — remote seed fetch (git clone) and Lahman warehouse build
2. **Processing records (x/y)** — handler bind loops (teams + players; primary counter on player rows)
3. **Cleaning up** — deferred entity registry flush at end of `run_network_bootstrap`

This slice is **UX only** — no storage perf changes, no new dependencies.

**Parent programs:** Storage evolution (timing gates still valid); baseball example bootstrap.

---

## Locked decisions (Paul + Grok, June 2026)

| # | Decision |
|---|----------|
| B1 | **stderr only** — keep stdout clean for future machine-readable refresh output. |
| B2 | **Three phases** — labels exactly: `Retrieving data…`, `Processing records (x/y)…`, `Cleaning up…` (ellipsis OK; `(x/y)` required on processing line). |
| B3 | **TTY behavior** — when `sys.stderr.isatty()`: in-place `\r` updates on processing line (no flood of lines). When not a TTY: emit at coarse intervals (e.g. every 1% or every 500 rows, whichever is less chatty). |
| B4 | **Env knob** — `MYCELIUM_BOOTSTRAP_PROGRESS`: `1` force on, `0` force off. **Default:** on when stderr is a TTY, off otherwise (CI/tests stay quiet without env). |
| B5 | **Framework reporter** — new `BootstrapProgress` in `src/network/bootstrap/progress.py`; handlers receive it via `BootstrapContext` (optional field, default factory when enabled). |
| B6 | **Cleanup hook** — `run_network_bootstrap` emits **Cleaning up** immediately before `commit_deferred_save()` in the `bootstrap_deferred_save()` exit (when depth returns to 0). |
| B7 | **Seed fetch** — `fetch_git_seed` / `fetch_example_seed` reports **Retrieving data** (same reporter or shared helper — avoid duplicating TTY logic). |
| B8 | **CRM unchanged semantically** — `DefaultSeedHandler` may wire processing counter for seed rows when progress enabled; 15-row CRM refresh stays fast and quiet when progress off. |
| B9 | **No tqdm / no admin UI** — plain stdlib strings only. |

---

## Read first

- `prompts/cursor/WORKFLOW.md`
- `docs/manual-checks/2026-06-17-storage-evolution-timing-gates.md` (timing context — this slice does not replace test 5)
- `src/network/bootstrap/run.py` — `bootstrap_deferred_save()` wrapper
- `src/agents/entity_registry.py` — `bootstrap_deferred_save`, `commit_deferred_save`
- `src/network/example.py`, `src/network/seed_fetch.py` — seed fetch before bootstrap
- `examples/networks/baseball/bootstrap_handlers/lahman_seed.py`, `lahman_common.py`
- `src/network/bootstrap/handlers/default_seed.py`
- `bin/refresh-example-network` — final summary lines on stdout (do not move progress there)
- `tests/test_lahman_seed_handler.py`, `tests/test_network_bootstrap.py`

---

## Architecture target

```
refresh_example_network
  → fetch_example_seed          # phase: Retrieving data
  → run_network_bootstrap
        BootstrapContext.progress = BootstrapProgress(...)
        handler.run(ctx)        # phases: Retrieving (warehouse), Processing (x/y)
        finally:                # phase: Cleaning up → commit_deferred_save()
```

**`BootstrapProgress` API (v1 — keep minimal):**

```python
class BootstrapProgress:
    def retrieving(self, detail: str = "") -> None: ...
    def processing(self, current: int, total: int, *, detail: str = "") -> None: ...
    def cleaning_up(self, detail: str = "") -> None: ...
    def done(self) -> None: ...  # optional: clear TTY line with newline
```

Implementation notes:

- `retrieving` / `cleaning_up`: single line each; newline when phase completes or when processing starts.
- `processing`: update same line with `(current/total)`; include optional detail suffix (e.g. `player binds`).
- Guard all output behind `enabled` property (env + TTY default per B4).
- Module must be importable without side effects; no global singleton required (pass instance through context).

---

## Implement

### 1 — `src/network/bootstrap/progress.py`

- `BootstrapProgress` with B1–B4 behavior.
- Helper `bootstrap_progress_enabled() -> bool` (env + TTY).
- Factory `make_bootstrap_progress() -> BootstrapProgress | None` — returns `None` when disabled (handlers check `ctx.progress`).

### 2 — Extend `BootstrapContext`

In `src/network/bootstrap/context.py`:

```python
progress: BootstrapProgress | None = None
```

Document that handlers should call progress methods when `ctx.progress` is not `None`.

### 3 — Wire `run_network_bootstrap`

In `src/network/bootstrap/run.py`:

- Build `progress = make_bootstrap_progress()` and pass into `BootstrapContext`.
- Wrap handler execution; on `bootstrap_deferred_save()` exit when flushing all registries:
  - `progress.cleaning_up(...)` then existing `commit_deferred_save()` loop.
- Call `progress.done()` after bootstrap completes (clear `\r` line on TTY).

### 4 — Wire seed fetch

In `src/network/seed_fetch.py` (and caller if needed):

- Accept optional `progress: BootstrapProgress | None` on `fetch_git_seed` / `fetch_example_seed`.
- Emit `retrieving` with detail like `lahman-seed@v2025.1` before clone; end retrieving before return.
- `refresh_example_network` in `src/network/example.py`: create progress once per refresh (or recreate — document choice) and pass into seed fetch **and** ensure bootstrap uses same instance if you thread it through paths; **simplest OK:** independent instances per stage as long as phase labels are correct.

### 5 — Wire `LahmanSeedHandler`

In `examples/networks/baseball/bootstrap_handlers/lahman_seed.py`:

| Step | Progress |
|------|----------|
| `ingest_warehouse` | `retrieving` with detail `building warehouse` (or call from handler before/after ingest) |
| Team loop | Optional: no separate counter required (241 rows — fast); may skip or fold into processing |
| Player loop | `processing(i, total, detail="player binds")` where `total = len(rows)` and `i` increments each iteration of `distinct_player_team_rows` loop |
| End handler | Ensure processing line ends with newline before bootstrap cleanup phase |

Prefer **one** `distinct_player_team_rows` call (already loads list) — do not re-query warehouse per row.

### 6 — Wire `DefaultSeedHandler` (light)

When `ctx.progress` set and seed people non-empty: `processing(i, len(people))` in import loop. Keep minimal.

### 7 — Tests — `tests/test_bootstrap_progress.py`

| Test | Assert |
|------|--------|
| Progress disabled | `MYCELIUM_BOOTSTRAP_PROGRESS=0` + Lahman tiny fixture → stderr lacks `Processing records` |
| Progress forced on | `MYCELIUM_BOOTSTRAP_PROGRESS=1` + tiny Lahman fixture via `run_network_bootstrap` → stderr contains all three phase labels and final `(x/y)` with `y` matching row count |
| CRM bootstrap | `test_run_network_bootstrap_crm_seed` still passes; entity counts unchanged |
| Lahman handler | Existing `test_lahman_seed_handler.py` tests green without requiring progress output |

Use `capsys` or `io.StringIO` on stderr; force non-TTY or `=1` explicitly so tests are deterministic.

### 8 — Docs

- **`examples/networks/baseball/README.md`** — one short paragraph: long bootstrap prints phase progress on stderr; `MYCELIUM_BOOTSTRAP_PROGRESS=0` silences.
- **Do not edit `TODO.md`.**

---

## Scope boundaries (strict)

**May modify:**

- `src/network/bootstrap/progress.py` (new)
- `src/network/bootstrap/context.py`
- `src/network/bootstrap/run.py`
- `src/network/seed_fetch.py`
- `src/network/example.py` (only if needed to pass progress into seed fetch)
- `src/network/bootstrap/handlers/default_seed.py`
- `examples/networks/baseball/bootstrap_handlers/lahman_seed.py`
- `tests/test_bootstrap_progress.py` (new)
- `examples/networks/baseball/README.md`

**Do not modify:**

- `src/storage/*`, specialist save paths, entity store perf
- `src/agents/entity_registry.py` (cleanup reporting stays in `run.py`)
- `admin-ui/`
- `TODO.md`

If progress from `commit_deferred_save` seems to require registry changes, **stop** and document in `output.md` — prefer `run.py` wrapper per B6.

---

## Explicit non-goals

- Incremental specialist SQLite saves (separate perf slice)
- Structured JSON progress / MCP / admin daemon streaming
- Progress for query graph or research loops
- Changing bootstrap counts, bind semantics, or deferred-save behavior
- Adding third-party progress libraries

---

## Exit criteria

| # | Criterion |
|---|-----------|
| E1 | `BootstrapProgress` exists; env + TTY gating per B4 |
| E2 | Lahman refresh shows three phases on stderr when TTY + progress on |
| E3 | Processing line shows `(x/y)` over player bind loop (~58k on full seed) |
| E4 | Cleaning up fires before deferred entity flush |
| E5 | CI/tests quiet by default (`MYCELIUM_BOOTSTRAP_PROGRESS=0` or non-TTY) |
| E6 | CRM + Lahman handler tests green |
| E7 | `./bin/ci-local` green |

---

## Governance (mandatory)

- **Do not edit `TODO.md`.** Roadmap updates are for Grok + Paul after review.
- In `output.md`, add **"For Grok + Paul"**: note for manual gate doc (optional UX note under test 5); queue status.
- Cursor delivers: code, tests, task-scoped docs, and `output.md` only.

## When finished (mandatory — see WORKFLOW.md §3)

1. `./bin/ci-local` green
2. `prompts/cursor/done/2026-06-17-2355-bootstrap-progress-reporting/` with `prompt.md` + `output.md`
3. Remove claimed file from `in-progress/` **and** ensure no duplicate remains in `next/`
4. **Do not commit or push** — tell Paul "slice ready for review"

**Suggested commit message:**

```
feat(bootstrap): stderr progress phases for long network refresh

Add BootstrapProgress (retrieving / processing x/y / cleaning up) wired
through bootstrap context, seed fetch, Lahman handler, and deferred
entity flush. TTY-aware updates; MYCELIUM_BOOTSTRAP_PROGRESS env knob.
```

---

## For Grok + Paul

After approval: optional note in timing-gates doc that operators can watch stderr during test 5; no timing expectation change from this slice alone.