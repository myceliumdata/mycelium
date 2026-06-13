# Program 2 — Slice 2: Read surfaces (provenance + admin)

**Status:** Blocked until Slice 1 approved  
**Program:** [`attribute-provenance-program2.md`](attribute-provenance-program2.md)  
**Depends on:** Slice 1 shipped — MVR values in specialist storage

---

## Objective

Expose MVR/bind field version history on **read paths**: `provenance=true` query responses and admin entity drill-down. Default flat `results[]` unchanged.

---

## Implement

### 1 — `src/agents/query_provenance.py`

- Remove bind-field exclusion (`_bind_field_names` filter) for fields that have versioned specialist storage.
- For each delivered entity + requested attribute (including `name`, `employer` when in scope), load versioned entry from owning specialist via taxonomy resolution.
- Omit bind fields with no versioned entry yet (backward compat during cutover).

### 2 — `src/network/introspection.py`

- Extend entity field drill-down: bind fields (`field_kind: bind`) include `versions[]` from specialist storage (same shape as extended fields post–Program 1).
- Hot-path display value still from entity cache; versions from specialist file.

### 3 — Admin UI (`admin-ui/`)

- Bind field rows show expandable version timeline (reuse extended-field version UI from Program 1 polish).
- No edit controls (Program 3).

### 4 — MCP schema

- Update `mycelium://schema/query-response` resource if provenance block documents bind attrs.

### 5 — Tests

- `tests/test_query_provenance.py` — `provenance=true` includes `name` / `employer` versions when stored.
- `tests/test_admin_daemon.py` — entity drill-down returns bind `versions[]`.
- Admin-ui build passes (`npm run build`).

### 6 — Docs

- [`mvr-redesign-entity-query-examples.md`](mvr-redesign-entity-query-examples.md) — optional provenance example with bind fields.
- [`attribute-provenance-and-storage.md`](attribute-provenance-and-storage.md) — read surfaces table marked done for Program 2.

---

## Do NOT

- Operator write endpoints.
- Research prompt changes (Slice 3).
- Change unified write API semantics (Slice 1).

---

## Verification

`./bin/ci-local` green; manual spot-check admin version cards for Andrea Kalmans bind fields optional.