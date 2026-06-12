# Program 1 — Slice 1: Versioned storage + research write path

**Status:** Ready (June 2026)  
**Program:** [`attribute-provenance-program1.md`](attribute-provenance-program1.md)  
**Depends on:** Nothing (breaking change on specialist storage)

---

## Objective

Introduce `versioned_provenance_v1` for extended attributes. Research and pending writes **append** versions. Flat v1 field entries **fail loud**. No specialist template / introspection / query changes in this slice (tests may stub minimal reads via `specialist_fields` only).

---

## Implement

### 1 — `src/agents/specialist_fields.py`

New module per program spec (`current_version`, `append_version`, `field_has_value`, flat v1 rejection, version id `v1`/`v2`/…).

### 2 — `src/tools/research.py`

- `_validate_and_build_record` — build a **version body** (not flat record). Map `researched_at` → version `at`; `sources` → `[{url}]`.
- `_persist_proposal` — for each field, load existing versioned entry or init empty `versions: []`. **Append** on status transitions; **in-place update** when current is already `pending` (P1-11). Set `current_version_id` on append only.
- `_mark_pending` — first `pending` appends `v1`; retry updates current pending in place (`at`, `last_error`; preserve `started_at`). Skip if current is `found` (P1-11).
- `_pending_record` — return version-shaped pending dict (include `actor` with category + specialist_name passed through `_execute_research`).
- Pass `category` and `specialist_name` into persist helpers for `actor`.

**Found skip semantics:** If current version is `found`, do not replace with pending/na on partial errors (preserve today’s behavior using `current_version`).

### 3 — `src/agents/entity_growth.py`

Read timestamp from `current_version(entry)["at"]` instead of `researched_at` (P1-10: attempt time for any status). Import helpers from `specialist_fields`.

### 4 — `src/agents/specialists/base.py`

Update default `storage_strategy.json` template:

- `"strategy": "versioned_provenance_v1"`
- Notes mention versioned field shape; flat v1 unsupported.

New specialist dirs created after this slice get v2 strategy. Existing dirs: strategy file updated on next `SpecialistStorage` init only if you touch `_ensure_initialized` — **optional**: add one-line doc that refresh wipes agents dir. Do **not** add migration logic.

### 5 — Tests

Update **all** tests that write or assert flat field blobs to versioned shape:

- `tests/test_specialist_sync_research.py`
- `tests/test_specialist_research_integration.py`
- `tests/test_entity_growth.py`
- `tests/test_network_status.py` (storage fixtures)
- Any other failing tests from grep `researched_at` / `"status": "found"` in `tests/`

Add focused unit tests: `tests/test_specialist_fields.py`

- append two research versions → two entries, current = v2
- flat v1 entry → `validate_versioned_field` raises
- pending / na version append
- `current_value` / `field_has_value` on each status

### 6 — Docs (minimal)

One paragraph in `docs/architecture.md` § Storage: extended attrs use `versioned_provenance_v1`; flat v1 invalid; refresh network to reset.

---

## Do NOT (Cursor lane)

- Do not edit `specialist_agent.py.j2` or regen framework specialists (Slice 2).
- Do not change `introspection.py` field display (Slice 2).
- Do not add `QueryResponse.provenance` (Slice 3).
- Do not touch `entities.json` / MVR / `bind_index`.
- Do not edit `TODO.md`.

---

## Smoke expectations

- Research integration tests pass with versioned storage assertions.
- `entity_growth` attribution still updates registry `last_researched_at` from current version `at`.
- Specialist graph tests that read storage **may fail** until Slice 2 — if so, document in `output.md` and limit failures to specialist read path only; prefer updating template read helpers in Slice 2 before merge. **Target:** keep full pytest green by minimally adjusting any supervisor tests that read raw flat shape in the same slice only if they block CI.

---

## Paul decisions (locked)

| # | Decision |
|---|----------|
| Q1 | Hard cutover; flat v1 fails loud |
| Q2 | No lazy migration |