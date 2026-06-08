# Review: Demo slice 5 — polish (1150)

**Reviewer:** Grok  
**Date:** 2026-06-08  
**Verdict:** **Approved** — all polish items landed; green smoke; ready for hands-on test.

---

## Scope check

| Fix | Status |
|-----|--------|
| 1 — `network status --json` plain `print(json.dumps(...))` | ✅ |
| 2 — `test_status_cli_json` parses JSON + `NO_COLOR=1` | ✅ |
| 3 — Specialists empty-state copy + unit test | ✅ |
| 4 — `network_configure_hint` in `health_check` info | ✅ |
| 5 — `allow_no_default` only on `--no-default` + non-`crm` auto-default test | ✅ |
| 6 — Plan docs `refresh-example-network` | ✅ (no `copy-example-network` left in `docs/plans/`) |
| Slice 2 `review.md` issues marked fixed | ✅ |
| `TODO.md` slice 5 checked off | ✅ |

---

## Verification (Grok re-run)

```text
uv run pytest -m smoke -q  → 119 passed
uv run pytest -q            → 139 passed
uv run ruff check src tests bin/  → clean
uv run mycelium network status --network-dir examples/networks/crm --json | jq -r .seed_people_count  → 15
```

---

## Why so many files in `git status`?

The working tree is **cumulative** — slices 1, 1050, 2, and 5 are all uncommitted together (~21 paths). **This polish slice** only needed to touch ~10 files per `output.md`; the rest is earlier demo work still sitting locally. One commit (or stack) for the full demo phase 1–2+5 batch will look large; the 1150 diff itself is small and focused.

---

## What looks good

- **Plain JSON** fixes the smoke blocker and `jq` piping in one move — no Rich ANSI in stdout.
- **`allow_no_default = no_default`** (not `or not make_default`) with `test_refresh_non_crm_example_auto_defaults` — correct future-example semantics.
- **MCP** — instructions + health hint aligned with retired `data/` shim (includes 1050 items that were bundled in the same `server.py` diff).
- **Tests** — new coverage for configure hint, ontology empty copy, non-`crm` default; smoke suite fully green.

---

## Non-blocking nit

- **Specialists empty-state branch** (`elif summary.ontology_present and summary.categories`) is only hit when `specialists=[]`. In practice, `build_network_status()` builds specialists from ontology `assigned_agent`, so post-query CRM with `categories.json` shows six specialist rows with `records=0` rather than “none with storage yet.” The unit test uses a synthetic summary; real UX is still fine for demos. Optional follow-up: treat all-zero-record specialists as “no storage yet” in human formatter.

---

## Next step

**Hands-on test** (Paul + Grok):

```bash
./bin/refresh-example-network crm --yes
uv run mycelium network status --network crm
uv run mycelium query --person-key "Nichanan Kesonpat" --attributes email --thread-id demo-$(date +%s)
uv run mycelium network status --network crm --person "Nichanan Kesonpat"
```

Then slice 3 (admin daemon) when ready.