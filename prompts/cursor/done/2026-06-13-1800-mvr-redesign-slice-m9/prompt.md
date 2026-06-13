# MVR redesign — Slice M9 (CLI, MCP, admin, examples, README migration)

**Program:** [`docs/plans/mvr-redesign-program.md`](../../docs/plans/mvr-redesign-program.md)  
**Prerequisite:** M8 reviewed and approved  
**Depends on:** M4–M8 target two-step protocol (resolve → deliver, metering, batch, create-on-deliver)

---

## Objective

Migrate **public surfaces** from legacy `entity_key` / `binding` to the **target two-step protocol** (`id` or `lookup` → `delivery_id` → deliver). Update CLI, MCP, admin status, example query JSON, and READMEs. Retire or hard-gate legacy resolution paths that M9 supersedes.

**Not in M9:** polish backlog pass (M10).

---

## Read first

- [`docs/plans/mvr-redesign-program.md`](../../docs/plans/mvr-redesign-program.md) — R1–R15, two-step protocol, removed fields
- [`docs/architecture.md`](../../docs/architecture.md) — MVR redesign (target) §
- [`docs/plans/mvr-redesign-entity-query-examples.md`](../../docs/plans/mvr-redesign-entity-query-examples.md)
- [`src/main.py`](../../src/main.py) — CLI `query` command
- [`src/mycelium_mcp/server.py`](../../src/mycelium_mcp/server.py) — MCP schemas + `query_entity`
- [`src/mycelium_admin/server.py`](../../src/mycelium_admin/server.py) — admin query API
- [`src/network/introspection.py`](../../src/network/introspection.py) — `describe_network` / `protocol_status`
- [`examples/networks/crm-metering/queries/`](../../examples/networks/crm-metering/queries/) — legacy fixtures to replace

---

## Tasks

1. **CLI `query`** — Replace required `--entity-key` with target flags:
   - Step 1: `--id` **or** `--lookup-json` (AND map); optional `--attributes`, `--provenance`
   - Step 2: `--delivery-id` (+ `--quote-id` when metered)
   - Remove or deprecate `--employer` / `--binding-json` (document migration in help text)
   - Update epilog/help to describe two-step flow

2. **MCP** — Update `query_entity` schema descriptions; remove “legacy until M4” wording; ensure `EntityQuery` JSON examples in tool docs match target protocol. Update error/debug paths that reference `entity_key` only.

3. **Admin** — Align admin query/status payloads and UI-facing docs with target fields and outcomes (`lookup_resolved`, `delivery`, etc.).

4. **Example query JSON** — Replace `examples/networks/*/queries/` legacy `entity_key` fixtures with two-step JSON (step-1 resolve + step-2 deliver). Include metered arc on `crm-metering` and at least one batch example on `crm`.

5. **README / guide migration** — Update `examples/networks/*/README.md`, `guide.md`, root README references, and MCP README for two-step usage. Set `protocol_status` in introspection to reflect target runtime (no longer “legacy until M9”).

6. **Legacy path** — Remove or gate `entity_key` / `binding` resolution in supervisor/graph where target protocol now covers all CLI/MCP entry points. Keep internal test helpers only if needed; do not break smoke tests — migrate them to `lookup` / `delivery_id`.

7. **Tests** — Smoke: CLI or graph roundtrip via target flags; MCP JSON step-1 + step-2; at least one updated example JSON exercised in tests.

---

## Constraints

- **Do not edit `TODO.md`.**
- **Do not** work the M10 polish backlog (`mvr-redesign-polish-m10.md`).
- **Do not** implement Program 2 versioned bind storage.

---

## Governance (mandatory)

- **Do not edit `TODO.md`.** Roadmap updates are for Grok + Paul after review.
- In `output.md`, add **"For Grok + Paul"**: what to check off, any roadmap notes.
- Cursor delivers: code, tests, task-scoped docs, and `output.md` only.

## When finished (mandatory)

1. `./bin/ci-local` green — record counts in `output.md`
2. Create `prompts/cursor/done/2026-06-13-1800-mvr-redesign-slice-m9/` with `prompt.md` + `output.md`
3. Every file in `output.md` must exist on disk
4. Remove claimed prompt from **`in-progress/`** and **`next/`**
5. **Do not `git commit` or `git push`**
6. Tell Paul: **"slice ready for review"**

See `prompts/cursor/WORKFLOW.md` §3.

---

## Verification

```bash
./bin/ci-local
```

---

## Output

`prompts/cursor/done/2026-06-13-1800-mvr-redesign-slice-m9/` — note M10 queue hint in **For Grok + Paul** only.

Do not commit until Grok review.

---

## Exit criteria

- CLI supports step-1 `id`/`lookup` and step-2 `delivery_id` (+ `quote_id`)
- MCP schemas and example JSON use target protocol
- Example network query fixtures migrated
- Legacy `entity_key` path retired or gated from public entry points
- Smoke green