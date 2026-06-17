# Review — baseball partial player lookup (CRM parity)

**Verdict: Approved + polish nits**

## CI

| Step | Result |
|------|--------|
| `./bin/ci-local` | Pass — **502** smoke, 98 deselected; ruff clean; admin-ui build ok |

## Delivery

`output.md` matches diff: 6-line routing fix in `target_resolve.py`, 3 test updates/additions, router doc + hand plan Q17 + `guide.md`. No scope creep.

## Diff reviewed

| File | Notes |
|------|-------|
| `src/agents/target_resolve.py` | `lookup_incomplete` + `inference.grain` → `_resolve_single_grain_step1` |
| `tests/test_strict_grain_routing.py` | Unknown → incomplete; Washington → resolved; John Smith homonym → 2 matches |
| `docs/query-grain-router.md` | `{player}` partial row + step 4 delegation note |
| `docs/manual-checks/2026-06-18-baseball-query-hand-test-plan.md` | Q05/Q17 + matrix G; intro summary table still stale (nit) |
| `examples/networks/baseball/guide.md` | Partial `{player}` sentence |

## Spec compliance

| Criterion | Result |
|-----------|--------|
| Delegate to `_resolve_single_grain_step1` (no duplicate logic) | Pass |
| `infer_grain_from_lookup` unchanged | Pass |
| CRM single-grain unchanged | Pass (502 smokes include CRM clarity tests) |
| Closed grain — no `create_pending` on partial 0-hit | Pass |
| Tests: unknown incomplete, unique resolved, homonym multi | Pass |
| Docs: router, hand plan, guide | Pass (intro table nit) |
| No entity store / bootstrap change | Pass |

## Legacy / dual-path

Full `{player, team}`, `{team}`, `id`, bind_index alias (1000), team closed aliases — unchanged per existing smokes.

## Design critique

**Strong:** Minimal fix at the right layer — multi-grain routing was short-circuiting before the resolver that already implements CRM partial behavior. Framework-generic (any multi-grain partial subset with unambiguous grain).

**No concerns:** Homonym multi-match matches CRM `645 Ventures` pattern. Partial lookup correctly skips `bind_index` (full MVR only).

## Nits

| ID | Severity | Item |
|----|----------|------|
| N1 | Non-blocking | Hand test plan **intro table** (lines 9–14) still says `{player}` only → always `lookup_incomplete`; body Q17 and matrix G are correct. Grok fixes intro on commit. |

## For Paul

- **Commit:** `fix: delegate partial multi-grain lookups to single-grain resolver (CRM parity)`
- **No re-bootstrap** — run Q17 on existing benchmark root after pull.
- **Hand test:** Q17 `{"player": "Hank Aaron"}` → `lookup_resolved`; Q05 unknown → incomplete.
- **Next:** baseline stat specialists / `requested_attributes` when ready; push when program gate CLEAR.