# Task: Demo slice 5 — polish (pre hands-on test)

**Read these first (mandatory):**
- `prompts/cursor/WORKFLOW.md` — claim by moving to `in-progress/` before starting
- `TODO.md` → Demo (phase) → Slice 5
- `prompts/cursor/done/2026-06-08-1100-demo-slice2-network-status/review.md`
- `prompts/cursor/done/2026-06-08-1050-demo-slice1-review-fixes/review.md` (non-blocking nits)
- `src/main.py` (network status + query JSON paths), `src/mycelium_mcp/server.py`, `tests/test_network_status.py`

**Depends on:** Demo slices 1–2 complete.

**Blocks:** Paul + Grok hands-on test (refresh → status → query → status); then slice 3.

---

## Workflow

1. Move this file to `prompts/cursor/in-progress/`.
2. Implement all fixes below.
3. Deliver `prompts/cursor/done/2026-06-08-1150-demo-slice5-polish/` with `prompt.md`, `output.md`.
4. Mark slice 5 items done in `TODO.md`.
5. Update open issues in slice 2 `review.md` (status → fixed).

---

## Objective

Clear all pending demo polish from slice 1–2 reviews before hands-on testing. **Priority:** `network status --json` must emit plain JSON for `jq`.

---

## Fixes (all required)

### 1. Plain JSON for `network status --json` (slice 2 blocker)

**File:** `src/main.py` — `network status` handler.

Replace Rich `console.print(JSON(...))` with plain stdout:

```python
print(json.dumps(status_to_dict(summary), indent=2))
```

- No ANSI, no soft-wrap — must pipe cleanly: `uv run mycelium network status --json | jq .seed_people_count`
- Human-readable path unchanged (`format_status_human` + `console.print`).

### 2. Fix `test_status_cli_json`

**File:** `tests/test_network_status.py`

After fix 1, assert by parsing JSON (not substring on raw stdout):

```python
payload = json.loads(result.stdout)
assert payload["seed_people_count"] == 15
```

Optional: keep `NO_COLOR=1` in subprocess env for consistency with other CLI tests.

### 3. Specialists empty-state copy (slice 2 nit)

**File:** `src/network/introspection.py` — `format_status_human`.

When `summary.specialists` is empty:
- If `summary.ontology_present` and categories exist → e.g. `Specialists: none with storage yet (ontology defines N categories)`
- Else → keep `Specialists: none registered`

Add or adjust a smoke test if straightforward.

### 4. `health_check` bootstrap hint (slice 1 / 1050 nit)

**File:** `src/mycelium_mcp/server.py` — `health_check` payload `info` dict.

Include `network_configure_hint` from `_network_health_info()` when present (unconfigured path). Update `test_network_health_info_unconfigured_hint` or `test_health_check_*` to assert hint appears in `health_check` JSON when unconfigured.

### 5. Refresh `allow_no_default` for future examples (slice 1 / 1050 nit)

**Files:** `src/network/example.py`, `src/network/registry.py`, tests.

Today `allow_no_default = no_default or not make_default` prevents first-registration auto-default for any non-`crm` example. Tighten:

- `allow_no_default=True` only when user passed `--no-default` (not whenever `make_default` is False).
- Non-`crm` first refresh without flags should still auto-default via `register_network` (existing `test_first_registration_becomes_default` behavior).
- `crm --no-default` on empty registry must still leave `default=False` (`test_refresh_crm_no_default_on_empty_registry` must pass).

### 6. Stale plan docs (slice 1 / 1050 nit)

One-line sweep only:
- `docs/plans/networks-terminology.md` — replace `copy-example-network` with `refresh-example-network` where still referenced (~11, ~301, ~324).
- `docs/plans/networks-phase5.md` — same for bootstrap mentions.

---

## Verification

```bash
uv run pytest -m smoke -q
uv run ruff check src tests bin/
uv run mycelium network status --network-dir examples/networks/crm --json | jq .seed_people_count
# expect: 15
```

Document counts in `output.md`.

---

## Scope boundaries

**May modify:** `src/main.py`, `src/network/introspection.py`, `src/network/example.py`, `src/network/registry.py`, `src/mycelium_mcp/server.py`, `tests/test_network_status.py`, `tests/test_network_polish.py`, `tests/test_example_network.py`, `docs/plans/networks-terminology.md`, `docs/plans/networks-phase5.md`, `TODO.md`, slice review.md status lines.

**Out of scope:** Slice 3 daemon, `query --json` Rich behavior (separate follow-up if desired).

---

## Deliverables

`prompts/cursor/done/2026-06-08-1150-demo-slice5-polish/` + green smoke suite.