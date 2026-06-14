# Target step-1 lookup clarity — outcomes, suggestions, confirm_new_entity

> **READY** — Move to `in-progress/` before starting (see `prompts/cursor/WORKFLOW.md`).

**Context (Paul + Grok, June 2026):** Target-protocol step 1 overloads `not_found` and silently offers `create_on_deliver` when full MVR matches zero rows — even when the **same name** already exists under a different employer (Andrea @ Wrong Corp vs Andrea @ Lontra Ventures). Agents discover MVR only via `describe_network`, not query responses. `required_fields` / `suggestions` on `QueryResponse` are always empty on public surfaces.

**Paul’s direction:** Early build — no backward-compat burden. Reduce JSON noise; never omit fields that help agents understand state. **Same-name / different-employer** is **suggestions territory** (like typos). Creating a genuinely new bind (Andrea @ Another Co) stays allowed but requires **`confirm_new_entity: true`** after seeing suggestions — removes ambiguity.

**Supersedes:** `2026-06-14-1000-query-response-omit-empty-lists.md` (merged into this slice).

**Prerequisites:** `74a7f94` (outcome-aware `public_dict` omission) on `main`.

---

## Read first

- `docs/plans/mvr-redesign-program.md` — R4 partial lookup, R10 full MVR create
- `src/agents/target_resolve.py`, `src/agents/dispatch.py` (`target_resolve_node`)
- `src/network/mvr.py` — `is_full_mvr_lookup`, `normalized_lookup_values`, `load_mvr`
- `src/agents/entity_registry.py` — `lookup_by_target_lookup`, `lookup_by_name`
- `src/agents/entity_resolution.py` — `_rank_suggestions`, `EntityKeySuggestion`
- `src/agents/responses.py` — add response builders
- `src/models/state.py` — `EntityQuery`, `QueryResponse`, `public_dict`
- `src/network/introspection.py` — `build_network_capabilities`, policy strings
- `admin-ui/src/App.tsx`, `admin-ui/src/types.ts` — query panel
- `src/main.py`, `src/mycelium_mcp/server.py`, `src/mycelium_admin/server.py`
- `tests/test_mvr_create_on_deliver.py`, `tests/test_mvr_target_resolve.py`, `tests/test_entity_key_suggestions.py`

---

## Summary — what this slice delivers

### A. Four clear step-1 stories (no overloaded `not_found`)

| Case | Example | New step-1 outcome | `delivery` | Key fields |
|------|---------|----------------------|------------|------------|
| **Partial lookup, 0 hits, missing MVR** | `{"name":"Paul Murphy"}` only, not in registry | `lookup_incomplete` | none | `required_fields: ["employer"]` |
| **Partial lookup, ≥1 hit** | `{"name":"Andrea Kalmans"}` | `lookup_resolved` | yes | `total_matches: N` (unchanged — R4 search) |
| **Full MVR, 0 hits, same name exists elsewhere** | Andrea @ Wrong Corp; Andrea @ Lontra in registry | `lookup_suggested` | none | `suggestions[]` (existing rows) |
| **Full MVR, 0 hits, name typo near-miss** | Kalman @ Acme; Kalmans exists | `lookup_suggested` | none | `suggestions[]` (`reason: sequence_ratio`) |
| **Full MVR, 0 hits, safe create** | Paul @ Acme on empty-crm; no name collision | `lookup_resolved` | yes | `create_on_deliver: true` |
| **Full MVR, 0 hits, intentional new bind after warning** | Andrea @ Another Co after `lookup_suggested` | `lookup_resolved` | yes | `confirm_new_entity: true` → `create_on_deliver` |
| **True dead end** | unknown `id`, expired `delivery_id` | `not_found` | none | (unchanged) |

### B. New request field — `confirm_new_entity` (step 1 only)

- **Type:** optional boolean, default false/omitted.
- **Meaning:** “I have seen same-name suggestions and intentionally want a **new** registry row for this full MVR lookup.”
- **Validation:** step 1 only; illegal on step 2; only meaningful with `lookup` (not `id`).
- **Wire:** CLI `--confirm-new-entity`; MCP/admin JSON field; admin UI checkbox (visible when last outcome was `lookup_suggested`).

### C. Suggestions on target protocol

Reuse `EntityKeySuggestion`; extend `reason` values:

| `reason` | When |
|----------|------|
| `same_name_different_employer` | Exact normalized name match; employer ≠ lookup employer |
| `sequence_ratio` | Fuzzy name near-miss (reuse `_rank_suggestions` on lookup `name` value) |

**Re-query guidance in `message`:** use `suggestions[].id` or full MVR `lookup` copied from suggestion — not legacy `entity_key`.

### D. Public JSON noise reduction (merged from 1000 slice)

In `QueryResponse.public_dict()`:

- Omit `required_fields` / `suggestions` when empty.
- Include when non-empty (`lookup_incomplete`, `lookup_suggested`).
- Omit `trace_id` when null.
- Add `lookup_incomplete` and `lookup_suggested` to step-1 public outcome set (may include `total_matches: 0`; never `delivery`).

### E. Onboarding / docs

- `build_network_capabilities()` — replace stale `entity_unknown` / `binding` policy with target rules:
  - partial lookup = search;
  - full MVR + 0 hits + same name = suggestions first;
  - `confirm_new_entity` for deliberate new bind;
  - `policy.mvr` unchanged source of bind field names.
- `docs/architecture.md` M9 paragraph — document new outcomes + confirm flag.
- Optional: `examples/networks/crm/README.md` one-line note.

### F. Admin UI (minimal)

- Outcome badge for `lookup_incomplete`, `lookup_suggested`.
- Show `required_fields` / `suggestions` when present (already gated on length).
- **Confirm new entity** checkbox on step-1 form; sets `confirm_new_entity` on next Run.

---

## Locked step-1 decision tree (implement in `resolve_target_step1` or helper)

After `entity_ids = registry.lookup_by_target_lookup(query.lookup)`:

**1. `entity_ids` non-empty** → existing `lookup_resolved` path (issue delivery; no `create_on_deliver` unless 0 — wait, non-empty means matches, no create). Unchanged.

**2. `entity_ids` empty, not `is_full_mvr_lookup(lookup)`** → `lookup_incomplete`

- `required_fields` = MVR bind fields absent from normalized lookup (non-empty values).
- No delivery issued.
- Message: which fields missing for **create**; partial search may still be intentional — if only missing fields, say “include … to create a new entity.”

**3. `entity_ids` empty, full MVR, `confirm_new_entity` is true** → existing create path (`lookup_resolved`, `total_matches: 0`, `create_on_deliver: true`, issue delivery).

**4. `entity_ids` empty, full MVR, not confirmed** → check collisions:

- If `name` in lookup: `same_name = registry.lookup_by_name(lookup name)` filtered to rows whose employer ≠ lookup employer (normalize consistently).
- If `same_name` non-empty → `lookup_suggested` with suggestions (`same_name_different_employer`); **no delivery**.
- Else if `name` in lookup: run `_rank_suggestions(name value)`; if any → `lookup_suggested` (fuzzy); **no delivery**.
- Else → safe create path (step 3 without confirm — no collision).

**5. `lookup_suggested` / `lookup_incomplete` never issue `delivery_id`.**

---

## Response builders

Add to `src/agents/responses.py`:

- `response_lookup_incomplete(query, required_fields, message, …)`
- `response_lookup_suggested(query, suggestions, message, …)`

Locked messages (tune for clarity, keep intent):

| Outcome | Message intent |
|---------|----------------|
| `lookup_incomplete` | No match; list missing MVR fields to create; partial lookup is search-only |
| `lookup_suggested` (employer) | Name matches existing row(s) with different employer; retry with `id` or corrected lookup, or set `confirm_new_entity` |
| `lookup_suggested` (fuzzy) | Near-miss names; retry with suggestion `id` or corrected lookup |
| `lookup_resolved` create | Keep existing create message |

---

## `EntityQuery` changes

```python
confirm_new_entity: bool = Field(
    default=False,
    description=(
        "Step 1 only. When true with full MVR lookup, issue create_on_deliver "
        "even if same-name registry rows exist under different employers. "
        "Use only after reviewing lookup_suggested."
    ),
)
```

Validator: reject on step 2; reject with step-1 `id`-only resolve (confirm only applies to lookup create path).

---

## `public_dict` / outcomes

- Extend `_STEP1_PUBLIC_OUTCOMES` with `lookup_incomplete`, `lookup_suggested`.
- `lookup_suggested` / `lookup_incomplete`: no `delivery`; `total_matches` = 0 when included.
- Omit empty `required_fields`, `suggestions`; omit null `trace_id`.

Update `QueryResponse.outcome` field description with new outcomes.

---

## Tests (smoke unless noted)

| Test | Assert |
|------|--------|
| `test_partial_lookup_missing_employer_lookup_incomplete` | `{"name":"Paul Murphy"}` 0 hits → `lookup_incomplete`, `required_fields` has `employer`, no `delivery` |
| `test_partial_lookup_name_hit_lookup_resolved` | `{"name":"Andrea Kalmans"}` → `lookup_resolved`, ≥1 match |
| `test_full_mvr_wrong_employer_lookup_suggested` | Andrea @ Wrong Corp → `lookup_suggested`, suggestions include Lontra row, no `delivery` |
| `test_full_mvr_wrong_employer_confirm_creates` | Same + `confirm_new_entity: true` → `lookup_resolved`, `create_on_deliver` |
| `test_full_mvr_no_collision_create` | Road Runner @ Acme → direct `create_on_deliver` (no confirm) |
| `test_fuzzy_name_lookup_suggested` | Kalman @ Acme → `lookup_suggested`, `sequence_ratio` (if seed has Kalmans) |
| `test_public_dict_omits_empty_negotiation_fields` | `found` → no `required_fields`/`suggestions` keys |
| `test_public_dict_includes_required_fields_when_incomplete` | wire JSON |
| Update `test_partial_lookup_zero_matches_not_found` | Now expects `lookup_incomplete` or renamed — **not** `not_found` for missing MVR |
| Admin wire test | `lookup_suggested` shape via POST `/query` |

Use `public_dict()` for wire assertions where applicable.

---

## Scope boundaries (strict)

**May modify:**

- `src/agents/target_resolve.py` (+ small helper module if needed)
- `src/agents/dispatch.py` (target_resolve_node wiring only)
- `src/agents/responses.py`
- `src/models/state.py`
- `src/network/introspection.py` (policy strings)
- `src/main.py` (CLI flag)
- `src/mycelium_mcp/server.py` (schema description; EntityQuery validation path)
- `admin-ui/src/App.tsx`, `admin-ui/src/types.ts`
- `docs/architecture.md` (M9 paragraph)
- `examples/networks/crm/README.md` (optional one paragraph)
- Tests under `tests/test_mvr_*`, `tests/test_mvr_entity_query_models.py`, `tests/test_admin_daemon.py`, new `tests/test_target_step1_lookup_clarity.py` if cleaner

**Out of scope:**

- `TODO.md`
- Deleting legacy `entity_key` graph / supervisor path
- Employer **update** / merge UX (Andrea moved companies — separate product)
- Program 3 full legacy cleanup
- Changing R4 partial search semantics for ≥1 hit

---

## Verification

```bash
./bin/ci-local
```

Manual (document in `output.md`):

```bash
# Incomplete
uv run mycelium query --network crm --lookup-json '{"name":"Paul Murphy"}'

# Suggested (seed Andrea)
uv run mycelium query --network crm \
  --lookup-json '{"name":"Andrea Kalmans","employer":"Wrong Corp"}'

# Confirm create
uv run mycelium query --network crm \
  --lookup-json '{"name":"Andrea Kalmans","employer":"Wrong Corp"}' \
  --confirm-new-entity

# Safe create (empty-crm)
./bin/refresh-example-network empty-crm --yes
uv run mycelium query --network empty-crm \
  --lookup-json '{"name":"Paul Murphy","employer":"Acme Corp"}'
```

---

## Governance (mandatory)

- **Do not edit `TODO.md`.**
- In `output.md`, **For Grok + Paul**: outcome table, example JSON snippets, admin UI notes, gate-doc updates if needed.
- Do not commit or push.

## When finished (mandatory — see WORKFLOW.md §3)

1. `./bin/ci-local` green
2. `prompts/cursor/done/2026-06-14-1100-target-step1-lookup-clarity/`
3. Remove claimed file from `in-progress/` and `next/`
4. Tell Paul **slice ready for review**

---

## Exit criteria

- Step-1 outcomes disambiguate partial / suggested / create / match
- `confirm_new_entity` wired CLI + MCP + admin
- Same-name different-employer blocks silent create
- Fuzzy name suggestions on target path when applicable
- Empty `required_fields`/`suggestions`/`trace_id` omitted in public JSON
- `describe_network` policy updated
- `./bin/ci-local` green

Suggested commit message:

```
feat: clarify target step-1 lookup with suggestions and confirm_new_entity

Add lookup_incomplete and lookup_suggested outcomes; require confirm_new_entity
for create when same name exists under different employer; omit empty negotiation
fields in public JSON; update onboarding policy.
```