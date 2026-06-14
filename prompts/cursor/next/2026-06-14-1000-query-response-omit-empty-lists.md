# QueryResponse public JSON — omit empty negotiation fields (+ null trace_id)

> **READY** — Move to `in-progress/` before starting (see `prompts/cursor/WORKFLOW.md`).

**Context (Paul + Grok, June 2026):** After `74a7f94`, step-2 responses no longer emit null `total_matches`/`delivery`. Paul wants the same **noise reduction** for fields that are always empty on public surfaces, without dropping fields that help agents when they carry data.

**Key finding:** On CLI/MCP/admin (target protocol only), `required_fields` and `suggestions` are **always `[]`** today. Public APIs reject `entity_key`/`binding` (M9); partial lookup returns `not_found`, not `entity_unknown` + `required_fields`. Those two fields only populate on internal `entity_key` graph tests (`MYCELIUM_ALLOW_LEGACY_ENTITY_KEY=1`) — not on public wire.

**Prerequisite:** `74a7f94` (outcome-aware omission) on `main`.

---

## Read first

- `prompts/cursor/WORKFLOW.md`
- `src/models/state.py` — `QueryResponse.public_dict()`, `_STEP1_PUBLIC_OUTCOMES`
- `src/main.py` — `_entity_query_from_args` (no legacy CLI flags)
- `src/mycelium_mcp/server.py` — public API rejects `entity_key`/`binding`
- `src/agents/dispatch.py` — `target_resolve_node` (target vs legacy defer)
- `admin-ui/src/App.tsx` — already renders `required_fields` / `suggestions` only when `length > 0`
- `prompts/cursor/done/2026-06-14-0900-query-response-omit-na-fields/` — prior slice

---

## Objective

Extend `QueryResponse.public_dict()` to **omit empty list fields and null trace_id** on public JSON. Keep in-memory `QueryResponse` models unchanged. When lists are non-empty, include them (future-proof for suggestions / negotiation).

**Non-goals:** Removing `required_fields`/`suggestions` from the Pydantic model; deleting legacy graph code; changing target lookup semantics to populate `required_fields` (separate product slice if desired).

---

## Locked semantics — additional omission rules

Add to `public_dict()` after existing outcome-aware logic:

| Field | Rule |
|-------|------|
| `required_fields` | **Omit key** when `[]` or missing; **include** when non-empty |
| `suggestions` | **Omit key** when `[]`; **include** when non-empty (serialize suggestion objects) |
| `trace_id` | **Omit key** when `None` (tracing off); **include** when set |
| `thread_id` | **Always include** when set — agents use it to correlate step 1 ↔ step 2 |
| `results` | **Always include** — `[]` on step 1 is intentional (“no rows until deliver”) |
| `message`, `outcome`, `debug` | **Always include** — primary agent/human context |

Do not emit `"required_fields": []` or `"suggestions": []`.

### Future product note (document only — do not implement here)

Paul may later want target step-1 partial lookup (e.g. name only) to return `required_fields: ["employer"]` instead of blunt `not_found`. Omit-when-empty supports that without API churn. Near-miss `suggestions` on target lookup is similarly future-ready.

---

## Implement

### 1 — `QueryResponse.public_dict()` (`src/models/state.py`)

After existing step-1 / deliver pops:

```python
if not self.required_fields:
    data.pop("required_fields", None)
if not self.suggestions:
    data.pop("suggestions", None)
if self.trace_id is None:
    data.pop("trace_id", None)
```

Update docstring with full omission table (step-1 fields, deliver fields, empty lists, null trace).

### 2 — Docs + MCP

- `docs/architecture.md` — M9 public surfaces paragraph: omit empty `required_fields`/`suggestions`; `trace_id` when unset.
- `src/mycelium_mcp/server.py` — schema description: negotiation fields present only when non-empty.

### 3 — Tests (smoke)

| Test | Assert |
|------|--------|
| `test_public_dict_omits_empty_required_fields_and_suggestions` | `found` response with `[]` → keys absent in `public_dict()` |
| `test_public_dict_includes_required_fields_when_set` | Builder with `outcome="entity_unknown"`, `required_fields=["employer"]` → key present |
| `test_public_dict_includes_suggestions_when_set` | Builder with non-empty `suggestions` → key present |
| `test_public_dict_omits_null_trace_id` | `trace_id=None` → absent; `trace_id="tr_…"` → present |
| Update wire tests if they assert `"required_fields": []` in CLI/MCP/admin JSON | Expect keys **absent** on target-protocol responses |

Keep internal graph tests asserting `response.required_fields == ["employer"]` on **in-memory** objects — only public JSON changes.

### 4 — Admin UI

No code change expected (`length > 0` guards). `./bin/ci-local` must pass.

---

## Scope boundaries (strict)

**May modify:**

- `src/models/state.py`
- `tests/test_mvr_entity_query_models.py` and/or new small test block
- `tests/test_mvr_target_public.py`, `tests/test_admin_daemon.py` (if wire JSON asserts empty lists)
- `src/mycelium_mcp/server.py` (description only)
- `docs/architecture.md` (M9 paragraph only)

**Out of scope:**

- `TODO.md`
- `dispatch.py` / target lookup behavior
- Removing `EntityQuery.entity_key` from model
- Program 3 legacy graph deletion

---

## Verification

```bash
./bin/ci-local
```

Manual (document in `output.md`):

```bash
uv run mycelium query --network crm \
  --lookup-json '{"name": "Road Runner", "employer": "Acme Corp"}'
# JSON should NOT contain required_fields, suggestions, or trace_id (unless tracing on)

uv run mycelium query --network crm --delivery-id <id>
# Same — no empty negotiation keys
```

---

## Governance (mandatory)

- **Do not edit `TODO.md`.**
- In `output.md`, **For Grok + Paul**: confirm `required_fields` never non-empty on public wire today; note future partial-MVR option.
- Do not commit or push.

## When finished (mandatory — see WORKFLOW.md §3)

1. `./bin/ci-local` green
2. `prompts/cursor/done/2026-06-14-1000-query-response-omit-empty-lists/`
3. Remove claimed file from `in-progress/` and `next/`
4. Tell Paul **slice ready for review**

---

## Exit criteria

- Empty `required_fields` and `suggestions` omitted from public JSON
- Non-empty lists still included
- Null `trace_id` omitted
- `thread_id` and `message` still present
- Tests + `./bin/ci-local` green
- `docs/architecture.md` updated

Suggested commit message:

```
fix: omit empty required_fields, suggestions, and null trace_id in public JSON

Reduce QueryResponse noise on target protocol; keep fields when they carry
negotiation or tracing context.
```