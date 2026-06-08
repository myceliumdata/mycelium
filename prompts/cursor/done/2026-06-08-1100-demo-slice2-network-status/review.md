# Review: Demo slice 2 — `mycelium network status`

**Reviewer:** Grok  
**Date:** 2026-06-08  
**Verdict:** **Approved** — polish `1150` fixed JSON/test issues; ready for hands-on test.

---

## Scope check

| Requirement | Status |
|-------------|--------|
| `mycelium network status` subcommand | ✅ |
| Shared `src/network/introspection.py` (CLI + future daemon) | ✅ |
| Read-only — no `run_query`, no graph | ✅ |
| `--network-dir`, `--network`, `--json`, `--category`, `--person` | ✅ |
| Seed count, ontology, specialists, storage stats | ✅ |
| Human-readable demo output | ✅ |
| Tests: empty, populated, JSON, person drill-down | ✅ (see CLI test bug) |
| README + CRM README | ✅ |
| `TODO.md` slice 2 done | ✅ |

---

## Verification (Grok re-run)

```text
uv run pytest -m smoke -q tests/test_network_status.py  → 3 passed, 1 FAILED (test_status_cli_json)
uv run pytest -m smoke -q                               → 115 passed, 1 FAILED
uv run ruff check src/network/introspection.py src/main.py tests/test_network_status.py  → clean
uv run mycelium network status --network-dir examples/networks/crm  → OK (human)
uv run mycelium network status --network-dir examples/networks/crm --json  → OK (content correct)
```

`output.md` claims 116 smoke passed — **not reproducible** until `test_status_cli_json` is fixed.

---

## What looks good

- **`introspection.py`** is a clean, shared read model: dataclasses, `build_network_status()`, human + dict formatters — ready for slice 3 HTTP binding.
- **Direct JSON reads** for registry/storage instead of `SpecialistStorage` — avoids `_ensure_initialized()` mkdir/write side effects on status-only inspection. Reasonable trade-off; prompt allowed “beyond what SpecialistStorage already does on init” and read-only intent is preserved.
- **Agent map** merges registry + ontology `assigned_agent` — populated fixture correctly shows 6 category specialists with contact storage stats.
- **`--person` drill-down** resolves seed id via `find_by_key`, per-field status — good demo story.
- **CLI wiring** uses `_configure_network_paths()` before introspection, same as `query`.
- **Module exports** in `network/__init__.py` for daemon reuse.

---

## Issues

### Issue 1 — Severity: bug
- File: `tests/test_network_status.py:167`
- Description: `test_status_cli_json` fails: subprocess stdout includes Rich ANSI markup (`\x1b[1m...`) from `console.print(JSON(...))`, so `'"seed_people_count": 15' in result.stdout` is false even though returncode is 0.
- Suggestion: Set `NO_COLOR=1` / `FORCE_COLOR=0` in subprocess env (pattern from `test_network_integration.py`); strip ANSI before assert; or assert on parsed JSON after stripping. Alternatively, print plain `json.dumps(...)` to stdout for `--json` (no Rich wrapper) — better for scripting/`jq`.
- Status: **fixed** (1150)

### Issue 2 — Severity: suggestion
- File: `src/main.py:312-313`
- Description: `--json` routes through Rich `JSON()` renderer — soft-wraps long paths and adds terminal markup; awkward for `jq` and CI piping.
- Suggestion: For `args.json`, use `print(json.dumps(status_to_dict(summary), indent=2))` (or `console.print` without Rich JSON). Match `query` behavior only if query has the same limitation; status is more likely to be piped.
- Status: **fixed** (1150)

### Issue 3 — Severity: nit
- File: `src/network/introspection.py:377-378`
- Description: “Specialists: none registered” when seed-only — technically ontology-derived agents are also absent; message is fine for demos but slightly imprecise when `categories.json` exists without `agent_registry.json`.
- Suggestion: Optional follow-up copy tweak in slice 5 polish; not blocking.
- Status: **fixed** (1150)

---

## Next step

1. Fix **Issue 1** (and preferably Issue 2) — re-run `uv run pytest -m smoke -q` → expect 117 passed (116 + full person test still deselected in smoke... actually 4 status smoke + rest = 116 total if 112 was before slice 2 added 4 tests = 116, one fails = 115).
2. **Hands-on test with Paul** — refresh CRM → `network status` → query → `network status --person "Nichanan Kesonpat"`.
3. Proceed to slice 3 after fix + quick manual pass.