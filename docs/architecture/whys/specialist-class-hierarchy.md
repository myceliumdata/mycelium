# Why a specialist class hierarchy (framework starting points)

**Status:** Direction locked (Paul, June 2026). **M14** ships the first warehouse tier in `src/`.  
**Mechanics:** [`architecture.md`](../architecture.md) § Specialist agents · M14 prompt `2340-baseball-warehouse-stat-specialist-base-class-m14.md`

---

## The short answer

**`SpecialistAgent` is already the framework root** — storage, provenance writes, `optimize_storage`, protocol snapshots. What we lack is **middle tiers** between that root and example-network thin subclasses.

Example networks (baseball, CRM) should not each reinvent warehouse graphs, derive-on-miss, or product-specialist shells. Proven patterns move **up** into `src/agents/specialists/` so the next network author subclasses a rich base, sets `category` / `domain` / manifest, and ships.

---

## Product goal (Paul)

Framework users should inherit a **rich hierarchy of starting points**, not copy 100-line graph loops from an example pack:

| User need | Framework starting point (target) |
|-----------|-----------------------------------|
| Web research per category | Factory `ResearchSpecialist` template (CRM today) |
| Tabular warehouse stats | `WarehousePlayerStatSpecialist` / `WarehouseTeamStatSpecialist` |
| Cross-table product artifact | `ProductTeamSpecialist` (roster, franchise, …) |
| Identity / bind reads | `IdentitySpecialist` hooks (registry-first) |

Baseball is the **proving ground**; the pack keeps Lahman-specific resolver modules and manifests. The **classes** live in the framework.

---

## Current state (June 2026, post-M14)

```text
SpecialistAgent                         ← framework root (storage + I/O)
├── CRM contact_specialist              ← factory-generated research graph
├── WarehousePlayerStatSpecialist       ← framework: manifest + derive-on-miss
│   ├── BattingSpecialist               ← pack: category/domain + Lahman hooks
│   ├── PitchingSpecialist              ← derive_on_miss via manifest (pitching domain)
│   ├── BioSpecialist                   ← extends WarehouseResearchStatSpecialist
│   └── FieldingSpecialist              ← derive_on_miss via manifest (fielding domain)
├── WarehouseResearchStatSpecialist     ← warehouse + Tavily research_on_miss (bio v1)
├── WarehouseTeamStatSpecialist
│   └── TeamSeasonSpecialist
└── roster_specialist / franchise_specialist  ← product_common (ProductTeamSpecialist follow-on)
```

**Derive-on-miss:** enabled per domain via `warehouse_domains.json` → `derive_on_miss`; framework reads via `domain_meta()` (pack `derive_resolve.derive_on_miss_enabled` delegates to the same rule).

---

## Target hierarchy

```text
SpecialistAgent                         # framework — canonical storage + protocol I/O
├── ResearchSpecialistAgent             # framework — web research loop (align w/ factory template)
├── WarehousePlayerStatSpecialist       # framework — manifest resolve + optional derive-on-miss
├── WarehouseTeamStatSpecialist         # framework — team warehouse reads + scope
└── ProductTeamSpecialist               # framework — team-scoped product attrs (scope-aware cache)

examples/networks/<network>/specialists/
├── batting_specialist.py               # class BattingSpecialist(WarehousePlayerStatSpecialist)
│                                       #   category = "batting"; domain = "batting"
├── roster_specialist.py                # class RosterSpecialist(ProductTeamSpecialist)
└── …                                   # pack wires Lahman resolve/derive modules via hooks
```

**Pack responsibilities (stay in example / user network):**

- `warehouse_domains.json`, `categories.json`, ontology
- Network-specific SQL conventions module (baseball: `warehouse_resolve.py`, `derive_resolve.py`)
- Bootstrap handlers, anchors, live gate

**Framework responsibilities (promote from examples):**

- Graph entry `run(state)` patterns
- Manifest-driven derive enablement
- Scope replay from `delivery_scope_query_scope`
- Product specialist shell with **scope-aware cache keys** (M11 fix lands with `ProductTeamSpecialist`)

---

## Promotion rules

| Criterion | Promote to `src/` when |
|-----------|-------------------------|
| Used by two networks | Second warehouse or research network needs same graph |
| No Lahman literals | Entity bridge keys and table names come from manifest / hooks |
| Stable protocol | Behavior covered by smoke tests in framework or one reference pack |

**Order of work:**

1. **M14** — `WarehousePlayerStatSpecialist` + `WarehouseTeamStatSpecialist` in framework; baseball thin subclasses.
2. **Post-M14** — `ProductTeamSpecialist` (roster/franchise); scope-aware cache.
3. **Extraction review** — resolver protocols; optional `ResearchSpecialistAgent` alignment with factory template.
4. **Onboarding** — “build a warehouse network” doc points at subclassing framework tiers, not copying `pack_common.py`.

---

## What we did not do

| Anti-pattern | Why |
|--------------|-----|
| One mega `StatSpecialist` with 500 attrs in Python | Manifest + conventions (warehouse factory stack) |
| Keep hierarchy only in `examples/networks/baseball/` | Next network would fork-copy; violates framework product goal |
| Factory-generate warehouse specialists | Derive + warehouse paths are not identical to CRM research; hand-written framework bases with pack hooks |

---

## Related

- [warehouse-factory-stack.md](warehouse-factory-stack.md) — manifest routing, not flat ontology
- [specialist-owned-data.md](specialist-owned-data.md) — why graph calls `AGENT.run`, not raw JSON
- [`TODO.md`](../../../TODO.md) — M14, framework extraction review, stat specialist doc