# Next chunk — prep brief (Paul + Grok, June 2026)

**Prerequisite:** Manual gate **CLEAR** (2026-06-13). **Active work:** [`mvr-redesign-program.md`](mvr-redesign-program.md) (M1 queued).

**Just shipped:** Program 1 — extended attribute provenance (versioned specialist storage, admin version history, `QueryResponse.provenance`, hard cutover). Post-push admin UI: full-width version cards, formatted timestamps, `reason` / `last_error` lines.

---

## Where we are

| Track | Status |
|-------|--------|
| **Program 1 — Provenance** | **Complete** — pushed June 2026 |
| **MVR redesign** | **Locked** — slices M1–M10; [`mvr-redesign-program.md`](mvr-redesign-program.md) |
| **Program 2 — MVR / entity storage** | After MVR redesign — versioned bind, `bind_versions[]` |
| **Program 3 — Operator write** | Deferred — admin edit + force re-research |
| **Toolbox** | TBD (Paul to define) |
| **Research robustness** | Backlog — [`research-robustness-backlog.md`](research-robustness-backlog.md) |
| **Website sync** | Review [myceliumdata.org](https://myceliumdata.org) after this push (`TODO.md` process) |

`prompts/cursor/next/` is **empty** intentionally — waiting on manual gate + Program 2 lock.

---

## Recommended next program: Program 2 (MVR / entity)

**Architecture:** [`attribute-provenance-and-storage.md`](attribute-provenance-and-storage.md)

**Scope (high level):**

- Specialist-owned canonical storage for MVR fields (`name`, `employer`) with same `versions[]` model
- `bind_versions[]` audit trail on entity row
- `bind_index` replace policy (no aliases after correction)
- Unified write API: one path updates canonical value + indexes + entity cache

**Blocks:** Operator attribute correction (Program 3), full “data attribution USP” story.

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

## Design revisit (may precede or overlap Program 2)

**MVR vs resolution** — Paul (June 2026): MVR should mean *minimum data to research*, not drive record lookup. Today `name_source` / `binding` / `required_fields` conflate the two. See `TODO.md` → *MVR redesign — research gate vs record lookup*. Lock in a design session before a fix slice.

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

1. Complete **manual gate** (3 checks) — [`2026-06-12-program1-post-push-gate.md`](../manual-checks/2026-06-12-program1-post-push-gate.md)
2. Choose **next program** (Program 2 recommended)
3. **Toolbox** — brief description when ready
4. **`TODO.md`** — Grok + Paul: bump “Last updated”; note post-push + gate (Cursor does not edit `TODO.md`)

---

*Created: 2026-06-12*