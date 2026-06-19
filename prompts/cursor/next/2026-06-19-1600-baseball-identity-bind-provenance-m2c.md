# Baseball identity bind + full provenance parameters (M2c)

> **READY** — Claim per `prompts/cursor/WORKFLOW.md`. **After M2b** (`2026-06-19-1500`) or in parallel if M2a/M2b not blocking.

**Priority:** Fix hand-test yellow flag — `debut_team` / `debut_year` must come from **registry bind**, not factory web research, when requested as attrs.

**Parent:** [`docs/plans/conversations/2026-06-19-warehouse-factory-layer3-specialist-emergence.md`](../../docs/plans/conversations/2026-06-19-warehouse-factory-layer3-specialist-emergence.md)

**Principles:**

- **Bind fields are registry ground truth** — not warehouse, not Tavily.
- **Warehouse specialists** — ensure `parameters` lists **all** values including `warehouse` path (complete M1 provenance gap).
- **Do not edit `TODO.md`.**

---

## Objective

When step 1 includes `debut_team` and/or `debut_year` in `requested_attributes`, step 2 returns bind values from the entity registry with provenance that reflects **bootstrap/registry** (not `actor.kind: research` + baseball-reference URL).

Warehouse attrs (`career_hr`, `birth_date`) still use dataset + computation provenance; add `warehouse` to `parameters` on every warehouse write.

---

## Locked behavior

| Field | Source | Provenance actor |
|-------|--------|------------------|
| `debut_team`, `debut_year`, `player` | `RegistryEntity.bind_values` | `specialist` / `bind` or `registry` — **not** research |
| `career_hr`, `birth_date`, … | Warehouse compute | `specialist` + dataset + computation |

**No web research** for MVR bind fields on `bootstrap_only` player record type on baseball roots.

---

## Implement

### 1 — `player_identity_specialist` (pack or framework policy)

Options (pick minimal):

- **A:** Pack `player_identity_specialist.py` that reads bind fields from registry via graph context / entity registry API and writes **found** versions without Tavily.
- **B:** Framework: bind fields in `requested_attributes` satisfied in `assemble_response` / identity path from registry without invoking research template.

Document choice in `output.md`.

### 2 — Full warehouse `parameters`

Update `write_computed_field` callers or helper so provenance always includes:

```json
"warehouse": "warehouse/lahman.sqlite"
```

(relative to network root, matching manifest M2a.)

### 3 — Tests

- Deliver with `requested_attributes: ["debut_team", "debut_year"]` on baseball fixture → values match bind; provenance **not** research URL.
- Existing warehouse provenance tests assert `parameters.warehouse`.

### 4 — Smoke

Optional `smoke-baseball-e2e` row for bind attrs provenance shape.

---

## Non-goals

- All bio attrs from People (M2b)
- Research migration for supplemental web bio
- `TODO.md` edits

---

## Verification

```bash
./bin/ci-local
uv run pytest tests/test_baseball_batting_specialist.py tests/test_baseball_bio_specialist.py -q
```

---

## For Grok + Paul (output.md)

- M2c done; Paul re-run multi-attr hand-test with `provenance: true`.

**Suggested commit message:**

```
baseball: registry bind attrs on deliver + full warehouse parameters (M2c)
```