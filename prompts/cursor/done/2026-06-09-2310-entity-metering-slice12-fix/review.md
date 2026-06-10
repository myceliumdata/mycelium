# Review — Entity metering Slice 12 fix (`2310`)

**Reviewer:** Grok (June 2026)  
**Verdict:** **Approve** — F1–F4 delivered; demo smoke verified; ready to commit with Slice 12.

---

## Summary

Fix slice closes all blocking and non-blocking nits from Slice 12 review. Demo script is reliable without caller env; admin docs steer operators to Vite dev stack; subprocess test guards regression.

---

## Checklist

| Fix | Verdict | Notes |
|-----|---------|-------|
| F1 Sync checkpointer in demo | Pass | `setdefault` in `_bootstrap()` before imports |
| F2 Admin demo docs | Pass | README + crm-metering README: `restart-admin crm-metering` default; `--demo` needs build |
| F3 Subprocess demo test | Pass | Explicitly clears caller `MYCELIUM_USE_SYNC_CHECKPOINTER`; asserts exit 0 + outcomes |
| F4 MCP queries README | Pass | 3-step table; placeholder `<quote_id-from-step-2>` |

**Bonus (in scope):** `admin-ui/dist/` added to `.gitignore` — sensible, aligns with dev-first admin path.

---

## Manual verification

```bash
unset MYCELIUM_USE_SYNC_CHECKPOINTER
./bin/refresh-example-network crm-metering --root /tmp/... --yes
./bin/demo-metering-negotiation --network-dir /tmp/...
→ exit 0, "Metering negotiation demo completed successfully."
```

---

## Tests

```
uv run pytest tests/test_cli_metering_query.py tests/test_entity_metering.py \
  tests/test_admin_daemon.py tests/test_example_network.py -q
→ 49 passed
```

Ruff clean on touched files.

---

## Nits

None blocking.

---

## Recommendation

Commit **Slice 12 + Slice 12 fix** together with unpushed Slice 11 (or as stacked commits). Suggested message from `output.md`:

```
Fix metering negotiation scaffolding nits (Slice 12 fix).

Sync checkpointer in demo script; restart-admin as default admin path;
subprocess demo test; MCP queries README.
```

Mark Slice 12 and Slice 12 fix done in `TODO.md`.