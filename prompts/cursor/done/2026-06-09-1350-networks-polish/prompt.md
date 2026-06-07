# Task: Networks polish — review niggles before integration testing

**Read these first (mandatory):**
- `prompts/cursor/WORKFLOW.md`
- `TODO.md` → **Networks polish** checklist
- `docs/plans/networks-terminology.md`
- Phase 1–4 done folders (especially Phase 2 path resolver, Phase 3 registry, Phase 4 CRM example)
- `src/network/paths.py`, `src/mycelium_mcp/server.py`, `src/main.py`

**Depends on:** Phase 4 (`2026-06-09-1300`) reviewed and approved (including runtime-artifact cleanup in example dir).

**Do not start** until Phase 4 is committed and in `prompts/cursor/done/`.

---

## Objective

Close **non-blocking review niggles** from Networks Phases 2–4 in one bounded slice so Phase 4.5 integration tests assert the final UX (especially `health_check` and MCP network metadata).

---

## Checklist (from `TODO.md` → Networks polish + Phase 4 review)

Implement all items; check them off in `output.md`:

### Phase 2–3 (carried forward)

1. **`health_check`** — expose `network_display_name` from `network.json` in `info` (use `network_display_name()` in `src/network/paths.py`).
2. **`health_check` error path** — `network_root` fallback via `framework_root() / "data"`, not cwd-relative `data/`.
3. **`.env.example`** — add `MYCELIUM_FRAMEWORK_ROOT` (network vars already partially documented).
4. **README MCP examples** — show `MYCELIUM_NETWORK` as alternative to full `MYCELIUM_NETWORK_ROOT` path.
5. **Legacy `mycelium seed`** — wire `_configure_network_paths` on `seed` **or** clarify deprecation in help text (smallest change that is honest).
6. **`docs/full-code-walkthrough.md`** — remove stale `core_data_agent` and `data/seed_crm.json` references; point at network root + example.
7. **README Status** — disambiguate “Phase 1 research” vs “Networks Phase N”.
8. **MCP instructions** — include resolved network name when registry / `network.json` provides it (may overlap with #1; keep instructions concise).

### Phase 4 review

9. **`examples/networks/crm/seed.json`** — sanitize public employer strings (e.g. strip internal CRM tags like `[Contacts Valuable][Funds dead]` from employer fields).
10. **`docs/plans/networks-terminology.md`** — update opening paragraph: CRM no longer embedded in repo root `data/` (Phase 4 complete).
11. **Bare `query` without bootstrap** — document (README or `data/README.md`) that legacy `data/` is empty on fresh clone until `copy-example-network`; optional smoke test for clear error when `seed.json` missing.

Add or extend smoke tests where behavior changes (#1, #2, #5, #11 if added).

---

## Scope boundaries

**May modify:** `src/mycelium_mcp/server.py`, `src/network/`, `src/main.py`, `README.md`, `.env.example`, `docs/`, `examples/networks/crm/seed.json` (employer sanitization only), `tests/`.

**Out of scope:** Phase 4.5 integration test suite (next slice), Phase 5 creation prompt, distributed discovery, re-adding runtime DB/checkpoint files to `examples/networks/crm/`.

---

## Verification

```bash
uv run pytest -m smoke -q
uv run ruff check src tests bin/
```

---

## Deliverables

`prompts/cursor/done/2026-06-09-1350-networks-polish/` with `prompt.md`, `output.md` (checklist with pass/fail per item).

**Next queue item:** `2026-06-09-1400-networks-integration-testing.md`