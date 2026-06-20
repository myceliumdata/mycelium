# Review — CLI step-2 `delivery_id` network hints (A + B)

**Verdict:** **Approved**

**CI:** `./bin/ci-local` — **605** smoke passed, ruff clean, admin-ui build ok (Grok, 2026-06-20).  
**Slice pytest:** `tests/test_delivery_network_hints.py` — **5** passed.

---

## Delivery

| Check | Result |
|-------|--------|
| `output.md` matches implementation | Pass |
| Prompt in `done/` | Pass — `prompt.md` + `output.md` |
| Scope creep in slice files | Pass — MCP, `state.py`, gate catalogs untouched |
| `TODO.md` untouched | Pass |

**Working-tree note:** Uncommitted changes also include **unrelated** live-gate WIP (`bin/gate-live`, `tests/live/*`, broader `docs/manual-checks/…` auto-refresh edits). Those are **not** part of this slice — do not one-shot commit the full tree.

---

## Spec compliance

| # | Requirement | Result |
|---|-------------|--------|
| **A** | Step-1 stderr hint with `--network` / `--network-dir`, `delivery_id`, optional `--quote-id` | Pass — `src/main.py` after `lookup_resolved` / `quote_required` |
| **B** | Cross-network deliver miss message | Pass — `find_delivery_on_other_network` + retry line |
| **B** | Expired on active network | Pass — distinct wording before cross-network scan |
| **B** | Fallback when unknown | Pass |
| **B** | Wired at deliver `not_found` only | Pass — both `dispatch.py` paths |
| **B** | No auto-switch network | Pass — instruct only |
| Tests | 4+ smoke cases | Pass — 5 tests |
| README | Step 2 shows `--network` | Pass |
| Live-gate doc footnote | Partial — CLI note line present in working tree, but file also has out-of-scope auto-refresh edits (see nits) |
| No MCP / schema changes | Pass |

---

## Diff reviewed

| File | Grok read |
|------|-----------|
| `src/network/delivery_hints.py` | Full file |
| `src/main.py` | Hint block (~553–568) |
| `src/agents/dispatch.py` | Deliver not_found message wiring |
| `tests/test_delivery_network_hints.py` | Full file |
| `README.md` | CLI two-step sections |
| `prompts/cursor/done/2026-06-20-2000-cli-delivery-id-network-hints/output.md` | Claims vs diff |

`/review` subagent: not used (focused UX slice).

---

## Design critique

**Strong**

- Pure helpers in `delivery_hints.py` — testable without full graph; registry-bounded scan matches spec.
- Exactly-one-other-network rule avoids ambiguous hints when multiple roots match.
- Expired-on-active checked before cross-network (correct priority).
- stdout JSON unchanged; hint on stderr only.
- `_network_selector` falls back to `--network-dir` when no registered name — matches prompt.

**Acceptable**

- Hydration `ValueError` path reuses `delivery_not_found_message` — may be generic if hydration fails for non-network reasons; still better than old one-liner and rare.

---

## Nits

| # | Severity | Item |
|---|----------|------|
| N1 | Non-blocking | `docs/manual-checks/2026-06-20-live-gate-program.md` in working tree mixes this slice’s CLI footnote with auto-refresh gate doc — land footnote with this commit or split when gate WIP commits |
| N2 | Non-blocking | Cursor ran slice `2000` before queued `1995` (fresh-derive default) — `1995` still in `next/`; no action on this review |

---

## Commit hygiene

**This slice only:**

- `src/network/delivery_hints.py`
- `src/main.py`
- `src/agents/dispatch.py`
- `tests/test_delivery_network_hints.py`
- `README.md`
- `prompts/cursor/done/2026-06-20-2000-cli-delivery-id-network-hints/`

**Exclude** (separate commits): `bin/gate-live`, `tests/live/*`, `crm_metering.yaml`, example READMEs, full manual-checks auto-refresh block.

---

## For Paul

- **Commit message:** `feat(cli): delivery_id network hints for two-step queries`
- **Manual check:** step 1 `--network baseball`, step 2 omit `--network` on default CRM → B message names baseball; stderr hint after step 1.
- **Next slice:** `prompts/cursor/next/2026-06-20-1995-baseball-fresh-derive-default-on.md` (still queued).
- **Push:** local only until you ask.