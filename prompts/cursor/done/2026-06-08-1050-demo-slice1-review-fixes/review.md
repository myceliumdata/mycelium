# Review: Demo slice 1 — review fixes (1050)

**Reviewer:** Grok  
**Date:** 2026-06-08  
**Verdict:** **Approved** — all slice 1 review issues resolved; slice 2 unblocked.

---

## Scope check

| Fix | Status |
|-----|--------|
| 1 — dry-run early-return before confirmation | ✅ |
| 2 — `test_refresh_dry_run_without_yes_leaves_root_unchanged` | ✅ |
| 3 — MCP instructions (no legacy `data/`) | ✅ |
| 4 — MCP health unconfigured hint (`network_root: null`) | ✅ |
| 5 — `allow_no_default` + `test_refresh_crm_no_default_on_empty_registry` | ✅ |
| 6 — TODO hands-on line | ✅ |
| 7 — slice 1 `output.md` dry-run note | ✅ |
| 8 — `networks-terminology.md` line ~11 | ✅ |
| 9 — `.gitignore` top-level `data/` | ✅ |

---

## Verification (re-run by Grok)

```text
uv run pytest -m smoke -q  → 112 passed
uv run pytest -q            → 131 passed
uv run ruff check src tests bin/  → clean
test ! -f bin/copy-example-network  → OK
./bin/refresh-example-network crm --dry-run  → exit 0 (no --yes, live root exists)
```

Slice 1 checklist also re-verified as part of this run.

---

## What looks good

- **Dry-run fix** is the right shape — early return at line 138, confirmation only for real writes.
- **`allow_no_default`** preserves `test_first_registration_becomes_default` for plain `register_network("solo", root)` while `crm --no-default` correctly leaves `default=False`.
- **MCP health** no longer misreports `<framework>/data`; test renamed and asserts hint text.
- **Two new smoke tests** close the gaps the slice 1 review identified.

---

## Non-blocking nits (no action required before slice 2)

1. **`health_check` JSON** does not surface `network_configure_hint` from `_network_health_info()` — only `network_root: null`. Fine for now; add to payload if MCP clients need the bootstrap pointer in health responses.
2. **`allow_no_default = no_default or not make_default`** — for a future non-`crm` example, first refresh would not auto-default (only `crm` gets auto-default today). Acceptable until a second example ships.

---

## Next step

Proceed to **`2026-06-08-1100-demo-slice2-network-status`**.