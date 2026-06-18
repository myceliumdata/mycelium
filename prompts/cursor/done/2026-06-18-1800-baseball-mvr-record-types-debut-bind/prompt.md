# Baseball player MVR + `record_type` / `new_records` vocabulary

> **READY** — Claim per `prompts/cursor/WORKFLOW.md` (move to `in-progress/` before starting).

**Priority:** Design lock from Paul + Grok (June 2026). Single cohesive slice: framework vocabulary rename, baseball player bind shape, Lahman bootstrap rewrite, partial 0-hit fix for `bootstrap_only` record types.

**Parent:** [`docs/plans/baseball-example-program.md`](../../docs/plans/baseball-example-program.md); conversation lock on `player` + `debut_team` + `debut_year` MVR.

**Principles:**

- **Framework generic** — `record_type` and `new_records` apply to all networks; no Lahman strings in `src/`.
- **Fail fast** — reject legacy manifest keys (`grains`, `default_grain`, `identity_mode`, `seed_grain`). No silent aliases.
- **Required `new_records`** — every `record_type` must declare `bootstrap_only` or `query_allowed`.
- **CRM behavior preserved** — `query_allowed` person record type still supports partial `{name}` → `lookup_incomplete`, full MVR 0-hit → `create_pending`.
- **Do not edit `TODO.md`.**

---

## Locked design (do not reinterpret)

### Manifest vocabulary

| Old | New |
|-----|-----|
| `mvr.grains` | `mvr.record_types` |
| `mvr.default_grain` | `mvr.default_record_type` |
| `bootstrap.seed_grain` | `bootstrap.seed_record_type` |
| `identity_mode: "open"` | `new_records: "query_allowed"` |
| `identity_mode: "closed"` | `new_records: "bootstrap_only"` |

Parse only the new keys. Missing `new_records` on any record type → `ValueError` at manifest load.

### Baseball `record_types`

```json
{
  "mvr": {
    "default_record_type": "player",
    "record_types": {
      "player": {
        "bind_fields": ["player", "debut_team", "debut_year"],
        "description": "MLB player identity (Lahman catalog; operator-extended via bootstrap).",
        "new_records": "bootstrap_only"
      },
      "team": {
        "bind_fields": ["team"],
        "description": "Fan-facing team identity (Lahman catalog; operator-extended via bootstrap).",
        "new_records": "bootstrap_only"
      }
    }
  }
}
```

### CRM / empty-crm / crm-metering

```json
{
  "mvr": {
    "default_record_type": "person",
    "record_types": {
      "person": {
        "bind_fields": ["name", "employer"],
        "description": "CRM people: display name plus employer before bind and research.",
        "new_records": "query_allowed"
      }
    }
  }
}
```

Add `"seed_record_type": "person"` to CRM bootstrap block (optional but preferred for documentation).

### Player bind semantics (bootstrap only — pack handler)

| Field | Rule |
|-------|------|
| `player` | `TRIM(nameFirst) || ' ' || TRIM(nameLast)` from `People` |
| `debut_year` | First 4 chars of `People.debut` when present; else `MIN(Appearances.yearID)` as string |
| `debut_team` | Fan label `Teams.name` for **debut year** (first appearance year). Multiple teams that year → `MIN(TRIM(Teams.name))` for stability |

- **One registry row per `lahman.playerID`** — single primary `bind_values` tuple; **no** appearance-driven `add_bind_alias` loop for players.
- Keep `source_keys["lahman.playerID"]` on each player row.
- Team bootstrap unchanged (distinct `Teams.name` labels).

### Lookup routing (by key shape — unchanged mechanism, new field names)

| Lookup keys | Record type | Notes |
|-------------|-------------|-------|
| `{player}` | `player` | Partial; field index; homonym multi-match OK |
| `{player, debut_team}` | `player` | Partial |
| `{player, debut_team, debut_year}` | `player` | Full MVR |
| `{team}` | `team` | Exact |
| `{player, team}` (legacy) | — | `not_found` (team is not a player bind field) |
| Unknown keys | — | `not_found` |

- No `EntityQuery.record_type` on step 1 (same as removed `grain` override).
- `id`-only step 1 still searches all record-type stores.

### `new_records: bootstrap_only` — partial 0-hit (generic fix)

When record type has `new_records: bootstrap_only` and step-1 lookup is **partial** with **0 exact hits** and **no fuzzy suggestions**:

- Return **`not_found`** (after alias expansion path), **not** `lookup_incomplete` nagging for `debut_team` / `debut_year`.

`query_allowed` record types keep today’s `lookup_incomplete` + `required_fields` on partial 0-hit.

Implement in `_resolve_single_grain_step1` (and ensure multi-record-type partial delegate path hits it). Rename internal helper `_resolve_closed_grain_zero_hit` → `_resolve_bootstrap_only_zero_hit` (or equivalent); gate on `new_records == "bootstrap_only"` not the old `identity_mode` name.

### Traffic model (docs only)

- ~97% clients send `{player}` only; disambiguate from step-2 bind fields on multi-match.
- `debut_year` is for eyeball disambiguation (e.g. two Pete Rose / Reds rows: 1963 vs 1997), not expected in client lookup.
- Warehouse validation (Paul’s Lahman): `(player, debut_team, debut_year)` has **0** collision groups across ~23.6k players.

---

## Implement

### A. `src/network/mvr.py`

- Rename `GrainMvrPolicy` → `RecordTypePolicy` (or keep dataclass name if churn too high — **prefer rename** for clarity).
- `NetworkMvrConfig.grains` → `record_types`; `default_grain` → `default_record_type`.
- Parse `new_records`: required; values `bootstrap_only` | `query_allowed` only.
- `default_record_type()`, `list_record_types()`, `load_mvr(record_type=...)`.
- `infer_grain_from_lookup` → `infer_record_type_from_lookup`; `GrainInferenceResult` → `RecordTypeInferenceResult` (`grain` field → `record_type`).
- `is_closed_identity_grain` → `is_bootstrap_only_record_type(record_type)` (or `new_records_is_bootstrap_only`) — implement via `new_records == "bootstrap_only"`.
- Remove `_parse_identity_mode` / `identity_mode` field entirely.

### B. Registry / delivery / state

- `get_entity_registry(record_type=...)`, `entity_store_path(paths, record_type)`, `DeliveryScope.record_type`, `LookupSuggestion.record_type`, `TargetResolveResult.record_type`.
- Grep `grain` in `src/` and `tests/` — update parameters, env/docs strings, MCP/`introspection` policy text.
- `MYCELIUM_ENTITIES_PATH` override applies to **default record type** store (same rule as today).

### C. Bootstrap config

- `bootstrap.seed_grain` → `seed_record_type`; `resolve_bootstrap_grain` → `resolve_bootstrap_record_type`.
- `DefaultSeedHandler` uses resolved bootstrap record type.

### D. `src/agents/target_resolve.py` + `target_deliver.py` + `dispatch.py`

- All `grain=` kwargs → `record_type=` where they mean MVR store selection.
- Partial 0-hit → `bootstrap_only` behavior (above).
- `resolve_id_all_grains` → `resolve_id_all_record_types` (or keep function name with updated doc — **prefer rename**).

### E. `examples/networks/baseball/bootstrap_handlers/`

**`lahman_common.py`**

- Add `distinct_player_debut_rows(warehouse_path) -> list[tuple[playerID, display_name, debut_year, debut_team]]` with SQL per locked semantics.
- Remove or stop exporting `distinct_player_team_rows` if unused after seed rewrite.

**`lahman_seed.py`**

- Replace appearance loop with one `ensure_entity_bind_fields` per `playerID` from `distinct_player_debut_rows`.
- Drop player `add_bind_alias` / appearance-driven bind collisions for multi-team aliases.
- Keep team loop; keep `source_keys`; keep warehouse ingest.

### F. Example manifests + guides

| File | Update |
|------|--------|
| `examples/networks/baseball/network.json` | Locked player MVR + `record_types` + `new_records` |
| `examples/networks/crm/network.json` | `record_types.person` + `new_records: query_allowed` |
| `examples/networks/empty-crm/network.json` | Same |
| `examples/networks/crm-metering/network.json` | Same |
| `examples/networks/baseball/guide.md` | Query keys, debut bind, `bootstrap_only`, partial `{player}` |
| `examples/networks/baseball/README.md` | Re-bootstrap note |

### G. Docs

- Rename `docs/query-grain-router.md` → `docs/query-record-type-router.md`; update content for new bind fields and `bootstrap_only` partial 0-hit → `not_found`.
- Grep repo for `query-grain-router`, `grain`, `identity_mode`, `seed_grain` in **active docs** (`docs/`, `README.md`, `examples/`) — update links and vocabulary. Do **not** rewrite historical `prompts/cursor/done/` prompts.
- `docs/seed-bootstrap.md` — `record_type`, `new_records`, `seed_record_type`.
- `docs/onboarding.md`, `docs/architecture.md` — replace grain/identity_mode references where they describe current behavior.

### H. `src/network/create.py`

- Network skeleton manifest uses `record_types` + required `new_records` + `default_record_type`.

### I. Smoke / CLI

- `bin/smoke-baseball-e2e` — player lookups use `debut_team` / `debut_year` where needed; drop expectations on `{player, team}` as full MVR.
- `bin/baseball-query` / ship-gate helpers if they assert old bind keys — update.
- `docs/manual-checks/2026-06-18-baseball-query-hand-test-plan.md` — new keys and outcomes (`Nobody` → `not_found` not `lookup_incomplete`).

---

## Tests

### Rename / rewrite

| File | Action |
|------|--------|
| `tests/test_strict_grain_routing.py` | Rename → `tests/test_strict_record_type_routing.py`; update bind keys, outcomes, `record_type` assertions on `DeliveryScope` |
| `tests/test_multi_mvr_entity_stores.py` | Rename → `tests/test_multi_record_type_entity_stores.py`; manifest uses `record_types`; require `new_records` |
| `tests/test_mvr_generic_vocabulary.py` | Update for `debut_team` / `debut_year` on baseball player context |

### Locked scenarios (add or update)

| Scenario | Lookup | Expected step-1 |
|----------|--------|-----------------|
| Ty Cobb unique | `{player: "Ty Cobb"}` | `lookup_resolved`, 1 |
| Homonym | `{player: "Bob Smith"}` | `lookup_resolved`, N>1 |
| Unknown partial (baseball) | `{player: "Nobody Here"}` | **`not_found`** (not `lookup_incomplete`) |
| Hank Aaron identity | deliver after `{player: "Hank Aaron"}` | bind shows `debut_team: Milwaukee Braves`, `debut_year: 1954` (fixture/bootstrap dependent) |
| Pin with debut_team | `{player: "Pete Rose", debut_team: "Cincinnati Reds"}` | multi-match or 1 — document actual count |
| Full MVR | `{player, debut_team, debut_year}` for known player | `lookup_resolved`, 1 |
| Legacy career team | `{player: "Hank Aaron", team: "Atlanta Braves"}` | `not_found` |
| CRM partial unknown | `{name: "Nobody"}` | `lookup_incomplete`, `employer` in `required_fields` |
| CRM create | full MVR 0-hit | `create_pending` unchanged |
| Bootstrap only | baseball full MVR 0-hit | `not_found` / suggest — never `create_pending` |
| Lahman seed | one row per playerID | no player `bind_index` alias explosion; bind keys include `debut_team`, `debut_year` |

### Manifest fail-fast tests

- Reject `mvr.grains`, `identity_mode`, missing `new_records`, invalid `new_records` value.
- `default_record_type` must exist in `record_types`.

Grep after edits: no remaining `grain=` on `EntityQuery` / `resolve_target_step1` in tests; `grain=` OK only in transitional grep — target **zero** `grain` in `src/` public APIs.

---

## Paul post-slice

- **Re-bootstrap** baseball network root (bind shape changed; old `player`+`team` entities invalid).
- Full Lahman hand test plan after re-bootstrap.

---

## Verification

```bash
./bin/ci-local
```

---

## Deliverables

- `prompts/cursor/done/2026-06-18-1800-baseball-mvr-record-types-debut-bind/`
  - `prompt.md`, `output.md` with **For Grok + Paul** (TODO notes, re-bootstrap reminder, doc link updates)
- Do not commit.

**Suggested commit message:** `feat(mvr): record_type + new_records; baseball player debut bind`