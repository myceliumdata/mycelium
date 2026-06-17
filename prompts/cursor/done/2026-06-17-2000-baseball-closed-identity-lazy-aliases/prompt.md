# Closed-world identity + lazy field aliases (baseball)

> **READY** — Claim per `prompts/cursor/WORKFLOW.md` (move to `in-progress/` before starting). **Run after** `2026-06-17-1900-registry-source-keys-alias-index` (needs `add_field_alias`).

**Priority:** Second baseball identity slice. **Slice 3** (query grain selection) is a separate design thread with Paul + Grok.

**Parent:** Paul + Grok June 2026 — Lahman team/player catalog is **closed** at query time; `create_pending` is wrong for unknown nicknames (`Bronx Bombers`, `Dodgers`). Aliases are **lazy** on 0-hit (LLM); first-query latency OK; **wrong outcome is not OK**.

**Principles:**

- **Closed grains** — baseball `team` and `player` never `create_pending`; only derivative/materialization work may create later (out of scope).
- **Lazy aliases** — on 0-hit, expand nickname → attach `field_aliases` → retry lookup before suggest/not_found.
- **Shared ambiguous aliases OK** — `"Dodgers"` may alias multiple teams; retry returns multi-match (`lookup_resolved`, `total_matches>1`).
- **Framework generic** — closed-grain policy driven by manifest; LLM prompt uses `guide.md` + canonical registry list, not hardcoded Lahman in `src/`.
- **Grain routing deferred** — slice 3 will pick active grain on query; this slice ships policy + alias expansion **functions** and wires them where `target_resolve` already runs (default grain). Team-grain query tests may use direct registry/policy helpers until slice 3.

---

## Problem (posterity)

Generic step-1 path: full MVR lookup, no hit, no fuzzy suggestions → **`create_pending`**. Correct for `empty-crm`; **nonsense** for baseball — there is no "create a new MLB team/player" story.

Without lazy alias expansion, `"Bronx Bombers"` or `"Dodgers"` hits `create_pending` or unhelpful fuzzy (first-token mismatch). Paul locked: **0-hit → LLM alias expansion → retry → resolve / multi-match / suggest / not_found**, never create.

---

## Locked scope

| # | Decision |
|---|----------|
| C1 | **Manifest policy** — per-grain `identity_mode` (or equivalent) in `network.json` → `mvr.grains.<grain>.identity_mode`: `"open"` (default, CRM) vs `"closed"` (baseball team + player). Load via `network/mvr.py` or small helper. |
| C2 | **Baseball manifest** — set `"identity_mode": "closed"` on `team` and `player` grains in `examples/networks/baseball/network.json`. |
| C3 | **`create_pending` gate** — in `target_resolve` (or shared helper called from there): when active grain is **closed** and lookup is a **0-hit** on identity bind fields, **do not** return `create_pending`. Fall through to alias expansion (C4) then suggest/not_found. |
| C4 | **Lazy alias expansion** — new module e.g. `src/agents/bind_alias_expansion.py` (name flexible): `expand_field_aliases(grain, field, query_value, *, registry, guide_text) -> AliasExpansionResult` with `entity_ids: list[str]` (targets), `aliases_written: int`. Uses **LLM structured output** (OpenAI when `OPENAI_API_KEY` set) with: network `guide.md` excerpt, grain description, list of canonical bind values from registry (cap list size for prompt — e.g. 500 team names). Returns which existing entity ids should receive `add_field_alias(field, query_value)`. |
| C5 | **Retry contract** — after writing aliases, call `lookup_by_target_lookup` again. Outcomes: 1 id → `resolved`; 2+ → `resolved` multi-match; 0 → `lookup_suggested` with full canonical `suggested_lookup` rows and/or `not_found` with clear message — **never** `create_pending` on closed grains. |
| C6 | **LLM off / tests** — when no API key, use injectable/mock expander returning deterministic mappings in tests. Production path uses real LLM when configured. |
| C7 | **`guide.md`** — update `examples/networks/baseball/guide.md`: closed identity; lazy aliases; nickname may multi-match; no query-time entity creation for team/player. |
| C8 | **Tests** — (1) closed `team` grain: unknown `"Bronx Bombers"` with mock expander → alias written → resolves to Yankees entity; (2) `"Dodgers"` mock returns two team ids → multi-match; (3) CRM `person` grain still allows `create_pending` on 0-hit; (4) nonsense `"XYZZY"` on closed team → not `create_pending`. |
| C9 | **Docs** — short section in `docs/plans/baseball-example-program.md` or `docs/seed-bootstrap.md` pointer: closed vs open identity, lazy aliases. |

---

## Read first

- `prompts/cursor/WORKFLOW.md`
- `src/agents/target_resolve.py` — `create_pending` branch
- `src/agents/entity_resolution.py` — fuzzy suggestions
- `src/agents/entity_registry.py` — `add_field_alias` (slice 1)
- `src/network/mvr.py` — grain config loading
- `examples/networks/baseball/network.json`, `guide.md`
- `docs/plans/conversations/2026-06-16-llm-alias-resolution.md`
- `prompts/cursor/done/2026-06-17-1900-registry-source-keys-alias-index/` — slice 1 output (after it lands)

---

## Implement

### Policy loading

- Parse `identity_mode` per grain; default `open`.
- `is_closed_identity_grain(grain: str) -> bool` (or `IdentityMode` enum).

### Alias expansion

- Implement C4 with structured LLM call (json schema / tool response). **No Tavily** — closed-world alias from canonical list + guide context.
- Persist aliases via `add_field_alias` from slice 1.
- Record provenance in `output.md` (e.g. `source=alias_expansion`, actor kind).

### Wire into step 1

- In `resolve_target_step1`, after 0-hit on closed grain (before `create_pending`): invoke expansion + retry per C5.
- Preserve existing CRM paths unchanged.

### Baseball example

- Manifest + `guide.md` updates per C2/C7.

### Tests

- Mocked LLM tests per C8; `./bin/ci-local` green.

---

## Scope boundaries (strict)

**May modify:**

- `src/agents/target_resolve.py`, new alias expansion module, `src/network/mvr.py` (grain config types)
- `examples/networks/baseball/network.json`, `guide.md`
- `tests/`
- Short doc note in `docs/plans/baseball-example-program.md`

**Do not modify:**

- Query grain selection / supervisor routing (slice 3)
- `LahmanSeedHandler` bootstrap logic (slice 1)
- Derivative `create_pending` / materialization
- Bootstrap batch LLM alias generation
- Admin UI (unless test-only)
- `TODO.md`

---

## Explicit non-goals

- Wiring full `mycelium query` against live baseball root end-to-end (grain selection slice)
- Player-grain lazy aliases beyond framework hook (implement same path for any closed grain — tests must include at least team; player test optional if default-grain wiring is player-only stub)
- Tavily / web research for aliases
- Franchise specialist

---

## Exit criteria

| # | Criterion |
|---|-----------|
| E1 | Baseball `team` + `player` grains declare `identity_mode: closed` |
| E2 | Closed grain 0-hit never returns `create_pending` |
| E3 | Mocked lazy alias: `Bronx Bombers` → resolves; `Dodgers` → multi-match when expander returns 2 ids |
| E4 | CRM open grain behavior unchanged (`create_pending` still possible) |
| E5 | `./bin/ci-local` green |
| E6 | `output.md` documents LLM prompt shape, mock injection, and slice-3 follow-ups |

---

## Governance (mandatory)

- **Do not edit `TODO.md`.**
- **For Grok + Paul** in `output.md`: slice-3 needs (explicit grain in `EntityQuery` vs router); env vars for alias LLM.

## When finished

Per `prompts/cursor/WORKFLOW.md` — no commit/push.

**Suggested commit message:**

```
feat(resolve): closed identity grains and lazy field aliases

Baseball team/player never create_pending on miss; LLM alias expansion
writes field_aliases and retries lookup for multi-match or resolve.
```