# Entity key suggestions — Phase 1 spec (locked)

> **Superseded field (June 2026, slice 1450):** Public `suggestions[]` use `suggested_lookup` (target-protocol lookup map), not `entity_key`. This doc retains historical `entity_key` naming for slice 1 context; see [`fuzzy-lookup-policy.md`](fuzzy-lookup-policy.md).

**Status:** Approved for implementation (Paul + Grok, June 2026)  
**Conversation:** [`docs/plans/conversations/2026-06-08-entity-key-negotiation.md`](conversations/2026-06-08-entity-key-negotiation.md)  
**Cursor slice:** `prompts/cursor/next/2026-06-09-1000-entity-key-suggestions-protocol.md`  
**Supersedes:** vague “fuzzy entity_key matching”; silent auto-resolve is **out of scope**

---

## Problem

Visiting agents (e.g. Claude) query `Andrea Kalman` when the seed has `Andrea Kalmans`. Today: exact miss → plain `not_found`, no structured hint → caller improvises retries. Paul wants **suggest, don’t resolve** — foundation for agent-to-agent negotiation (x402 Phase A).

---

## Locked design decisions

### 1. Public `outcome` on `QueryResponse` (machine-readable)

Add optional fields to `QueryResponse` (`src/models/state.py`):

| Field | Type | Notes |
|-------|------|-------|
| `outcome` | `str \| None` | Public, agent-facing. Mirrors debug `outcome=` for all paths when set. |
| `suggestions` | `list[EntityKeySuggestion]` | Empty unless near-miss suggestions exist. |

New model `EntityKeySuggestion`:

```python
class EntityKeySuggestion(BaseModel):
    entity_key: str      # retry key — seed display name (canonical for re-query)
    id: str              # stable seed UUID
    name: str
    employer: str | None = None
    score: float         # 0.0–1.0
    reason: str          # "sequence_ratio" (slice 1 only)
```

**Outcome values (slice 1):**

| `outcome` | When |
|-----------|------|
| `found` | Identity-only hit (existing `response_found`) |
| `assembled` | Specialist merge complete (existing `response_assembled`) |
| `not_found` | Zero exact matches **and** zero suggestions above threshold |
| `entity_key_unresolved` | Zero exact matches **and** ≥1 suggestion above threshold |

**Reserved for slice 2 (do not implement yet):** `entity_unknown` (Paul Murphy — no near-miss).

**Backward compatibility:** Existing consumers that ignore new fields keep working. CLI/MCP JSON gains `outcome` + `suggestions` keys (omit or `null` when unset is fine; prefer explicit `outcome` on every response).

Keep `debug` `outcome=` in sync with public `outcome`.

### 2. Confirmation shape — retry with `entity_key` only

**No** `confirm_suggestion_id` in slice 1.

Contract for visiting agents (document in `describe_network` policy + MCP tool docstrings):

> On `outcome: "entity_key_unresolved"`, call `query_entity` again with `entity_key` set to a chosen `suggestions[].entity_key` (usually the highest `score`). Same `thread_id` optional. **No attribute data is authoritative until an exact match resolves.**

### 3. Suggestion thresholds & ranking

**When to suggest:** Only after **zero exact matches** (`find_by_key` unchanged for exact path).

**Do not suggest for:** empty key; UUID-shaped keys with no exact id hit (no fuzzy UUID).

**Normalization (comparison only — never rewrite caller’s `entity_key` in messages):**

```text
strip → lowercase → collapse whitespace → remove apostrophe and hyphen
```

**Score:** `difflib.SequenceMatcher.ratio()` on normalized query vs normalized seed `name`.

**Inclusion rules (all must pass):**

1. `score >= 0.85` (`SUGGESTION_MIN_SCORE`)
2. First token of normalized query equals first token of normalized candidate name (avoids cross-person noise)
3. Cap at **5** suggestions, sorted by `score` descending

**If no candidate passes:** `outcome=not_found`, `suggestions=[]` (today’s message shape; slice 2 may upgrade true unknowns to `entity_unknown`).

**Motivating case:** `Andrea Kalman` vs seed `Andrea Kalmans` → single suggestion, score ≈ 0.96.

### 4. Distinct from unknown entity (slice 2)

| Case | Exact match | Near-miss | Slice 1 outcome |
|------|-------------|-----------|-----------------|
| Kalman / Kalmans | No | Yes | `entity_key_unresolved` |
| Paul Murphy | No | No | `not_found` (unchanged until slice 2) |
| Kevin Zhang ×2 | Yes (multiple) | — | existing multi-match (`found` / `assembled`) |

---

## API: `resolve_entity_key()`

**Location:** `src/agents/seed.py` (or new `src/agents/entity_resolution.py` if cleaner — prefer colocated with seed lookup).

```python
@dataclass
class EntityResolution:
    kind: Literal["exact", "multiple", "suggest", "none"]
    matches: list[dict[str, Any]]       # seed rows for exact / multiple
    suggestions: list[EntityKeySuggestion]
```

**Algorithm:**

1. `matches = find_by_key(entity_key)` — exact path unchanged.
2. If `len(matches) >= 1` → `exact` or `multiple` (same as today; `multiple` when len > 1 and name lookup).
3. Else if key is UUID-shaped and missing → `none`.
4. Else rank all seed `name` values → if any above threshold → `suggest`.
5. Else → `none`.

`find_by_key` remains public; supervisor calls `resolve_entity_key` instead.

---

## Supervisor & graph short-circuit

**On `kind == "suggest"`:**

- **Do not** run classification.
- **Do not** populate `specialists_to_invoke`.
- **Do not** invoke specialists or Tavily.
- Set state for assemble: e.g. `entity_resolution_kind="suggest"`, `entity_suggestions=[...]`.
- Route: supervisor → `assemble_response` (skip `build_context` / `invoke_specialists`).

**On `kind == "none"`:** existing behavior for slice 1 (including classify when `requested_attributes` set — pre-existing; slice 2 gates unknown+attrs).

**On `exact` / `multiple`:** unchanged.

**New response builder:** `response_entity_unresolved()` in `src/agents/responses.py`:

- `results=[]` always (no `id` / `employer` / attribute values from suggested rows)
- `outcome="entity_key_unresolved"`
- `suggestions` populated
- `message` example: `No exact match for 'Andrea Kalman'. Did you mean 'Andrea Kalmans' (Lontra Ventures)? Re-query with that entity_key to continue.`
- Include `employer` in message when present (helps agents; not in `results`)

`assemble_response_node` checks resolution kind before `not_found`.

---

## MCP / CLI / onboarding

1. **`build_network_capabilities()`** — add `policy.entity_key_unresolved` string explaining retry contract.
2. **`query_entity` docstring** — document `outcome` + `suggestions` in response JSON.
3. **CLI** — no flag changes; JSON output picks up new fields automatically.
4. **Optional:** one line in `examples/networks/crm-seeded/guide.md` (agent-facing) — only if it fits existing tone.

---

## Tests (smoke)

Use tmp network root or `examples/networks/crm-seeded` seed (contains `Andrea Kalmans`).

| Test | Assert |
|------|--------|
| `Andrea Kalman` + `email` | `outcome=entity_key_unresolved`; `suggestions[0].entity_key == "Andrea Kalmans"`; `results==[]`; no specialist contributions / no research side effects (mock Tavily or assert audit log has no invoke) |
| `Andrea Kalmans` + `email` | normal assembled/found path (not unresolved) |
| `NoSuchPerson-xyz` | `outcome=not_found`; `suggestions==[]` |
| UUID miss | `not_found` or `none`; no suggestions |
| Multi-match `Kevin Zhang` | unchanged — multiple exact matches, not suggest |

---

## Explicit non-goals (slice 1)

- Silent fuzzy resolve
- `confirm_suggestion_id`
- `entity_unknown` / `required_fields` (slice 2)
- Entity registry / persistence
- Changes to `EntityQuery` shape
- Metering / x402

---

## Files (expected touch)

| File | Change |
|------|--------|
| `src/models/state.py` | `EntityKeySuggestion`, `QueryResponse.outcome`, `QueryResponse.suggestions` |
| `src/agents/seed.py` (or `entity_resolution.py`) | `resolve_entity_key`, normalization, scoring |
| `src/agents/supervisor.py` | use resolver; short-circuit suggest |
| `src/agents/responses.py` | `response_entity_unresolved`; set `outcome` on existing builders |
| `src/agents/dispatch.py` | assemble branch for suggest |
| `src/network/introspection.py` | policy string |
| `src/mycelium_mcp/server.py` | docstring touch |
| `tests/` | new `test_entity_key_suggestions.py` (smoke) |