# Review — baseball derive codegen sandbox (M3)

**Verdict:** **Approved + polish nits**  
**Reviewer:** Grok  
**Date:** 2026-06-19

## CI

| Check | Result |
|-------|--------|
| `./bin/ci-local` | **574** smoke passed, ruff clean, admin-ui build ok |
| `./bin/smoke-baseball-e2e` | **11** scenarios passed |
| M3 pytest subset | `test_derive_sandbox` (3) + `test_baseball_career_avg_derive` (2) + `test_baseball_batting_specialist` (6) — **11** passed |

## Delivery

`output.md` matches commit `35a89ab` (already on `main` locally). All prompt deliverables present on disk.

| File | Role |
|------|------|
| `src/network/derive_sandbox.py` | AST validation + restricted exec |
| `examples/networks/baseball/specialists/derive_resolve.py` | Pack LLM orchestration |
| `examples/networks/baseball/specialists/batting_specialist.py` | Derive path after M2 miss |
| `examples/networks/baseball/specialists/specialist_loader.py` | `load_derive_resolve()` |
| `examples/networks/baseball/warehouse_domains.json` | `derive_candidates: ["career_avg"]` |
| `tests/test_derive_sandbox.py` | Sandbox unit tests |
| `tests/test_baseball_career_avg_derive.py` | Mocked LLM e2e + cache + provenance |

## Diff reviewed

Full read of all files in `35a89ab` (9 files, +580 lines). No `/review` subagent — diff size moderate.

## Spec compliance

| Criterion | Result |
|-----------|--------|
| M2 alias path unchanged (`career_hr` no LLM) | Pass |
| Alias miss (`career_avg`) → derive once, cache on success | Pass |
| LLM / sandbox failure → `N/A`, no partial value | Pass |
| Provenance: `computation.inline` + full `parameters` | Pass |
| Framework sandbox + pack orchestration split | Pass |
| `derive_candidates` manifest gate | Pass |
| Mocked LLM tests CI-green without `OPENAI_API_KEY` | Pass |
| `career_avg` format locked **0.500** (fixture), three decimals | Pass |

## Legacy / dual-path

`test_baseball_batting_specialist.py` career_hr paths unchanged. M2 warehouse resolve still first; derive only when `resolve_domain_attribute` returns `None` and attr ∈ `derive_candidates`.

## Tests

**Strong:** sandbox rejects imports; e2e proves `0.500`, provenance inline + `parameters.warehouse` / `attribute`, second deliver skips LLM (counter=0).

**Gaps (non-blocking):** no test that non-candidate unaliased attr skips LLM; no test for sandbox rejection at orchestration layer (derive → `N/A`).

## Design critique

**Strong:** Correct layer-3 placement — framework owns sandbox safety, pack owns prompt + Lahman context. `derive_candidates` prevents LLM on every manifest miss. Fail-closed to `write_na_field` matches M2 sticky-`N/A` semantics. Provenance envelope aligns with [computation-centric-provenance.md](../../../docs/architecture/whys/computation-centric-provenance.md).

**Sub-optimal (v1 acceptable):** AST allowlist blocks `import` and named forbidden calls but does not restrict `Path.read_text()` / other `Path` methods — LLM could read outside warehouse if prompted badly. Tighten in a future sandbox hardening slice if live codegen misbehaves.

**Sub-optimal (minor):** `generate_and_run_derive` swallows all exceptions silently — correct for deliver UX, but debug logging would help operators.

## Nits (non-blocking)

| # | Nit | Suggested follow-up |
|---|-----|---------------------|
| N1 | Hand-test doc still lists `career_avg` → `N/A` | Update [`docs/manual-checks/2026-06-19-baseball-specialist-hand-test.md`](../../../docs/manual-checks/2026-06-19-baseball-specialist-hand-test.md) gate rows + add M3 manual step (clear batting storage, `provenance: true`, expect ≈ `0.305` on full Lahman) |
| N2 | `CAREER_AVG_SOURCE` duplicated in `test_derive_sandbox.py` and `test_baseball_career_avg_derive.py` | Shared fixture constant in `tests/` helper (polish) |
| N3 | No `smoke-baseball-e2e` scenario for `career_avg` | Optional row with env-guarded mock or document pytest-only (prompt allowed either) |
| N4 | Sandbox Path method allowlist | Future slice if codegen abuse seen in manual gate |

Program polish backlog: baseball program doc § M3 row when Paul confirms manual Lahman gate.

## For Paul

- **Commit:** Already landed as `35a89ab` (`baseball: LLM derive sandbox for career_avg (M3)`). This review adds `review.md` only.
- **Manual gate:** Clear `agents/batting/storage.json` if stale `N/A` for `career_avg`; deliver Hank Aaron with `provenance: true` on full Lahman — expect ≈ **`0.305`**, inline `computation` with `query_warehouse`, `parameters.warehouse` + `lahman.playerID`.
- **M4+:** free-form `derive` label / intent hash — not in scope; queue when ready.
- **Push:** Local only until you ask.