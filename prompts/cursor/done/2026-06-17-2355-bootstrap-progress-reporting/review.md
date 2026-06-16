# Review: Bootstrap progress reporting (stderr phases + x/y)

**Verdict:** **Approved + polish nits**  
**Reviewer:** Grok  
**Date:** 2026-06-17

---

## CI

| Suite | Result |
|-------|--------|
| `./bin/ci-local` (Grok re-run) | **466 passed**, 97 deselected; ruff clean; admin-ui build ok |

---

## Delivery

| Artifact | Status |
|----------|--------|
| `src/network/bootstrap/progress.py` | ✅ `BootstrapProgress`, env + TTY gating |
| `src/network/bootstrap/run.py` | ✅ Cleaning up before deferred flush |
| `src/network/bootstrap/context.py` | ✅ `progress` on context |
| `src/network/seed_fetch.py`, `example.py`, `seed_import.py` | ✅ Shared reporter through refresh |
| `lahman_seed.py`, `default_seed.py` | ✅ Warehouse retrieving + player `(x/y)` |
| `tests/test_bootstrap_progress.py` | ✅ 4 smoke tests |
| `examples/networks/baseball/README.md` | ✅ Operator note |
| `prompt.md` + `output.md` | ✅ |
| Prompt removed from `next/` | ✅ |

---

## Spec compliance

| # | Criterion | Status |
|---|-----------|--------|
| E1 | Env + TTY gating (`MYCELIUM_BOOTSTRAP_PROGRESS`) | ✅ |
| E2 | Three phase labels on stderr when enabled | ✅ |
| E3 | Processing `(x/y)` on player bind loop | ✅ |
| E4 | Cleaning up before deferred entity flush | ✅ |
| E5 | CI/tests quiet when progress off | ✅ |
| E6 | CRM + Lahman tests green | ✅ |
| E7 | `./bin/ci-local` green | ✅ |

Locked B1–B9: Pass.

---

## Diff reviewed

- `src/network/bootstrap/progress.py` (full)
- `src/network/bootstrap/run.py`, `context.py`
- `src/network/example.py`, `seed_fetch.py`, `seed_import.py`
- `src/network/bootstrap/handlers/default_seed.py`
- `examples/networks/baseball/bootstrap_handlers/lahman_seed.py`
- `tests/test_bootstrap_progress.py` (full)
- `tests/test_example_network.py`, `tests/test_seed_fetch.py` (signature updates)
- `examples/networks/baseball/README.md`

---

## Design critique

**Strong:**

- Small, focused module; no third-party deps.
- TTY `\r` vs non-TTY coarse emit matches prompt.
- Single `BootstrapProgress` instance threaded refresh → fetch → bootstrap.
- Lahman preloads `player_rows` once (no double warehouse query).
- CRM path unchanged when progress off (entity count test).

**Nits (resolved in `9052f45` follow-up):**

1. ~~`run.py` duplicated `bootstrap_deferred_save()`~~ — now uses `bootstrap_deferred_save(before_commit=...)`.
2. ~~`seed_fetch` typed progress as `object`~~ — now `BootstrapProgress | None`.
3. ~~`HOLD.md` stale~~ — fixed on initial commit.

---

## Nits

See design critique #1–#2. Logged here only (no program polish backlog for ad-hoc UX slice).

---

## For Paul

- **Commit:** `feat(bootstrap): stderr progress phases for long network refresh` (below).
- **Next:** incremental specialist writes (`2340`) — perf fix before re-benchmarking.
- **Test 5:** If still running, stderr will not show progress until this commit is in the tree; re-run optional for UX validation only.
- **Push:** local only until you ask.