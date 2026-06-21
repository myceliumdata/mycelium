# Baseball multi-domain derive + live gate — output

## Summary

Enabled manifest-driven `derive_on_miss` on **pitching** and **fielding**, fixed framework to pass `domain=self.domain` into `generate_and_run_derive`, and added five live gate derive scenarios with SQL-discovered anchors. **`bb-pitch-03` unchanged** — `career_era` still resolves via `career_era_weighted` manifest path.

## Discovery SQL + anchors (Nolan Ryan `ryanno01`, Aaron `aaronha01`)

```sql
-- Pitching (Ryan)
SELECT
  (SUM(BB) + SUM(H)) * 1.0 / (SUM(IPouts) / 3.0) AS career_whip,
  SUM(SO) * 9.0 / (SUM(IPouts) / 3.0) AS k_per_9,
  SUM(IPouts) / 3.0 AS career_innings_pitched
FROM Pitching WHERE playerID='ryanno01';

-- Fielding (Aaron)
SELECT (SUM(PO) + SUM(A)) * 1.0 / (SUM(PO) + SUM(A) + SUM(E))
FROM Fielding WHERE playerID='aaronha01';
```

| Anchor key | Value | Gate tolerance |
|------------|-------|----------------|
| `pitcher_career_whip` | **1.247** | 0.01 |
| `pitcher_k_per_9` | **9.548** | 0.05 |
| `pitcher_career_innings_pitched` | **5386** | 0.1 |
| `fielding_percentage` | **0.982** | 0.0001 |

## Live gate

| Item | Value |
|------|-------|
| New scenarios | `bb-derive-04` … `bb-derive-08` |
| Total catalog | **34** (27 prior + 5 derive + 2 bio from `2410`) |
| `bb-pitch-03` | Manifest-only `career_era` — verified smoke |

Paul: run `./bin/gate-live baseball` with `OPENAI_API_KEY` — derive phase needs keys; expect **34/34** (includes `2410` bio scenarios).

## Key changes

| Area | Change |
|------|--------|
| Framework | `domain=self.domain` in `resolve_derive_on_miss` |
| Manifest | `derive_on_miss: true` on pitching + fielding |
| Pack | `derive_resolve._audit_line` uses domain specialist name |
| Gate | `RATE_DRIFT_ATTRS` + drift checks for new attrs |
| Tests | `test_baseball_pitching_derive.py`, `test_baseball_fielding_derive.py`, domain unit test |

## Verification

```text
./bin/ci-local    # 655 passed
```

## For Grok + Paul

- Mark **2400** shipped; live gate target **34/34** with `2410`.
- `bb-derive-08` may create `intent_map` entry `whip` → `career_whip` on first live run — note in gate output if synonym timestamp check fails once.
- Optional 4th pitching stat (`career_winning_percentage`) deferred.

Suggested commit message:

```
feat(baseball): multi-domain derive-on-miss + live gate (pitching, fielding)
```
