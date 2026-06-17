# Review — 2026-06-17-2000-baseball-closed-identity-lazy-aliases

**Verdict: Approved + polish nits**

---

## CI

| Step | Result |
|------|--------|
| `./bin/ci-local` (Grok re-run) | **Pass** |
| smoke pytest | **485 passed**, 98 deselected |
| ruff | clean |
| admin-ui build | ok |

```bash
./bin/ci-local
# CI local: all steps passed.
```

Cursor `output.md` claim: 485 passed — matches.

---

## Delivery

`prompt.md` + `output.md` in `done/`. Prompt removed from `next/` (only `2100` + polish remain). Implementation matches claims.

**Working tree note:** Uncommitted tree still contains **1800 default-seed** hunks (`default_seed.py`, CRM `rows[]`, `architecture.md`, `onboarding.md`, full `docs/seed-bootstrap.md`, many test fixture tweaks). Stage **2000 files only** for this commit.

---

## Framework isolation (Paul gate)

| Check | Result |
|-------|--------|
| `lahman` / `baseball` in `src/` logic | **None** |
| Docstring examples (`lahman.playerID`) | `entity_registry.py` only — OK |
| Baseball manifest / guide | `examples/networks/baseball/` only |

**Pass.**

---

## Diff reviewed

| File | Notes |
|------|--------|
| `src/network/mvr.py` | `GrainMvrPolicy.identity_mode`; `is_closed_identity_grain()` |
| `src/agents/bind_alias_expansion.py` | **New** — LLM structured output, canonical cap 500, injectable `AliasExpander` |
| `src/agents/target_resolve.py` | `grain` + `alias_expander` on `resolve_target_step1`; closed 0-hit → expansion → retry → suggest/not_found |
| `examples/networks/baseball/network.json` | `identity_mode: closed` on team + player |
| `examples/networks/baseball/guide.md` | Closed identity + lazy aliases documented |
| `docs/plans/baseball-example-program.md` | `identity_mode` + lazy expansion row |
| `tests/test_closed_identity_lazy_aliases.py` | **New** — Bronx Bombers, Dodgers multi-match, XYZZY, CRM `create_pending` |

---

## Spec compliance

| # | Criterion | Result |
|---|-----------|--------|
| C1 | Manifest `identity_mode` loaded | Pass |
| C2 | Baseball team + player `closed` | Pass |
| C3 | Closed 0-hit skips `create_pending` | Pass |
| C4 | Lazy alias expansion module + LLM shape | Pass |
| C5 | Retry after `add_field_alias` | Pass |
| C6 | Mock expander in tests; LLM when key set | Pass |
| C7 | `guide.md` updated | Pass |
| C8 | Tests per scenarios | Pass |
| C9 | Doc note in baseball program | Pass |
| E1–E6 | Exit criteria | Pass |

Non-goals respected: no grain router, no Lahman bootstrap changes, no Tavily.

---

## Design critique

**Strong**

- Clean manifest-driven policy (`open` default, `closed` opt-in) — CRM unchanged.
- Injectable expander keeps tests deterministic; production LLM path gated on `OPENAI_API_KEY`.
- Closed path ordering is right: alias expansion → fuzzy suggest → `not_found`; `confirm_new_entity` on closed grain also blocked.
- `resolve_target_step1(grain=…)` gives slice 3 a hook without premature `EntityQuery.grain`.

**Acceptable deferrals (slice 3)**

- `dispatch.py` still calls `resolve_target_step1(query)` without `grain` — baseball team queries need grain router before production use.
- `_lookup_suggestions_for_full_mvr` / `_rank_suggestions` use default-grain registry — documented in `output.md`.

**Minor gap**

- Prompt C4 asked provenance note (`source=alias_expansion`); `add_field_alias` persists aliases but no actor/provenance kind — logged as follow-up in `output.md`. Non-blocking.

---

## Polish nits (non-blocking)

| # | Nit |
|---|-----|
| P1 | `prompts/cursor/HOLD.md` still lists `2000` in `next/` as READY — update on commit |
| P2 | `docs/seed-bootstrap.md` has good `identity_mode` section but file is bundled with uncommitted 1800 content — either commit with 1800 or cherry-pick identity section into 2000 docs commit |
| P3 | Slice 3: pass `grain` from router into `resolve_target_step1`; grain-aware fuzzy suggestions on closed path |
| P4 | Optional: provenance actor for query-time `add_field_alias` writes |

---

## For Paul

**Commit (2000 scope only):**

```
feat(resolve): closed identity grains and lazy field aliases

Baseball team/player never create_pending on miss; LLM alias expansion
writes field_aliases and retries lookup for multi-match or resolve.
```

**Next:** `2026-06-17-2100-query-grain-router.md` — ready in `next/`.

**Timing:** Test 8 regression vs 555 s still open; slice 2 does not affect bootstrap — P4 batch `set_source_keys` remains optional if Test 8 confirms regression.

**Push:** local only until Paul asks.