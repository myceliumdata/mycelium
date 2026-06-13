# MVR redesign — Slice M1 (docs + schema notes)

**Program:** [`docs/plans/mvr-redesign-program.md`](../../docs/plans/mvr-redesign-program.md)  
**Prerequisite:** Manual gate clear; Program 1 complete  
**Breaking:** No runtime behavior change in M1 — documentation and schema narrative only

---

## Objective

Land operator and implementer docs for the locked MVR redesign: UUID identity, two-step `delivery_id` protocol, MVR vs lookup separation. Prepare architecture and capabilities text for slices M2+.

---

## Read first

- [`docs/plans/mvr-redesign-program.md`](../../docs/plans/mvr-redesign-program.md) — locked decisions R1–R15
- [`docs/plans/mvr-best-practices.md`](../../docs/plans/mvr-best-practices.md)
- [`docs/architecture.md`](../../docs/architecture.md) — public query flow, `EntityQuery`, outcomes
- [`prompts/cursor/WORKFLOW.md`](../WORKFLOW.md)

---

## Tasks

1. **Architecture** — Update [`docs/architecture.md`](../../docs/architecture.md):
   - Replace `entity_key` / `binding` / `name_source` narrative with `id`, `lookup`, two-step `delivery_id` (+ `quote_id`).
   - Document `lookup_resolved` outcome.
   - Cross-link program + best-practices docs.
   - Note: Program 2 (versioned bind) still deferred.

2. **Introspection / describe_network** — Update policy/capabilities text in [`src/network/introspection.py`](../../src/network/introspection.py) **comments or static guide strings only** if they document the *target* protocol (mark “shipping in MVR redesign” if current code still old shape). Do **not** change runtime query behavior in M1.

3. **Plans index** — Update [`docs/plans/README.md`](../../docs/plans/README.md): add `mvr-redesign-program.md`, `mvr-best-practices.md` under active backlogs; note Program 2 blocked on this program.

4. **Best practices** — Review [`docs/plans/mvr-best-practices.md`](../../docs/plans/mvr-best-practices.md); expand only if gaps found during architecture pass.

5. **EntityQuery JSON schema examples** — Add a short `docs/plans/mvr-redesign-entity-query-examples.md` with step-1 / step-2 request and response examples (from program doc). Optional if fully covered in program doc — prefer one canonical place.

---

## Constraints

- **Do not edit `TODO.md`.**
- **Do not** change `EntityQuery` / graph / resolution runtime behavior (M2–M9).
- **Do not** remove `entity_key` from code yet.
- Match existing doc tone; no drive-by refactors.

---

## Verification

- `./bin/ci-local` green (docs-only slice should not break build).
- No test changes required unless introspection string assertions break.

---

## Output

Deliver under `prompts/cursor/done/2026-06-13-1000-mvr-redesign-slice-m1/`:

- `output.md` — summary + **For Grok + Paul** (`TODO.md` pointers if any)
- Do not commit; Paul reviews after `review.md`

---

## Exit criteria

- Architecture and plans index reflect locked MVR redesign protocol.
- Capabilities/guide strings aligned or explicitly marked pending implementation.
- Ready for M2 (`DeliveryStore` + TTL).