# Program 3 — Slice 1550: Policy, docs, and program close (final slice)

> **READY** — Claim per `prompts/cursor/WORKFLOW.md` before starting.

**Program:** [`docs/plans/entity-protocol-legacy-cleanup-program.md`](../../docs/plans/entity-protocol-legacy-cleanup-program.md)  
**Prerequisite:** Slices **1500–1540** approved.

**Note:** This is the **program final slice** — Grok runs `pytest -m full` at review per `WORKFLOW.md`.

---

## Objective

Scrub **operator-facing docs** and **`describe_network` policy** of legacy `entity_key` / `binding` negotiation language. Mark Program 3 complete in plan doc. Queue nothing that edits `TODO.md` (Grok + Paul after manual gate).

---

## Read first

- [`src/network/introspection.py`](../../src/network/introspection.py) — `_POLICY_*`, policy dict ~line 790
- [`docs/architecture.md`](../../docs/architecture.md) — legacy entity_key mentions
- [`docs/full-code-walkthrough.md`](../../docs/full-code-walkthrough.md)
- [`README.md`](../../README.md)
- [`docs/onboarding.md`](../../docs/onboarding.md)
- [`examples/networks/crm/README.md`](../../examples/networks/crm/README.md)
- [`docs/manual-checks/2026-06-13-program2-post-program-gate.md`](../../docs/manual-checks/2026-06-13-program2-post-program-gate.md) — status commands
- [`prompts/system/PROJECT_BRIEF.md`](../../prompts/system/PROJECT_BRIEF.md)
- [`docs/plans/README.md`](../../docs/plans/README.md)

---

## Locked design

### 1. `describe_network` / MCP policy

- **Remove** from primary `policy` map (or equivalent): `entity_unknown`, `entity_bind`, `entity_key_unresolved`, `entity_validated`, legacy `entity_growth` wording that references `entity_key`.
- **Keep / expand** `_POLICY_MVR_REDESIGN_TARGET` as the authoritative query rules.
- Add short **status inspect** paragraph: `GET /status` / `network status` use `id` or `lookup` JSON; response includes `resolve: { id, lookup }`; exact match only.
- Add **registry** one-liner: entity rows use `bind_values` keyed by `mvr.bind_fields`.

Optional: `policy.historical` subsection with one sentence “Pre-2026 entity_key protocol removed” — no detailed legacy instructions.

### 2. Architecture + walkthrough

- Remove `MYCELIUM_ALLOW_LEGACY_ENTITY_KEY` references.
- Document `bind_values` registry shape and generic `bind_index`.
- Document status `resolve` JSON (D2-b).

### 3. README / onboarding / CRM example

- Status examples: `--lookup-json` / `--id`.
- No `network status --entity`.
- Seed `people[]` format unchanged; note imported into `bind_values`.

### 4. Program 2 manual gate doc

- Update status check commands (Checks 1, 7, etc.) to target inspect flags.
- Add note: superseded by Program 3 gate when Paul runs it (optional short § at top).

### 5. `PROJECT_BRIEF.md`

- Public API: `lookup` / `id` / `delivery_id` — not `entity_key`.

### 6. Program plan + plans index

- Mark [`entity-protocol-legacy-cleanup-program.md`](../../docs/plans/entity-protocol-legacy-cleanup-program.md) **Complete**.
- Update [`docs/plans/README.md`](../../docs/plans/README.md) — Program 3 under completed programs.

### 7. New manual gate doc (optional but recommended)

Create [`docs/manual-checks/2026-06-14-program3-post-program-gate.md`](../../docs/manual-checks/2026-06-14-program3-post-program-gate.md):

- Short checklist: `entities.json` has `bind_values`; status `--lookup-json`; query unchanged; no `entity_key` in public JSON; `./bin/ci-local`.
- Status: **PENDING**

---

## Tests (smoke — mandatory)

- `./bin/ci-local` green.
- **New (optional):** `test_describe_network_policy_omits_legacy_entity_key_outcomes` — policy keys or text do not advertise `entity_key` negotiation as current.

---

## Out of scope

- `TODO.md` (Grok + Paul)
- Program 4 operator write
- Website repo

---

## Deliverable

`prompts/cursor/done/2026-06-14-1550-policy-docs-hygiene/` — suggested commit:

```
docs: Program 3 protocol cleanup — bind_values, resolve status, policy hygiene
```

**For Grok + Paul in `output.md`:**

- Program 3 ready for manual gate
- Suggest `program_3` tag after gate CLEAR
- TODO: mark Program 3 complete; Program 4 next