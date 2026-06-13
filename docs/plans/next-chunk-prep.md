# Next chunk — prep brief (Paul + Grok, June 2026)

**Prerequisite:** MVR redesign manual gate — [`2026-06-13-mvr-redesign-post-program-gate.md`](../manual-checks/2026-06-13-mvr-redesign-post-program-gate.md).

**Just shipped (local, not pushed):** MVR redesign M1–M10 — target two-step protocol on CLI/MCP/admin; batch deliver; create-on-deliver; metering; admin-ui two-step form.

---

## Where we are

| Track | Status |
|-------|--------|
| **Program 1 — Provenance** | **Complete** — pushed June 2026 |
| **MVR redesign** | **Complete** (M1–M10, June 2026) — [`mvr-redesign-program.md`](mvr-redesign-program.md) |
| **Program 2 — MVR / entity storage** | **Next** — versioned bind, `bind_versions[]`, deferred M10 nits |
| **Program 3 — Operator write** | Deferred — admin edit + force re-research |
| **Toolbox** | TBD (Paul to define) |
| **Research robustness** | Backlog — [`research-robustness-backlog.md`](research-robustness-backlog.md) |
| **Website sync** | Review [myceliumdata.org](https://myceliumdata.org) after this push (`TODO.md` process) |

`prompts/cursor/next/` is **empty** — MVR program done; waiting on post-program manual gate + Program 2 lock.

---

## Recommended next program: Program 2 (MVR / entity)

**Architecture:** [`attribute-provenance-and-storage.md`](attribute-provenance-and-storage.md)

**Scope (high level):**

- Specialist-owned canonical storage for MVR fields (`name`, `employer`) with same `versions[]` model
- `bind_versions[]` audit trail on entity row
- `bind_index` replace policy (no aliases after correction)
- Unified write API: one path updates canonical value + indexes + entity cache

**Blocks:** Operator attribute correction (Program 3), full “data attribution USP” story.

**Folded from MVR M10 post-ship nits** (no separate remedial slice):

| Item | Program 2 action |
|------|------------------|
| `bind_provisional_from_scope` still `bind_provisional(name, employer)` only | Generalize when MVR bind fields move to specialist-owned storage |
| Target-path `payment_required` smoke | Add when payment surfaces expand in P2/P3 |
| Admin-ui query e2e test | Optional — API tests cover contract; add Playwright/component test if admin grows |
| `health_check` lightweight ping (P26) | Defer unless MCP liveness becomes hot path |

---

## Decisions to make together (Program 2 lock)

These are the open questions from the architecture doc. Defaults apply if we stay silent — confirm or override.

| # | Question | Default | Paul call |
|---|----------|---------|-----------|
| **Q1** | `bind_versions[]` on entity row vs sidecar `entities_history.json`? | On entity row | |
| **Q2** | MVR → specialist mapping: hardcoded CRM map vs `network.json` driven? | Hardcoded v1 | |
| **Q4** | Re-research after operator override: block / warn / allow with new version? | Block overwrite of `actor: operator` without explicit force | |
| **P5–P6** | Replace bind-key policy (no aliases) — acceptable for CRM + future networks? | Locked in arch doc | |
| **Slice map** | How many Cursor slices? Suggested: **2a write**, **2b read/admin**, **2c polish** (mirror Program 1) | TBD | |

**Architecture sign-off checklist** (from architecture doc):

- [ ] Three-layer model (canonical / indexes / protocol) matches mental model
- [ ] Program 2 slice map agreed
- [ ] Q1, Q2, Q4 decided

Once locked → Grok writes `attribute-provenance-program2.md` + queues slice prompts.

---

## Alternative / parallel tracks (if not Program 2)

| Track | Why consider | Dependency |
|-------|--------------|------------|
| **Program 3 — Operator correction** | Paul Murphy LinkedIn wrong-URL case; admin “edit value” | Program 2 (bind + unified write) |
| **Research robustness** | Multi-identity → `na`, source-quality rules | Independent; complements provenance |
| **Toolbox** | Paul mentioned — scope unknown | Paul defines |
| **Admin: binding context + write actions** | `TODO.md` Admin UI v2 deferred items | Program 3 |
| **Thread merge semantics** | Same `thread_id`, new attributes without redundant research | Independent |
| **Website copy** | Post-push architecture alignment | Sibling repo `mycelium-website` |

---

## What Grok is ready to do now (no code)

1. **Program 2 design session** — walk Q1/Q2/Q4, draft program spec + slice map
2. **Website diff** — compare site to new provenance / version history capabilities
3. **Toolbox intake** — once Paul describes it, place on roadmap

## What waits on Paul

1. Complete **MVR post-program gate** — [`2026-06-13-mvr-redesign-post-program-gate.md`](../manual-checks/2026-06-13-mvr-redesign-post-program-gate.md)
2. Push `origin` when satisfied (13 local commits ahead)
3. Lock **Program 2** (design session)
3. **Toolbox** — brief description when ready
4. **`TODO.md`** — Grok + Paul: bump “Last updated”; note post-push + gate (Cursor does not edit `TODO.md`)

---

*Created: 2026-06-12*