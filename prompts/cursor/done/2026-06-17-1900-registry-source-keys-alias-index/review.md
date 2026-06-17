# Review — 2026-06-17-1900-registry-source-keys-alias-index

**Verdict: Approved + polish nits**

---

## CI

| Step | Result |
|------|--------|
| `./bin/ci-local` | Pass |
| smoke pytest | **480 passed**, 97 deselected |

```bash
./bin/ci-local
# CI local: all steps passed.
```

Prior baseline (slice 1 `output.md`): 480 passed. Re-verified on review run.

---

## Delivery

`output.md` matches slice 1 implementation. `prompt.md` present in `done/`. Framework APIs, Lahman pack handler, tests, and docs delivered per K1–K9.

**Working tree note:** Uncommitted tree also contains **`2026-06-17-1800-default-seed-handler-generic`** changes (CRM `rows[]`, `default_seed.py`, many test fixture updates). Stage **1900 files only** for this commit, or commit 1800 first — do not mix unrelated hunks in one commit message.

---

## Framework isolation (Paul gate)

| Check | Result |
|-------|--------|
| `lahman` / `baseball` imports in `src/` | **None** |
| `lahman.*` in `src/` logic | **None** |
| Docstring examples (`lahman.playerID`) | 2 lines in `entity_registry.py` — **OK** (illustrative only) |
| Lahman key strings | `examples/networks/baseball/bootstrap_handlers/lahman_seed.py` only |

**Pass.**

---

## Diff reviewed

| File | Notes |
|------|--------|
| `src/agents/entity_registry.py` | `source_keys`, `field_aliases`, `source_key_index`, `lookup_by_source_key`, `set_source_keys`, `add_field_alias`; rebuild on load/save/deferred commit |
| `src/agents/field_index.py` | `build_field_indexes` merges `field_aliases`; multi-entity per norm |
| `examples/.../lahman_common.py` | `distinct_team_label_rows()` — MIN teamID/franchID per label |
| `examples/.../lahman_seed.py` | No `player_ids`; source-key dedup + `set_source_keys` |
| `tests/test_entity_store_evolution.py` | Round-trip source key + Dodgers multi-match |
| `tests/test_lahman_seed_handler.py` | Asserts `lahman.playerID` on player rows |
| `docs/seed-bootstrap.md`, baseball README, `baseball-example-program.md` | Identity layers documented |

---

## Spec compliance

| # | Criterion | Result |
|---|-----------|--------|
| E1 | No `player_ids` in `lahman_seed.py` | Pass |
| E2 | `lookup_by_source_key("lahman.playerID", …)` after bootstrap | Pass |
| E3 | `add_field_alias` — two teams + `"Dodgers"` → 2 ids | Pass (`test_add_field_alias_allows_multi_entity_lookup`) |
| E4 | Multi-team same `playerID` | Pass |
| E5 | `./bin/ci-local` green | Pass |
| E6 | Disk shape in `output.md` | Pass |
| K4 | Bind alias vs field alias separation | Pass — `add_bind_alias` unchanged |
| K6/K7 | Team + player `source_keys` in pack | Pass |

Non-goals respected: no query graph, no lazy LLM aliases, no cross-refresh merge.

---

## Design critique

**Strong**

- Clean split: `bind_index` for full MVR binds; `field_aliases` for shared nicknames (slice 2 ready).
- `source_key_index` rebuilt from entity rows — single source of truth; persisted for inspection.
- Deferred bootstrap: `_save` during defer rebuilds indexes without disk flush — compatible with Lahman volume.
- `set_source_keys` on player create even when `duplicate` bind — idempotent re-bootstrap within pass.

**Sub-optimal (non-blocking)**

- Team `duplicate` bind skips `set_source_keys` — fine under bootstrap-once; re-refresh would leave team source keys unset on existing bind rows.
- `build_source_key_index` last-wins on collision — documented; acceptable for Lahman.
- `set_source_keys` / `add_field_alias` each call `_save()` — acceptable with deferred flush; optional batch API deferred.

---

## Nits

| ID | Item |
|----|------|
| N1 | Optional: assert `registry_entity_to_match` omits `source_keys` (guard public API) |
| N2 | Commit hygiene: stage 1900 paths only; 1800 default-seed is separate slice in same tree |
| N3 | `examples/networks/baseball/README.md` says field aliases “slice 2” — correct; ensure slice 2 updates wording when lazy path ships |

---

## For Paul

- **Verdict:** Approved — ready for local commit (1900 scope).
- **Suggested commit message** (from `output.md`):

```
feat(registry): source_keys and field alias index

Persist Lahman source IDs on RegistryEntity; field aliases for
multi-entity nickname lookup; Lahman handler drops in-memory playerID map.
```

- **Next:** Slice 2 (`2000-baseball-closed-identity-lazy-aliases`) can proceed on `add_field_alias`.
- **No push** unless you ask.