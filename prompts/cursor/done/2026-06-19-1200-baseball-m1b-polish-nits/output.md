# Output — baseball M1b polish nits

## Summary

Resolved Grok review P1–P3 for M1b batting specialist without changing query contract. `career_hr==3`, provenance keys, and smoke/E2E gates unchanged.

## Changes

| Nit | Fix |
|-----|-----|
| **P1** | `career_hr()` is single source of truth; `CAREER_HR_COMPUTATION_INLINE = inspect.getsource(career_hr)`. Same pattern applied to `bio_specialist.birth_date`. |
| **P2** | `SpecialistAgent.write_na_field()` uses incremental `load_entity`/`save_entity` on `minisql_v1`; pack specialists call it instead of bulk `_mark_na`. |
| **P3** | `_overall_field_status()` helper replaces dead branching in `_evaluate_batting_fields` (mirrored in bio). |

## Tests

- `test_career_hr_provenance_shape` — asserts inline contains `SUM` and `playerID`
- `test_write_na_field_uses_incremental_save_entity` — minisql incremental path for `na` writes

## Verification

| Check | Result |
|-------|--------|
| `./bin/ci-local` | **565** smoke passed |

## For Grok + Paul

- P1–P3 resolved; no roadmap update required.
- No commit (per workflow).

**Suggested commit message:**

```
polish(baseball): align batting specialist provenance and storage paths (M1b nits)
```
