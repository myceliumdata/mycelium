# Program 3 — Slice 1560: Polish (review nits)

> **READY** — Claim per `prompts/cursor/WORKFLOW.md` before starting.

**Program:** [`docs/plans/entity-protocol-legacy-cleanup-program.md`](../../docs/plans/entity-protocol-legacy-cleanup-program.md)  
**Backlog:** [`docs/plans/entity-protocol-legacy-cleanup-polish.md`](../../docs/plans/entity-protocol-legacy-cleanup-polish.md)  
**Prerequisite:** Slices **1500–1550** approved.

**Note:** This is the **program final slice** — Grok runs `pytest -m full` at review per `WORKFLOW.md`.

---

## Objective

Close non-blocking nits from Grok slice reviews (1500+). Read the polish backlog table — **do not** expand Program 3 scope.

---

## Read first

- [`docs/plans/entity-protocol-legacy-cleanup-polish.md`](../../docs/plans/entity-protocol-legacy-cleanup-polish.md) — authoritative nit list (Grok updates P5–P9 from later reviews)
- [`src/agents/entity_registry.py`](../../src/agents/entity_registry.py) — `RegistryEntity`, `_load`, `make_bind_key`, `lookup_by_bind_values`
- [`src/agents/attribute_write.py`](../../src/agents/attribute_write.py) — `ensure_entity_bind_fields`
- Grep `.name` / `.employer` on `RegistryEntity` after 1530

---

## Locked actions (P1–P4 from slice 1500)

### P1 — Remove `name` / `employer` properties

- Delete `@property` `name` and `employer` on `RegistryEntity`.
- Update remaining callers to `bind_value("name")`, `bind_value("employer")`, or `bind_values` dict access.
- `registry_entity_to_match` continues to emit flat `name`/`employer` in match dicts (derived from `bind_values`).

### P2 — MVR bind policy (verify 1510)

- If `ensure_entity_bind_fields` still hard-requires `"name"`, replace with **all `mvr.bind_fields` required** for bind_index operations (or document seed exception in code comment + test).
- If 1510 already fixed this, mark P2 **verified** in `output.md` with test name.

### P3 — Fail-loud legacy `entities.json` load

On `EntityRegistry._load`, detect entity rows with top-level `name` or `employer` but missing/empty `bind_values`:

- Raise clear `ValueError` (or dedicated error type) naming the path and fix: `./bin/refresh-example-network <net> --yes`.
- **Smoke test:** fixture legacy row → load fails with helpful message.

### P4 — Full MVR `bind_values` for bind_index

- `make_bind_key` / `lookup_by_bind_values` / `assign_bind_index`: require every `mvr.bind_fields` key present and non-empty in the input map.
- Do not pad missing fields with `""`.
- **Smoke test:** partial map raises; full CRM pair succeeds.

---

## P5–P9 (from later reviews)

Implement each row in the polish backlog that Grok filled from 1510–1550 `review.md`. If a row is empty, skip. If waived, document why in `output.md`.

---

## Tests (mandatory)

- `./bin/ci-local` green
- New/updated smokes for P3 and P4
- No regression on target-protocol query/status paths

---

## Docs

- Mark P1–P4 (and P5–P9) done in [`entity-protocol-legacy-cleanup-polish.md`](../../docs/plans/entity-protocol-legacy-cleanup-polish.md) exit criteria
- One line in [`entity-protocol-legacy-cleanup-program.md`](../../docs/plans/entity-protocol-legacy-cleanup-program.md) — polish complete (Grok may update after review)
- Do **not** edit `TODO.md`

---

## Deliverable

`prompts/cursor/done/2026-06-14-1560-program3-polish/` — suggested commit:

```
chore(program3): polish registry bind_values and load hardening nits
```