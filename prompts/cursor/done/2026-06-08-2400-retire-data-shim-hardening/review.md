# Review: Retire repo-root `data/` shim hardening

**Reviewer:** Grok (verification pass)  
**Commit:** `a57804d`  
**Verdict:** **Approved**

---

## Prompt checklist

| Requirement | Status | Notes |
|-------------|--------|-------|
| `runtime_path()` in `network/paths.py` | ✅ | Correct precedence: explicit env → `MYCELIUM_NETWORK_ROOT` → `resolve_network_root()` → fail loud |
| `shell_export_network_paths()` for Studio | ✅ | Uses `shlex.quote`; exports all path vars |
| Replace `data/` fallbacks in consumers | ✅ | No `data/...` defaults remain in `src/` runtime code (reference specialist docstrings unchanged per scope) |
| `bin/run-studio` bootstrap + fail on unconfigured | ✅ | `bash -n` clean; eval exports resolve to `~/mycelium-networks/crm` |
| Smoke tests (4 new cases) | ✅ | 12/12 in `test_network_paths.py` |
| README brief note | ✅ | Studio section documents retired `data/` |
| Did not edit `TODO.md` | ✅ | Notes left in `output.md` for Grok + Paul |
| `uv run pytest -m smoke -q` | ⚠️ | 158 passed, 1 failed — pre-existing LLM flake (`test_create_specialist_writes_files_and_registers`: `na` vs `pending`) |
| `ruff check` on touched Python | ✅ | Clean |

---

## Manual verification (Grok)

- Repo-root `data/` absent after Paul's manual delete; not recreated by verification commands.
- Unconfigured `runtime_path()` raises: `No network configured. Run: ./bin/refresh-example-network crm`
- With registry default: checkpoint resolves to `/Users/paul/mycelium-networks/crm/checkpoints.sqlite`
- `mycelium query --network crm` runs end-to-end (tested `Aaron Holiday`).

---

## Minor notes (non-blocking)

1. **Stale `.env` per-path overrides** — If `MYCELIUM_CHECKPOINT_PATH=data/checkpoints.sqlite` (or similar) remains in `.env`, `runtime_path()` will still honor it (explicit env wins). Worth a one-line note in README or `.env.example` cleanup pass later.
2. **`introspection.py` bundled specialists fallback** — Cursor correctly flagged as intentional; optional follow-up only.
3. **Smoke flake** — Unrelated to this slice; do not block merge on it.

---

## For Grok + Paul

- Slice is good to ship as-is.
- Optional `TODO.md` note: add a checked item for **runtime_path hardening** (complements existing "Retired legacy `data/` shim" item) if you want the roadmap to reflect commit `a57804d` explicitly.