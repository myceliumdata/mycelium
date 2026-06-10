# Review — Seed elimination Slice 17 (delete runtime seed module)

**Reviewer:** Grok (June 2026)  
**Verdict:** **Approve** — `agents.seed` gone; test sweep complete; full smoke green.

---

## Summary

Slice 17 deletes `src/agents/seed.py`, removes the legacy `mycelium seed` CLI, updates `storage/core.py` docstring, and migrates 20+ test files to `import_seed_for_test` / `reset_entity_registry`. Fixes Slice 16 carry-over (`test_mcp_query_entity_round_trip_json`). No `agents.seed` references remain in `src/` or `tests/`.

---

## Checklist

| Item | Verdict | Notes |
|------|---------|-------|
| Delete `agents/seed.py` | Pass | Module removed |
| `mycelium seed` CLI | Pass | Parser + handler removed from `main.py` |
| `storage/core.py` | Pass | Docstring: identity via `entities.json` / `import_seed_file` |
| `network_helpers` | Pass | Enhanced `import_seed_for_test`; `import_seed_at_root` retained |
| `conftest.py` | Pass | Session cleanup uses `reset_entity_registry` |
| Test sweep | Pass | No `agents.seed` / `get_seed_data` / `reset_seed_data` in `tests/` |
| `test_entity_rename.py` | Pass | MCP round-trip imports seed into registry |
| `test_network_polish.py` | Pass | Missing seed → `import_seed_file` returns `0` |
| Scope boundaries | Pass | No admin UI / README edits (Slice 18) |
| Governance | Pass | No `review.md` from Cursor; no `TODO.md` edits |
| **Full smoke** | Pass | **271 passed**, 26 deselected |

---

## Tests (re-verified)

```bash
rg 'agents\.seed|get_seed_data|reset_seed_data' src/ tests/
→ no matches

uv run ruff check src tests
→ All checks passed

uv run pytest -m smoke -q
→ 271 passed, 26 deselected
```

---

## Nits (non-blocking — Slice 18)

| Item | Notes |
|------|-------|
| CLI help strings in `main.py` | Still say "seed record" in places — polish in Slice 18 |
| `docs/architecture.md` etc. | Stale `agents.seed` references noted in `output.md` — Slice 18 |

---

## Recommendation

Commit Slice 17. Mark done in `TODO.md`. Proceed to **Slice 18** (admin UI, docs, phase exit / full pytest).

Suggested commit message (from `output.md`):

```
Delete runtime seed module and legacy seed CLI (Slice 17).

Remove agents.seed; tests bootstrap via import_seed_for_test;
mycelium seed subcommand removed; smoke 271 green.
```