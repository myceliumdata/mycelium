# Rename suggestions[].entity_key → suggested_lookup (target protocol vocabulary)

> **READY** — Move to `in-progress/` before starting (see `prompts/cursor/WORKFLOW.md`).

**Context:** Public query input **`entity_key` was removed** in MVR redesign M9 (`lookup` / `id` / `delivery_id` only). **`suggestions[].entity_key` still appears** in `lookup_suggested` responses — a pre-MVR leftover from slice 1 (`EntityKeySuggestion`). That confuses human and agent readers (e.g. employer typo suggests `entity_key: "645 Ventures"` which looks like the retired query field).

**Paul:** This is **not polish** — names matter. Align suggestion JSON with the target protocol retry contract.

**Prerequisite:** Slice `1440` approved (employer fuzzy uses `employer_sequence_ratio` and canonical employer string).

**Breaking change:** Intentional. **No** `entity_key` alias on suggestions. Public JSON must not expose `suggestions[].entity_key`.

---

## Read first

- [`docs/architecture.md`](../../docs/architecture.md) — M9 target protocol; public surfaces
- [`src/models/state.py`](../../src/models/state.py) — `EntityKeySuggestion`, `QueryResponse`
- [`src/agents/entity_resolution.py`](../../src/agents/entity_resolution.py) — `_rank_suggestions`, `_rank_employer_suggestions`
- [`src/agents/target_resolve.py`](../../src/agents/target_resolve.py) — `_same_name_different_employer_suggestions`
- [`src/agents/responses.py`](../../src/agents/responses.py) — `response_lookup_suggested`, `response_entity_unresolved`
- [`src/network/introspection.py`](../../src/network/introspection.py) — `_POLICY_MVR_REDESIGN_TARGET`, `_POLICY_ENTITY_KEY_UNRESOLVED`
- [`admin-ui/src/mvr.ts`](../../admin-ui/src/mvr.ts) — `lookupFromSuggestion` (1440 `output.md` flagged employer mapping bug)
- [`tests/test_target_step1_lookup_clarity.py`](../../tests/test_target_step1_lookup_clarity.py)
- [`tests/test_entity_key_suggestions.py`](../../tests/test_entity_key_suggestions.py) — legacy internal path
- [`tests/test_mvr_target_public.py`](../../tests/test_mvr_target_public.py) — public JSON shape

---

## Locked design

### 1. Rename model

`EntityKeySuggestion` → **`LookupSuggestion`**

Update imports/types across `src/`, `admin-ui/`, tests. Old name must not remain on public models.

### 2. Replace field

**Remove:** `entity_key: str`

**Add:** `suggested_lookup: dict[str, str]` — partial or full MVR bind map the caller should send on step-1 retry.

| `reason` | `suggested_lookup` example |
|----------|---------------------------|
| `sequence_ratio` (name typo) | `{"name": "Andrea Kalmans"}` |
| `employer_sequence_ratio` | `{"employer": "645 Ventures"}` |
| `same_name_different_employer` | `{"name": "Andrea Kalmans", "employer": "Lontra Ventures"}` |

**Keep** (display / id-retry): `id`, `name`, `employer`, `score`, `reason` — same semantics as today. Employer-only fuzzy may omit `id`/`name` (1440).

### 3. Central builder (required)

Add a small helper (e.g. `lookup_suggestion(...)` in `entity_resolution.py` or `models/state.py`) so every suggestion path sets `suggested_lookup` consistently. **Do not** hand-build dicts in three places.

### 4. Retry contract (public)

Document in introspection + `QueryResponse.suggestions` field description:

> On `lookup_suggested`, retry step 1 with `lookup` merged from `suggestions[].suggested_lookup` (or `suggestions[].id` when the suggestion targets one known row). **Do not** send `entity_key`.

Update `_lookup_suggested_message` and legacy `response_entity_unresolved` copy to reference **`suggested_lookup`**, not `entity_key`.

### 5. Legacy internal path (`MYCELIUM_ALLOW_LEGACY_ENTITY_KEY=1`)

Keep `EntityQuery.entity_key` for internal smokes only. Suggestions on `entity_key_unresolved` use **`suggested_lookup`** too (typically `{"name": "…"}`). Legacy retry: use `suggested_lookup["name"]` as the next `entity_key` **in tests/docs only** — not exposed in public MCP/CLI JSON.

### 6. Admin UI

- `admin-ui/src/types.ts`: `LookupSuggestion` with `suggested_lookup`
- `lookupFromSuggestion`: merge `item.suggested_lookup` into form bind fields (fixes employer-only suggestions — set `employer` from map, not `entity_key` → `name`)
- Display: show `suggested_lookup` (or formatted bind fields), not `entity_key`

### 7. Network status

`entity_suggestions` in status payloads uses the new shape (via `model_dump()`).

---

## Tests (smoke — mandatory)

| Test | Assert |
|------|--------|
| **Update** all suggestion assertions | Use `suggested_lookup`, not `entity_key` |
| **New:** `test_public_json_suggestions_exclude_entity_key` | `public_dict()` / MCP JSON: no `entity_key` key inside `suggestions[]`; each item has `suggested_lookup` |
| **New:** `test_employer_fuzzy_public_json_omits_person_fields` | **1440 review carry-forward.** `lookup={"employer":"645 Venture"}` → `public_dict()` suggestion item has `suggested_lookup == {"employer": "645 Ventures"}` and **must not** include `id` or `name` keys (absent keys, not `null`). Also assert `reason == "employer_sequence_ratio"`. Prefer `test_mvr_target_public.py` or `test_target_step1_lookup_clarity.py` with `public_dict()` / `public_json()` — not model internals only. |
| **New:** `test_name_fuzzy_suggested_lookup_shape` | `Andrea Kalman` → `suggested_lookup == {"name": "Andrea Kalmans"}`; name fuzzy public JSON **may** include `id` and `name` when row-specific |
| **New:** `test_employer_fuzzy_suggested_lookup_shape` | `645 Venture` → `suggested_lookup == {"employer": "645 Ventures"}` |
| **New:** `test_same_name_different_employer_suggested_lookup` | wrong employer → `suggested_lookup` has both `name` and `employer` |
| **Keep:** legacy `test_entity_key_suggestions.py` green with `suggested_lookup` |
| **Keep:** `./bin/ci-local` admin-ui build |

---

## Docs

- [`docs/plans/fuzzy-lookup-policy.md`](../../docs/plans/fuzzy-lookup-policy.md) — replace `entity_key` retry references with `suggested_lookup`
- [`docs/architecture.md`](../../docs/architecture.md) — one line under target protocol: suggestions use `suggested_lookup`
- [`examples/networks/crm/README.md`](../../examples/networks/crm/README.md) — example `lookup_suggested` JSON snippet if step-1 table exists
- [`docs/plans/entity-key-suggestions-phase1.md`](../../docs/plans/entity-key-suggestions-phase1.md) — add **Superseded field** note at top (historical doc; do not rewrite whole file)

---

## Out of scope

- Removing `EntityQuery.entity_key` from internal models (already gated)
- Renaming `NetworkStatusSummary.entity_key` (status display key — separate concern)
- Alias / backward-compat `entity_key` on suggestions

---

## Verification

```bash
./bin/ci-local
```

**Manual:**

```bash
MYCELIUM_NETWORK=crm uv run mycelium query --network crm \
  --lookup-json '{"employer":"645 Venture"}' --json
# suggestions[0].suggested_lookup.employer == "645 Ventures"
# suggestions[0].entity_key must be absent

MYCELIUM_NETWORK=crm uv run mycelium query --network crm \
  --lookup-json '{"name":"Andrea Kalman"}' --json
# suggestions[0].suggested_lookup.name == "Andrea Kalmans"
```

Admin: click employer suggestion → lookup form `employer` field updates (not `name`).

---

## Governance

- Do not edit `TODO.md`.
- In `output.md` → **For Grok + Paul**: suggestion vocabulary aligned with target protocol; MCP restart for agents.
- Do not commit or push.

## When finished

1. `./bin/ci-local` green
2. `prompts/cursor/done/2026-06-14-1450-suggestion-suggested-lookup-rename/`
3. Remove from `in-progress/` and `next/`
4. Tell Paul **slice ready for review**

---

## Exit criteria

- No `entity_key` on `LookupSuggestion` / public `suggestions[]`
- Every suggestion path populates `suggested_lookup`
- Employer fuzzy `public_dict()` smoke: `id`/`name` absent on employer-only suggestions (1440 nit closed)
- Introspection policy + messages reference `suggested_lookup`
- Admin suggestion click uses `suggested_lookup`
- `./bin/ci-local` green

Suggested commit message:

```
refactor(query): replace suggestions[].entity_key with suggested_lookup

Rename EntityKeySuggestion to LookupSuggestion; suggestion retry hints
use target-protocol lookup maps instead of retired entity_key vocabulary.
```