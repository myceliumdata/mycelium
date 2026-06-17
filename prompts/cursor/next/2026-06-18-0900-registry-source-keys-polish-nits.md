# Registry + resolve polish nits (post 1900 / 2000 / 2100)

> **LOW PRIORITY** — Run when Paul asks or no higher-priority slice is queued. Nits from Grok reviews of `done/2026-06-17-1900-registry-source-keys-alias-index/`, `done/2026-06-17-2000-baseball-closed-identity-lazy-aliases/`, `done/2026-06-17-2100-query-grain-router/`, and Grok `ci-local` timing review (June 2026).

## Nits — slice 1900 (registry)

| ID | Item |
|----|------|
| P1 | Test guard: `registry_entity_to_match` does **not** expose `source_keys` / `field_aliases` in public match dict |
| P2 | Team bootstrap `duplicate` bind path: optionally `set_source_keys` on existing team entity (harmless under bootstrap-once; helps re-refresh debugging) |
| P3 | Tighten `examples/networks/baseball/README.md` field-alias wording (lazy query-time vs bootstrap bind aliases) — **2000 shipped**; safe to do now |
| P4 | ~~Batch `set_source_keys`~~ — **obsolete**; superseded by `c96c5e2` + slice `2026-06-18-0800-bootstrap-save-entity-source-key-skip` (incremental index + bind-only `save_entity` skip). Drop this row when polishing. |

## Nits — slice 2000 (closed identity / lazy aliases)

| ID | Item |
|----|------|
| P5 | **Provenance:** query-time `add_field_alias` writes persist but have no actor/provenance kind (prompt C4 mentioned `source=alias_expansion`) — add minimal provenance hook or document intentional omission in `output.md` / architecture |
| P6 | **`docs/seed-bootstrap.md`:** ensure § Open vs closed identity (`identity_mode`) is committed — file may still be uncommitted with 1800 default-seed content; land with 1800 or cherry-pick identity section if 1800 is separate |

## Nits — slice 2100 (query grain router)

| ID | Item |
|----|------|
| P7 | **`_partial_lookup_result` grain-aware fuzzy:** `query_grain_router._partial_lookup_result` calls `_rank_bind_field_fuzzy_suggestions`, which uses `get_entity_registry()` (default grain only). Pass grain into entity-resolution helpers or fan-out partial lookup per participating grain so non-default-grain partial queries don't suggest from the wrong store. |
| P8 | **`cross_grain_ambiguous` message:** `responses._lookup_suggested_message` has no branch for `cross_grain_ambiguous` — 3c responses get generic "near-miss names" copy. Add agent-facing message ("pick candidate by grain + suggested_lookup or id"). |
| P9 | **`docs/query-grain-router.md` link:** links `seed-bootstrap.md` — broken on clean tree until slice 1800 lands. Fix link (conditional note) or land cross-ref when 1800 commits; coordinate with P6. |
| P10 | **Doc markdown:** fix `` `**name**` `` / `` `**team**` `` formatting in `docs/query-grain-router.md` (lines ~23, ~80) — renders awkwardly. |
| P11 | **Test gaps** in `tests/test_query_grain_router.py`: (a) Dodgers-style 2 hits one grain / no LLM via `resolve_target_step1`; (b) disambiguation `chosen` outcome (single `{grain, entity_id}`); (c) duplicate id across grains → `not_found`; (d) explicit E2 0-hit alias-retry smoke. |
| P12 | **Type `disambiguator`:** `resolve_target_step1(..., disambiguator: Any \| None)` → `GrainDisambiguator \| None` from `grain_disambiguation.py`. |
| P13 | **Test helper for paths:** `tests/test_query_grain_router.py` imports private `network.paths._RUNTIME_ENV_FIELDS` — add public test helper (e.g. `apply_network_paths_monkeypatch`) or document pattern in `network_helpers`. |
| P14 | **`bin/smoke-baseball-e2e`:** extend minimal fixture with team-grain resolve scenario now that router + `delivery.grain` ship (step-1 team lookup → step-2 deliver). |

**Priority within 2100 nits:** P7 + P8 + P11 first (behavior/UX/tests); P14 when baseball e2e gate is next; P9 waits on 1800 unless doc-only workaround.

## CI smoke (`./bin/ci-local` timing — June 2026)

| ID | Item |
|----|------|
| P15 | **`test_mcp_example_batch_fixture_roundtrip` (~30s / ~64% of smoke pytest):** step-2 MCP batch deliver runs full graph without mocked research; equivalent scenario in `test_mvr_batch_deliver.py` completes in ~0.1s with `_mock_email_research` + pre-registered contact specialist. **Fix:** add `_mock_email_research(monkeypatch)` and specialist setup to `crm_public_env` (or test-local fixture) — *or* keep smoke as step-1 MCP wire check only and demote step-2 roundtrip to `@pytest.mark.full`. Target: smoke pytest drops ~25–30s; no loss of batch-deliver coverage (already in `test_mvr_batch_deliver.py`). |

**Do first when touching this slice:** P15 — highest ROI; verify with `pytest -m smoke --durations=5` before/after.

## Scope

**May modify:**

- `src/agents/query_grain_router.py`, `entity_resolution.py`, `responses.py`, `target_resolve.py`, `target_deliver.py`
- `src/agents/entity_registry.py`, `bind_alias_expansion.py`
- `examples/networks/baseball/` (README, bootstrap handler tweaks for P2)
- `tests/test_query_grain_router.py`, `tests/test_mvr_target_public.py`, related smoke tests
- `docs/query-grain-router.md`, `docs/seed-bootstrap.md` (if 1800 content available)
- `bin/smoke-baseball-e2e`
- `tests/network_helpers.py` or `network/paths.py` (P13 only — small public helper)

**Do not modify:** `TODO.md`

- `./bin/ci-local` green
- Polish only — no required behavior change except P7/P8/P11/P14/P15 where listed; P4 only if Paul's Test 8 timing gate confirms regression

## When finished

Per `WORKFLOW.md` — no commit until Grok review unless Paul authorizes direct commit.