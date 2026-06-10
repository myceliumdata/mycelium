# Task: Identity vocabulary rename (breaking)

> **READY** — Paul approved breaking change (June 2026). Move to `in-progress/` before starting.

**Read first:**

- [`docs/plans/entity-identity-vocabulary-rename.md`](../../docs/plans/entity-identity-vocabulary-rename.md)
- [`docs/architecture.md`](../../docs/architecture.md)
- [`docs/plans/historical-assumptions-audit.md`](../../docs/plans/historical-assumptions-audit.md) §6

**Depends on:** Seed elimination complete (main green).

---

## Objective

Rename seed-era graph/MCP vocabulary to registry identity terms. **Breaking change is intentional** — no backward-compat aliases.

---

## Rename map (mandatory)

| Old | New |
|-----|-----|
| `SeedRecord` | `IdentityRecord` |
| `seed_record` | `identity_record` |
| `seed_records` | `identity_records` |
| MCP `mycelium://schema/seed-record` | `mycelium://schema/identity-record` |
| `context` dict key `'seed'` | `'identity'` |
| Functions/vars `_seed_records_from_match`, `_rows_to_seed_records`, etc. | `_identity_*` |

Update **all** docstrings that still say “seed match” or “seed identity” in `src/models/state.py`, `routing.py`, `responses.py`, `supervisor.py`, `storage/core.py` if touched.

**Keep unchanged:** `seed.json`, `--seed`, `import_seed_file`, bootstrap fixture wording in CLI help.

**Do not rename** `RegistryEntity` (`entity_registry.py`).

---

## State consolidation

`MyceliumGraphState` has `matched_records` (dicts) **and** typed `seed_records`. After rename:

1. Audit all readers of `seed_records` / `identity_records`.
2. **Prefer canonical `matched_records`** for graph flow (supervisor, dispatch, gates, specialists).
3. Remove redundant typed list from supervisor return payload **if** nothing needs Pydantic typing in graph state.
4. If Studio needs typed list, keep `identity_records` but document single source: populate from same rows as `matched_records`.

Document choice in `output.md`.

---

## Files (expected touch)

- `src/models/state.py`, `src/models/__init__.py`
- `src/agents/supervisor.py`, `routing.py`, `dispatch.py`, `responses.py`
- `src/agents/context.py` (identity key in context dict)
- `src/mycelium_mcp/server.py` (schema resource)
- `src/graphs/core.py`, `src/storage/core.py` if referenced
- `src/agents/factory/templates/specialist_agent.py.j2`
- Tests: grep `SeedRecord|seed_record` under `tests/`
- Docs: `docs/full-code-walkthrough.md`, `docs/architecture.md` (type names only; brief)

**Out of scope:** `docs/plans/*` historical slice specs, `prompts/cursor/done/*`, `TODO.md`, `admin-ui/` (unless types import SeedRecord — grep first).

---

## Governance

- Do **not** edit `TODO.md`.
- Do **not** create `review.md`.
- `output.md` → **For Grok + Paul**: note breaking MCP URI; old checkpoints may need fresh `thread_id`.

---

## Verify

```bash
uv run ruff check src tests
rg 'SeedRecord|seed_records|seed_record|schema/seed-record' src/ tests/
LANGCHAIN_TRACING_V2=false uv run pytest -q
```

Report full pytest count in `output.md`.

---

## Suggested commit message

```
Breaking: rename SeedRecord to IdentityRecord and seed_* state fields.

Registry identity vocabulary; MCP schema identity-record; consolidate
matched_records where possible.
```
