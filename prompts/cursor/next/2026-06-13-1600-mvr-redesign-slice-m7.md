# MVR redesign — Slice M7 (create-on-0 + retire legacy resolution)

**Program:** [`docs/plans/mvr-redesign-program.md`](../../docs/plans/mvr-redesign-program.md)  
**Prerequisite:** M6 reviewed and approved  
**Depends on:** M4–M6 target two-step protocol (resolve → deliver + metering)

---

## Objective

**Create on deliver** when step-1 `lookup` has 0 matches but supplies **full MVR** + `requested_attributes`; retire **`name_source`** and narrow legacy **`entity_key`** / **`entity_resolution`** paths toward target protocol. Partial lookup with 0 matches stays **`not_found`** (no create).

**Not in M7:** batch provenance shape (M8), CLI/MCP migration (M9).

---

## Read first

- [`docs/plans/mvr-redesign-program.md`](../../docs/plans/mvr-redesign-program.md) — R10, R11, create flow
- [`src/agents/entity_resolution.py`](../../src/agents/entity_resolution.py)
- [`src/network/mvr.py`](../../src/network/mvr.py)
- M4–M6 target resolve/deliver/metering modules

---

## Tasks

1. **0 matches + full MVR** — on step-1 resolve, when lookup is complete per `mvr.bind_fields` and count is 0, bind attrs into `delivery_id` scope for provisional create on step-2 deliver (not on step-1).

2. **Step-2 create** — deliver path creates provisional registry entity when scope indicates create intent; research when attrs bound.

3. **Remove `name_source`** — from `network.json` schema, introspection, MVR policy loader; `name` is a normal bind field in `lookup`.

4. **Legacy path** — document what remains for `entity_key` (CLI) until M9; reduce or gate duplicate resolution where target protocol supersedes.

5. **Tests** — smoke: partial lookup 0 → `not_found`; full MVR 0 → step-1 delivery + step-2 create; `name_source` absent/ignored.

---

## Constraints

- **Do not edit `TODO.md`.**
- **Do not** implement batch provenance JSON (M8) or CLI/MCP migration (M9).

---

## Governance (mandatory)

- **Do not edit `TODO.md`.** Roadmap updates are for Grok + Paul after review.
- In `output.md`, add **"For Grok + Paul"**: what to check off, any roadmap notes.
- Cursor delivers: code, tests, task-scoped docs, and `output.md` only.

---

## Verification

```bash
./bin/ci-local
```

---

## Output

`prompts/cursor/done/2026-06-13-1600-mvr-redesign-slice-m7/` — queue M8 in For Grok + Paul.

Do not commit until review.

---

## Exit criteria

- Full MVR + 0 matches → create on deliver
- Partial lookup 0 → `not_found`
- `name_source` removed
- Smoke green; target protocol paths preserved