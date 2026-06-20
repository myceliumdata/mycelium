# Baseball warehouse stat specialist base class + manifest-driven derive (M14)

> **READY** — Pack refactor. Claim after M13 (`2260`) and bootstrap perf (`2280`) are **Approved** (or Paul waives). Run **before** polish capstone (`2350`). **Do not edit `TODO.md`.**

## Objective

Consolidate warehouse **player stat** specialists onto a shared **base class** (same design discipline as CRM `SpecialistAgent` + factory template): derive-on-miss, manifest conventions, and graph wiring live in the base; domain modules are thin subclasses.

Today only `batting_specialist.py` carries ~100 lines of derive callbacks; pitching/bio/fielding omit them. `derive_resolve.py` is already domain-parameterized; enablement should be **`warehouse_domains.json` → `derive_on_miss`**, not per-file copy-paste.

## Design (locked — class-based)

Introduce in the baseball pack (framework promotion is a later extraction slice):

| Class | Extends | Declares | `run()` behavior |
|-------|---------|----------|------------------|
| **`WarehousePlayerStatSpecialist`** | `SpecialistAgent` | `domain: str` (manifest key) | `run_warehouse_player_graph` with derive hooks from manifest |
| **`WarehouseTeamStatSpecialist`** | `SpecialistAgent` | `domain: str` | `run_warehouse_team_graph` (no derive v1) |

**Thin subclasses** (each file ~15 lines after refactor):

- `BattingSpecialist(WarehousePlayerStatSpecialist)` — `category = "batting"`, `domain = "batting"`
- `PitchingSpecialist(WarehousePlayerStatSpecialist)` — `category = "pitching"`, `domain = "pitching"`
- `BioSpecialist(WarehousePlayerStatSpecialist)` — `category = "bio"`, `domain = "bio"`
- `FieldingSpecialist(WarehousePlayerStatSpecialist)` — `category = "fielding"`, `domain = "fielding"`
- `TeamSeasonSpecialist(WarehouseTeamStatSpecialist)` — `category = "team_season"`, `domain = "team_season"`

**Base class responsibilities** (not free-function callbacks passed ad hoc):

- `derive_on_miss_enabled()` — read manifest for `self.domain`
- `resolve_derive_on_miss(key, ...)` — move logic from `_batting_derive_on_miss_resolve` (intent slug, cache, `generate_and_run_derive`)
- `run(state)` — wire graph with `on_miss` / `on_miss_resolve` bound to instance methods when manifest flag set

Prefer new module `warehouse_stat_specialist.py` (or `pack_stat_specialist.py`) sibling to `pack_common.py`; keep `pack_common` as graph/evaluate helpers the base class calls.

**Do not** use a different pattern (manifest-only hooks with no base class) — Paul lock: match CRM class isolation.

## Manifest

- `batting` domain: keep `"derive_on_miss": true`
- Other player domains: **unchanged** (`false` / omitted) unless you add a mocked derive smoke for pitching in this slice (optional, not required)
- Document in `output.md` how to enable derive on another domain (flip JSON flag only)

## Tests

- Existing batting derive smokes (`career_avg` / `ops` mocked) must pass unchanged
- `test_career_hr_ignores_year_scope` and warehouse read smokes for pitching/bio/fielding/team_season unchanged
- Add one unit-style test: `WarehousePlayerStatSpecialist.derive_on_miss_enabled` respects manifest flag (minimal manifest fixture)

## Live gate

**N/A** — refactor only; existing scenarios must keep passing.

## Constraints

- No framework `src/` moves in this slice (pack only); note promotion candidates in `output.md` for extraction review.
- `./bin/ci-local` must pass.
- CRM unchanged.
- Product specialists (`roster`, `franchise`, identity) **out of scope**.

## Output

Follow `prompts/cursor/WORKFLOW.md`. In `output.md` **For Grok + Paul**:

- Before/after line counts for batting_specialist vs base class
- How subclasses enable derive (manifest flag table)
- Framework promotion notes for `WarehousePlayerStatSpecialist`

Suggested commit message:

```
refactor(baseball): warehouse stat specialist base class + manifest derive
```