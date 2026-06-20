# Baseball live gate — default `--fresh-derive` when derive runs

> **READY** — Claim per `prompts/cursor/WORKFLOW.md`.

**Objective:** Stop requiring operators to remember `--fresh-derive` for baseball derive gates. Mirror the `refresh_before_gate` / `--no-refresh` pattern: **default on** when derive phase runs; explicit opt-out.

**Context (Paul + Grok, June 2026):** `--fresh-derive` clears `agents/batting/storage.json` and `intent_map.json` before derive scenarios. Docs say to use it, but the CLI leaves it optional. That caused confusion after the warm-cache fix — operators shouldn't need a mental flag for normal derive regression.

**Design lock:**

| Item | Decision |
|------|----------|
| Default | Clear derive cache when baseball gate includes **derive** phase (all phases or `--phase derive`) |
| Registry | `fresh_derive_before_gate: true` on `baseball` in `tests/live/networks.yaml` |
| Opt-out | `--no-fresh-derive` (parallel to `--no-refresh`) |
| `--fresh-derive` | Keep as **force-on** override (no-op when already default; useful if registry default ever changes) |
| Scope | Only when `derive` ∈ phases (or full run = all phases). **No** clear on `--phase m2` only |
| In-run state | Unchanged — clear happens **once before** pytest; `bb-derive-01` → `03` accumulation still intentional |
| Other networks | Unaffected |

**Do not edit `TODO.md`.**

Read for context: `docs/manual-checks/2026-06-20-live-gate-program.md`, `bin/gate-live`, `tests/live/gate_runner.py`.

---

## Scope (strict)

You may modify only:

- `bin/gate-live`
- `tests/live/networks.yaml`
- `tests/live/gate_runner.py` (registry field on `NetworkEntry` + loader only)
- `tests/test_live_gate_runner_unit.py`
- `docs/manual-checks/2026-06-20-live-gate-program.md`

Do **not** change scenario catalogs, baseball specialists, or CI wiring.

---

## Implementation

### 1 — Registry (`tests/live/networks.yaml`)

Under `baseball:` add:

```yaml
fresh_derive_before_gate: true
```

Other networks omit or `false`.

### 2 — `NetworkEntry` (`gate_runner.py`)

Add field:

```python
fresh_derive_before_gate: bool = False
```

Load from YAML: `bool(cfg.get("fresh_derive_before_gate", False))`.

### 3 — CLI logic (`bin/gate-live`)

Add helper (name flexible):

```python
def _should_fresh_derive(
    *,
    network: str,
    entry: NetworkEntry,
    phases: set[str] | None,
    fresh_derive_flag: bool,
    no_fresh_derive: bool,
) -> bool:
    ...
```

Rules:

1. `network != "baseball"` → `False`
2. `no_fresh_derive` → `False`
3. Derive not in scope → `False` (`phases is None` means all phases → derive in scope; else require `"derive" in phases`)
4. `entry.fresh_derive_before_gate or fresh_derive_flag` → `True`

Replace current `if args.fresh_derive and network == "baseball":` block with `_should_fresh_derive(...)`.

**stderr messaging** (when cache cleared, not `--json`):

```text
Clearing baseball derive cache: agents/batting/storage.json, intent_map.json
```

If auto (registry default, no `--fresh-derive` flag), append hint:

```text
  (fresh_derive_before_gate; pass --no-fresh-derive to keep existing cache)
```

**Optional but encouraged:** when derive in scope, cache files exist, and `--no-fresh-derive` → print one-line **warning** to stderr that stale derive cache may cause false failures.

### 4 — argparse

```python
parser.add_argument(
    "--no-fresh-derive",
    action="store_true",
    help="Baseball only: skip clearing batting storage + intent_map before derive phase",
)
```

Update `--fresh-derive` help text: "Force clear … (default when fresh_derive_before_gate and derive phase runs)".

### 5 — `--list` output

After `refresh_before_gate`, print:

```text
fresh_derive_before_gate: yes|no
```

for each network.

### 6 — Env var `LIVE_GATE_FRESH_DERIVE`

Set when `_should_fresh_derive` is true (not only when explicit flag). Unset otherwise. Keeps bootstrap contract from slice `2026-06-20-1600`.

---

## Tests (`test_live_gate_runner_unit.py`)

Add smoke tests:

| Test | Assert |
|------|--------|
| `test_baseball_fresh_derive_before_gate_flag` | `registry["baseball"].fresh_derive_before_gate is True`; CRM networks `False` |
| `test_should_fresh_derive_*` | Unit-test helper logic: all phases → true; `--phase m2` only → false; `--no-fresh-derive` → false; non-baseball → false |

Prefer testing extracted helper in `gate_runner.py` (importable from unit tests) over subprocess CLI if cleaner.

---

## Docs (`docs/manual-checks/2026-06-20-live-gate-program.md`)

Update Quick start:

```bash
./bin/gate-live baseball --phase derive          # auto-clears derive cache
./bin/gate-live baseball --phase derive --no-fresh-derive   # keep cache
```

Remove wording that implies operators must always pass `--fresh-derive`. Explain default + opt-out in Baseball section (replace current single-line "Use `--fresh-derive`…").

---

## Verification

```bash
./bin/ci-local
uv run pytest tests/test_live_gate_runner_unit.py -q
./bin/gate-live --list   # shows fresh_derive_before_gate for baseball
```

Live gate re-run optional in `output.md` (no API required for slice completion).

---

## Exit criteria

- [ ] Baseball derive gate clears cache by default; `--no-fresh-derive` skips
- [ ] Non-derive baseball phases do not clear cache
- [ ] `--list` shows registry flag
- [ ] Unit tests cover helper + registry
- [ ] Manual gate doc updated
- [ ] `./bin/ci-local` green

---

## Governance (mandatory)

- **Do not edit `TODO.md`.**
- In `output.md`, **"For Grok + Paul"**: note operator UX change; no roadmap edits needed.
- Cursor delivers: code, tests, doc, `output.md` only.

## When finished (mandatory — see WORKFLOW.md §3)

1. `./bin/ci-local` green
2. `prompts/cursor/done/2026-06-20-1995-baseball-fresh-derive-default-on/` with `prompt.md` + `output.md`
3. Remove claimed file from `in-progress/` and `next/`
4. **Do not commit or push** — tell Paul "slice ready for review"

---

## Suggested commit message

```
feat(gate-live): default fresh-derive for baseball derive phase
```