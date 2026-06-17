# Query grain router — multi-grain fan-out + disambiguation

> **READY** — Claim per `prompts/cursor/WORKFLOW.md` (move to `in-progress/` before starting). **Run after** `2026-06-17-2000-baseball-closed-identity-lazy-aliases` (closed grains, lazy aliases, `add_field_alias`).

**Priority:** Slice 3 of baseball identity program. Paul + Grok design locked June 2026.

**Parent:** [`docs/plans/baseball-example-program.md`](../../../docs/plans/baseball-example-program.md) — query grain selection; [`done/2026-06-17-1400-multi-mvr-entity-stores/`](done/2026-06-17-1400-multi-mvr-entity-stores/) — per-grain stores (query path still default-grain only).

**Principles:**

- **Framework generic** — no baseball/Lahman strings or imports in `src/`. Router uses `mvr.grains`, `guide.md`, registry hits. Baseball examples live in tests + `examples/networks/baseball/`.
- **CRM unchanged** — single-grain networks behave as today when fan-out degenerates to one grain.
- **Docs are mandatory** — ship `docs/query-grain-router.md` with mermaid flows (Paul: “pretty complicated”).

---

## Problem (posterity)

`target_resolve` always uses `get_entity_registry()` / `load_mvr()` for **default grain only**. Baseball has **team** + **player** grains; team queries cannot resolve. Paul locked a **fan-out router**: lookup all grains (filtered keys), disambiguate when multiple grains hit, integrate 0-hit lazy-alias pipeline from slice 2.

---

## Locked behavior (Paul + Grok — do not reinterpret)

### Fan-out (per-grain lookup filtering)

For each declared grain `g`:

1. `filtered = {k:v for k,v in lookup.items() if k in g.bind_fields}`.
2. If `filtered` empty → **skip** `g` (no lookup, no 0-hit alias on `g`).
3. Else `lookup_by_target_lookup(filtered)` on **`g`’s registry**.

**Examples (document in router doc):**

| `lookup` | Team grain | Player grain |
|----------|------------|--------------|
| `{name: y, team: x}` | `{name: y}` only | `{name: y, team: x}` |
| `{team: x}` only | skip | `{team: x}` |
| `{name: y}` | `{name: y}` | `{name: y}` |

Agents use **`name`** for team-grain queries; key **`team`** applies to **player** grain only — state clearly in docs/MCP examples.

### 0 hits everywhere

1. Fan-out → all grains skipped or all return `[]`.
2. **Lazy alias expansion** (slice 2) on each **closed** grain that had non-empty `filtered` lookup.
3. **Re-fan-out** same lookup.
4. Still 0 → `lookup_suggested` / `not_found` on closed grains; **never** `create_pending`.

### Single grain with hits

- 1 id → `lookup_resolved` (`total_matches=1`).
- 2+ ids on **same grain** → standard multi-match (`lookup_resolved`, `total_matches>1`) — **no** disambiguation LLM.

### Disambiguation LLM — trigger A (locked)

Invoke **only when ≥2 grains** each have **≥1 hit**.  
Examples: **no LLM** for `{name: "Dodgers"}` (2 team, 0 player). **LLM** for `{name: "Washington"}` when both team and player registries hit.

**Not** the slice-2 alias LLM (0-hit). New generic **grain disambiguation** module.

### Disambiguation LLM output (all three — locked)

Structured response, mutually exclusive:

| Outcome | Action |
|---------|--------|
| `chosen: {grain, entity_id}` | Single resolve on that grain |
| `chosen_grain: "…"` | Use all hits **on that grain only** (1 → resolved, 2+ → multi-match) |
| `ambiguous` | **3c** below |

Mockable when `OPENAI_API_KEY` unset (tests).

### Cross-grain ambiguous — 3c (locked)

When LLM returns `ambiguous` (e.g. 1 team + 1 player for same string): **`lookup_suggested`** with candidates tagged with **`grain`**, `id`, `suggested_lookup`. **No** mixed-grain `delivery_id` in v1. User/agent picks → new step 1 (optional `grain` override).

Within **one grain**, existing multi-match delivery unchanged.

### `id`-only step 1 (locked)

Search **all grains** for uuid when `grain` omitted. 0 → `not_found`; 1 → resolve with that grain on delivery; 2+ → `not_found` (data error). No LLM.

### Optional `EntityQuery.grain` (locked)

When set on step 1: **skip** fan-out and disambiguation LLM; single-grain path (slice 2 closed + lazy alias on that grain only). For tests, MCP, power users.

### Delivery scope (locked)

Persist **`grain`** on delivery at issue time (from resolved grain). Step 2 loads correct registry/MVR. Multi-match within one grain: single `grain`, multiple `entity_ids`.

### CRM (locked)

Single grain → no behavioral change; capstones green.

---

## Implement

### Router module (`src/agents/` — name flexible)

- `resolve_target_step1_multi_grain(query) -> TargetResolveResult` or integrate into `target_resolve.py`.
- Orchestrates: optional grain override → id search → fan-out → 0-hit pipeline → single-grain resolve → disambiguation LLM → 3c suggest.
- Call slice-2 alias expansion and slice-1 registry APIs; **no** baseball imports.

### Disambiguation LLM

- Inputs: `guide.md`, grain descriptions from manifest, list of `{grain, entity_id, bind_values}` hits.
- Outputs: `chosen` | `chosen_grain` | `ambiguous` per locked table.

### Models / protocol

- Optional `grain: str | None` on `EntityQuery` (step 1 only; validate against manifest grains).
- `grain` on `DeliveryScope` / delivery store.
- `LookupSuggestion` or suggest payloads include **`grain`** when multi-grain suggest (3c).
- MCP / `describe_network` / introspection: document team uses `name` key; update JSON schema examples.

### Docs (mandatory)

**`docs/query-grain-router.md`** with:

1. Fan-out + filtering table (human/agent note on `{team}` vs `{name}`).
2. Mermaid: 0-hit pipeline.
3. Mermaid: multi-grain disambiguation.
4. Trigger A examples (Dodgers vs Washington).
5. 3c suggest flow.
6. Optional `grain` override.
7. Link from `docs/architecture.md` (one paragraph).

### Tests

| Test | Assert |
|------|--------|
| CRM capstones / employer partial multi-match | Unchanged |
| `{name, team}` fan-out | Team filtered to `{name}` only |
| `{team: x}` only | Team skipped, player searched |
| Mock disambiguation: 2 grains hit → `chosen_grain: "team"` | Team multi-match only |
| Mock `ambiguous` | `lookup_suggested` with per-candidate `grain` |
| `id` in one grain | Resolves with `delivery.grain` |
| `EntityQuery.grain: "team"` | Skips fan-out |
| `./bin/ci-local` | Green |

Use baseball fixtures in tests; **no** `baseball` / `lahman` literals in `src/`.

---

## Scope boundaries (strict)

**May modify:**

- `src/agents/target_resolve.py`, new router/disambiguation modules
- `src/models/state.py` (`EntityQuery`, `LookupSuggestion` if needed)
- `src/network/delivery.py` (delivery `grain`)
- `src/agents/dispatch.py`, `src/agents/responses.py` (suggest `grain`)
- `src/mycelium_mcp/server.py`, `src/network/introspection.py` (schema copy)
- `tests/`
- `docs/query-grain-router.md`, short `architecture.md` link

**Do not modify:**

- `examples/networks/baseball/bootstrap_handlers/` (except README cross-link optional)
- Warehouse / stats / derivatives
- Cross-grain single delivery (3b)
- `TODO.md`

---

## Explicit non-goals

- Natural-language supervisor routing (NL → grain)
- Cross-grain roster + career in one delivery
- Mixed-grain step-2 assembly (3b)
- Changing lazy-alias LLM prompt content (slice 2)

---

## Exit criteria

| # | Criterion |
|---|-----------|
| E1 | Fan-out with per-grain filtering; skip empty filtered |
| E2 | 0-hit pipeline matches locked behavior |
| E3 | Disambiguation LLM trigger A only; mock tests |
| E4 | 3c cross-grain `ambiguous` → `lookup_suggested` + `grain` |
| E5 | `delivery.grain` set and honored on step 2 |
| E6 | `docs/query-grain-router.md` complete with mermaid |
| E7 | No baseball-specific code in `src/` |
| E8 | `./bin/ci-local` green |

---

## Grok review gate

Grok will reject if review finds Lahman/baseball branches in `src/` or missing router doc.

## Governance (mandatory)

- **Do not edit `TODO.md`.**
- **For Grok + Paul** in `output.md`: MCP client follow-ups; derivative `create_pending` deferred.

## When finished

Per `prompts/cursor/WORKFLOW.md` — no commit/push.

**Suggested commit message:**

```
feat(resolve): multi-grain query router and delivery grain

Fan-out lookup per MVR grain with LLM disambiguation on multi-grain
hits; 0-hit lazy-alias retry; cross-grain ambiguous uses lookup_suggested.
```