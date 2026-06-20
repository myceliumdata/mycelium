# Baseball warehouse stat specialist base class + manifest-driven derive (M14)

> **READY** — **Framework + pack** refactor. Claim after M13 (`2260`) and bootstrap perf (`2280`) are **Approved** (or Paul waives). Run **before** polish capstone (`2350`). **Do not edit `TODO.md`.**

## Objective

Consolidate warehouse **player/team stat** specialists onto **framework base classes** subclassing `SpecialistAgent`, with baseball pack modules as thin declarations (`category`, `domain`, pack resolver hooks).

Paul lock (June 2026): example-network patterns move **up** into the framework so users inherit rich starting points — not pack-only base classes. Read [`docs/architecture/whys/specialist-class-hierarchy.md`](../../../docs/architecture/whys/specialist-class-hierarchy.md).

Today only `batting_specialist.py` carries ~100 lines of derive logic; other stat specialists are thin wrappers around `pack_common` functions. `derive_resolve` is domain-parameterized; enablement must be **`warehouse_domains.json` → `derive_on_miss`**.

## Design (locked — framework hierarchy)

### Framework (`src/agents/specialists/`)

Add **`warehouse_stat.py`** (names negotiable in `output.md` if clearer):

| Class | Extends | Declares | `run()` behavior |
|-------|---------|----------|------------------|
| **`WarehousePlayerStatSpecialist`** | `SpecialistAgent` | `domain: str` (manifest key) | Warehouse player graph + manifest-driven derive-on-miss |
| **`WarehouseTeamStatSpecialist`** | `SpecialistAgent` | `domain: str` | Warehouse team graph (no derive v1) |

**Framework base responsibilities:**

- `run(state)` — canonical graph entry (move orchestration out of per-network specialists)
- `derive_on_miss_enabled()` — read manifest for `self.domain` (via existing `warehouse_manifest` / domain meta helpers in `src/network/`)
- `resolve_derive_on_miss(...)` — intent slug + cache + derive pipeline (logic from `_batting_derive_on_miss_resolve`)
- **Pack hooks** (subclass or class attributes — document choice): load network-specific `warehouse_resolve` / `derive_resolve` without `src/` importing `examples/`. Prefer explicit override methods on baseball subclasses, e.g. `_load_warehouse_resolve()`, `_load_derive_resolve()`, returning pack modules.

**Keep in `pack_common` (or migrate only what is network-agnostic):** low-level `evaluate_*_warehouse_fields`, `query_year_id`, response contrib assembly — framework base **calls** these; do not duplicate graph loops.

**Export** new classes from `src/agents/specialists/__init__.py` or documented import path for pack authors.

### Baseball pack (`examples/networks/baseball/specialists/`)

Thin subclasses only (~15 lines each):

- `BattingSpecialist(WarehousePlayerStatSpecialist)` — `category = "batting"`, `domain = "batting"`
- `PitchingSpecialist(WarehousePlayerStatSpecialist)` — `category = "pitching"`, `domain = "pitching"`
- `BioSpecialist(WarehousePlayerStatSpecialist)` — `category = "bio"`, `domain = "bio"`
- `FieldingSpecialist(WarehousePlayerStatSpecialist)` — `category = "fielding"`, `domain = "fielding"`
- `TeamSeasonSpecialist(WarehouseTeamStatSpecialist)` — `category = "team_season"`, `domain = "team_season"`

`batting_specialist.py` must shrink to subclass + `AGENT` singleton — no inline derive callbacks.

**Do not** implement hierarchy only under `examples/` — Paul lock.

### Out of scope (document as follow-on in `output.md`)

- `ProductTeamSpecialist` for roster/franchise (separate slice after M14)
- Promoting `warehouse_resolve.py` / `derive_resolve.py` into `src/` (extraction review)
- CRM / factory template alignment with `ResearchSpecialistAgent`

## Manifest

- `batting` domain: keep `"derive_on_miss": true`
- Other player domains: unchanged unless optional mocked pitching derive smoke added
- Document in `output.md`: enable derive on any domain by flipping JSON only

## Tests

| Layer | Tests |
|-------|--------|
| Framework | Unit tests for `WarehousePlayerStatSpecialist.derive_on_miss_enabled` (minimal manifest fixture); no baseball root required |
| Pack | Existing batting derive smokes, career_hr scope, pitching/bio/fielding/team_season smokes unchanged |
| CRM | Regression — framework change must not break CRM specialists |

## Live gate

**N/A** — refactor only; all existing baseball scenarios must pass after Paul's `--sync-only`.

## Constraints

- **`src/agents/specialists/` changes required** — this is a framework slice, not pack-only.
- No `examples/` imports from `src/` (pack hooks only).
- `./bin/ci-local` must pass.
- Product specialists (`roster`, `franchise`, identity) untouched.

## Output

Follow `prompts/cursor/WORKFLOW.md`. In `output.md` **For Grok + Paul**:

- Hierarchy diagram: `SpecialistAgent` → framework warehouse bases → baseball subclasses
- Before/after line counts (`batting_specialist.py`)
- Manifest derive flag table
- List of `pack_common` symbols still in pack vs candidates for next promotion
- Pointer to `docs/architecture/whys/specialist-class-hierarchy.md`

Suggested commit message:

```
feat(specialists): warehouse stat base classes + baseball thin subclasses (M14)
```