# QueryResponse public JSON — omit N/A fields (outcome-aware)

> **READY** — Move to `in-progress/` before starting (see `prompts/cursor/WORKFLOW.md`).

**Context (Paul + Grok, June 2026):** Step-2 `found` responses currently emit `total_matches: null`, `delivery: null`, `quote: null`, `provenance: null`. That reads like a bug to humans and visiting agents. We already omit `delivery.create_on_deliver` unless true (`DeliveryPayload.public_dict`). Extend the same rule to top-level step-1-only fields: **omit keys that do not apply to the current `outcome`**, do not emit `null` placeholders.

**Prerequisite:** Program 2 local work on `main`; manual gate may still be in progress — this slice is independent polish.

---

## Read first

- `prompts/cursor/WORKFLOW.md` — governance, claiming, no commit
- `docs/architecture.md` — § Public surfaces (CLI, MCP, admin) — M9 (~line 289)
- `src/models/state.py` — `DeliveryPayload.public_dict`, `QueryResponse.public_dict`
- `src/agents/responses.py` — response builders (in-memory models unchanged)
- `tests/test_mvr_entity_query_models.py` — `test_public_dict_preserves_explicit_null_top_level_fields` (replace)
- `tests/test_mvr_target_deliver.py` — step-2 assertions
- `tests/test_mvr_target_resolve.py` — step-1 JSON shape tests
- `admin-ui/src/App.tsx` — already hides `total_matches` when null (verify no regression)
- `prompts/cursor/done/2026-06-13-2200-admin-query-step1-create-on-deliver/review.md` — prior `public_dict` design notes

---

## Objective

Make CLI, MCP, and admin `POST /query` JSON **phase-appropriate**: only include fields that mean something for the response `outcome`. Reduce agent/human confusion without changing query semantics or in-graph `QueryResponse` models.

**Non-goals:** Changing when `total_matches` is set internally; auto-deliver; legacy `entity_key` graph behavior.

---

## Locked semantics — public JSON omission rules

Implement in **`QueryResponse.public_dict()`** (single source — CLI/MCP/admin already call it). `public_json()` inherits automatically.

### Step-1 family (`outcome` in step-1 set)

**Outcomes:** `lookup_resolved`, `quote_required`, `payment_required`, `principal_required`

| Field | Rule |
|-------|------|
| `total_matches` | **Include** when not `None` |
| `delivery` | **Include** when not `None` (use nested `delivery.public_dict()`) |
| `quote` | **Include** when not `None`; **omit key** when `None` |
| `results` | Keep `[]` on step 1 (empty by design) |
| `provenance` | **Omit** when `None` |

### Deliver / terminal family (all other public outcomes)

**Outcomes:** `found`, `assembled`, `not_found`, `error`, plus legacy graph outcomes if they still surface on public paths (`entity_unknown`, etc.)

| Field | Rule |
|-------|------|
| `total_matches` | **Omit key** (even if model has `None`) — step-1-only metadata |
| `delivery` | **Omit key** |
| `quote` | **Omit key** when `None` |
| `provenance` | **Omit** when `None`; include when present |
| `results` | Always include (may be `[]`) |

### Always keep (unless already omitted by `exclude_none`)

- `outcome`, `message`, `debug`, `trace_id`, `thread_id`
- `required_fields` — keep `[]` when empty (clients depend on list presence; same as M10 slice)
- `suggestions` — keep `[]` when empty

### Do not emit

- `false` for booleans that mean “not applicable” (follow `create_on_deliver` precedent)
- `null` for omitted keys above — **absent key**, not `"field": null`

---

## Implement

### 1 — `QueryResponse.public_dict()` (`src/models/state.py`)

- Add a small helper or outcome sets (readable, tested).
- Start from `model_dump(exclude_none=True)` or selective pop — whichever stays clearest.
- Preserve existing `delivery.public_dict()` nesting for included deliveries.
- Update `QueryResponse` / `public_dict` docstrings to document omission rules.
- **In-memory** `QueryResponse` objects unchanged (`total_matches=None` on step 2 is fine internally).

### 2 — MCP / docs

- `src/mycelium_mcp/server.py` — update `QueryResponse` schema description if it claims explicit `null` on optional fields.
- `docs/architecture.md` — replace “preserves explicit `null` on other optional fields” with outcome-aware omission wording.

### 3 — Tests (smoke)

| Test | Assert |
|------|--------|
| **Replace** `test_public_dict_preserves_explicit_null_top_level_fields` | New tests below |
| `test_public_dict_step2_found_omits_step1_fields` | Road Runner or CRM deliver: step-2 `public_dict()` has **no** keys `total_matches`, `delivery`; has `results` |
| `test_public_dict_step1_lookup_resolved_includes_matches` | Step-1 `lookup_resolved`: has `total_matches`, `delivery`; **no** `quote` key when null |
| `test_public_dict_quote_required_includes_quote` | Existing metering test path or minimal builder — `quote_required` includes `quote`, `total_matches`, `delivery` when set |
| Update `test_lookup_resolved_serializes_to_json` if it asserts `"quote" in payload` with null | Expect quote **absent** when null |

Keep existing in-memory assertions (`step2.total_matches is None`) — only **public JSON** changes.

### 4 — Admin UI

- Verify `admin-ui/src/App.tsx` still works (optional fields in `types.ts`).
- No UI change required if omission-only; build must pass via `./bin/ci-local`.

---

## Scope boundaries (strict)

**May modify:**

- `src/models/state.py`
- `tests/test_mvr_entity_query_models.py`
- `tests/test_mvr_target_deliver.py` (public_dict assertions only, if needed)
- `tests/test_mvr_target_resolve.py` (quote null assertion, if needed)
- `tests/test_admin_daemon.py` (only if response key assertions break)
- `src/mycelium_mcp/server.py` (docstring/schema description only)
- `docs/architecture.md` (Public surfaces paragraph only)

**Out of scope:**

- `TODO.md`
- Production graph logic in `dispatch.py` / `responses.py` (unless a test forces a one-line comment)
- Changing `required_fields: []` omission policy
- Program 3 / operator write UI

---

## Verification

```bash
./bin/ci-local
```

Manual sanity (document in `output.md`):

```bash
# Step 1 — expect total_matches + delivery; no quote key
uv run mycelium query --network crm \
  --lookup-json '{"name": "Road Runner", "employer": "Acme Corp"}'

# Step 2 — expect results; no total_matches or delivery keys in JSON
uv run mycelium query --network crm --delivery-id <delivery_id>
```

---

## Governance (mandatory)

- **Do not edit `TODO.md`.**
- In `output.md`, **For Grok + Paul**: note any client that relied on explicit `null` (unlikely); suggest gate doc tweak if useful.
- Do not commit or push.

## When finished (mandatory — see WORKFLOW.md §3)

1. `./bin/ci-local` green
2. `prompts/cursor/done/2026-06-14-0900-query-response-omit-na-fields/`
3. Remove claimed file from `in-progress/` and `next/`
4. Tell Paul **slice ready for review**

---

## Exit criteria

- `public_dict()` omits step-1-only fields on `found` / `assembled` / `not_found`
- Step-1 responses still include `total_matches` + `delivery` when set
- Null `quote` / `provenance` omitted (not `"key": null`)
- Tests updated; `./bin/ci-local` green
- `docs/architecture.md` reflects new serialization policy

Suggested commit message:

```
fix: omit N/A QueryResponse fields in public JSON by outcome

Omit total_matches and delivery on step-2 deliver responses; omit null
quote and provenance. Aligns with create_on_deliver omission precedent.
```