# Program 3 — Slice 1520: Status surfaces — target resolve JSON (D2-b)

> **READY** — Claim per `prompts/cursor/WORKFLOW.md` before starting.

**Program:** [`docs/plans/entity-protocol-legacy-cleanup-program.md`](../../docs/plans/entity-protocol-legacy-cleanup-program.md)  
**Prerequisite:** Slices **1500** + **1510** approved.

**Paul (D2-b):** Status mirrors query step-1 — `resolve: { id, lookup }`. No `entity_key`. Exact inspect only.

---

## Objective

Align CLI and admin **inspect** surfaces with target protocol vocabulary. Breaking change to status JSON is intentional.

---

## Read first

- [`src/main.py`](../../src/main.py) — `network status --entity`
- [`src/mycelium_admin/server.py`](../../src/mycelium_admin/server.py) — `GET /status`
- [`src/network/introspection.py`](../../src/network/introspection.py) — `NetworkStatusSummary`, formatters
- [`src/agents/entity_resolution.py`](../../src/agents/entity_resolution.py) — `resolve_status_for_target_lookup`
- [`admin-ui/src/mvr.ts`](../../admin-ui/src/mvr.ts), [`admin-ui/src/types.ts`](../../admin-ui/src/types.ts), [`admin-ui/src/EntityDrilldown.tsx`](../../admin-ui/src/EntityDrilldown.tsx)
- [`tests/test_network_status.py`](../../tests/test_network_status.py), [`tests/test_admin_daemon.py`](../../tests/test_admin_daemon.py)

---

## Locked design

### 1. CLI `mycelium network status`

**Add:**

- `--id UUID`
- `--lookup-json '{"name":"…","employer":"…"}'`

**Remove:**

- `--entity` (no alias — hard remove)

Pass to `build_network_status(resolve_id=…, resolve_lookup=…)` (new API — see below).

### 2. Admin `GET /status`

**Add:** `id` query param (registry UUID).

**Keep:** `lookup` JSON string (already exists).

**Remove:** `entity` query param.

### 3. `NetworkStatusSummary` → JSON shape

Replace resolution fields:

| Old | New |
|-----|-----|
| `entity_key` | **`resolve`**: `{ "id": str \| null, "lookup": dict \| null }` — exactly one of id or lookup set when drill-down active |
| `entity_matches` | `resolve_matches` |
| `entity_resolution_kind` | `resolve_kind` |
| `entity_required_fields` | `resolve_required_fields` |
| `entity_suggestions` | `resolve_suggestions` |
| `entity_match_summaries` | `resolve_match_summaries` |
| `entity_fields` | **unchanged** (drill-down attribute/bind rows) |

When no drill-down requested, `resolve` is `null` (or omitted in JSON — match existing omit-null style if used elsewhere).

**Remove** code path calling `resolve_entity_for_lookup(entity_key)` — use **`resolve_status_for_target_lookup(lookup)`** or id → `lookup_by_id` only.

Inspect does **not** run fuzzy suggestion ranking.

### 4. Human CLI formatters

Update `format_status_demo` / `format_status_verbose` to print `resolve.id` or formatted `resolve.lookup`, not `entity_key`.

### 5. Admin UI

- `StatusResponse` type: `resolve`, `resolve_matches`, etc.
- `inspectStatusParams`: send `id` param in ID mode (not `entity`).
- `EntityDrilldown`: header from `resolve` (format lookup map or id).
- `hasStatusTarget`: check `resolve` inputs in params (`id` or `lookup`).

Rebuild admin-ui (`./bin/ci-local` includes vite build).

---

## Tests (smoke — mandatory)

| Test | Assert |
|------|--------|
| **Update** `test_status_lookup_map_single_match` | `resolve.lookup` matches input; `resolve_matches == 1`; no `entity_key` key |
| **New:** `test_status_by_id` | `GET /status?id=<uuid>` → exact match |
| **New:** `test_status_cli_lookup_json` | CLI `--lookup-json` drill-down (subprocess or `build_network_status` unit) |
| **New:** `test_status_json_omits_entity_key` | `status_to_dict` has no `entity_key` |
| **Update** network status tests using `entity_key=` | Use `resolve_lookup` / `resolve_id` |

`./bin/ci-local` green.

---

## Out of scope

- Removing `resolve_entity_for_lookup` entirely (1530) — but status must not call it after this slice
- `describe_network` policy cleanup (1550)

---

## Docs (light)

- Update [`docs/manual-checks/2026-06-13-program2-post-program-gate.md`](../../docs/manual-checks/2026-06-13-program2-post-program-gate.md) Check 1 / 7 commands: `--lookup-json` or `--id` instead of `--entity` (only the lines this slice breaks).

Do not edit `TODO.md`.

---

## Deliverable

`prompts/cursor/done/2026-06-14-1520-status-surfaces-target/` — suggested commit:

```
feat(status): target resolve JSON and id/lookup-json inspect inputs
```