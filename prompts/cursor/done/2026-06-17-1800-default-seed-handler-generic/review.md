# Review — 2026-06-17-1800-default-seed-handler-generic

**Verdict: Approved + polish nits** — land with small doc delta; **no re-scope or re-do** of core work.

**Reviewer:** Grok  
**Date:** 2026-06-17 (review run on uncommitted WIP + committed `main` through 2100)

---

## Context

Cursor finished this slice **June 17 ~11:24** (`output.md` timestamp). It was **never reviewed or committed** while baseball identity slices 1900 → 2000 → 2100 proceeded. Implementation lives in the **working tree** (not on `main`).

This review asks: is 1800 still valid after later work, or obsolete?

**Answer:** The **`rows[]` + `bootstrap.seed_grain` + `resolve_bootstrap_grain()`** design is **still correct and needed**. Slices 1900–2100 did not replace it. Later slices **depend** on it indirectly (`docs/query-grain-router.md` links `seed-bootstrap.md`; polish P6/P9 track the missing commit).

---

## CI

| Step | Result (WIP = 1800 + committed 2100) |
|------|--------------------------------------|
| `./bin/ci-local` | **Pass** — **493** smoke, 100 deselected |
| `./bin/smoke-crm-e2e` | **Pass** — 7 scenarios, 15 seed_bootstrap rows |
| ruff | clean |

`output.md` claimed 478 smoke (June 17); count grew with later committed tests — not a 1800 defect.

---

## Delivery vs `output.md`

| Claim | Actual |
|-------|--------|
| `load_seed_rows`, `rows[]`, `seed_grain` | ✅ In WIP `default_seed.py`, `config.py`, `seed_import.py`, `create.py` |
| CRM `seed.json` → `rows` | ✅ WIP |
| `docs/seed-bootstrap.md` new | ✅ Present (untracked); content is **stronger** than prompt minimum (includes source_keys + `identity_mode` from 1900/2000 — good consolidation) |
| `docs/architecture.md` seed section updated | ❌ **Not in WIP** — committed file still says `people` / `people[]` in § Seed bootstrap |
| `introspection.py` `rows[]` copy | ❌ **Not in WIP** — `_POLICY_REGISTRY` still says `seed people[]` |
| `main.py` help text | ✅ WIP |
| `onboarding.md` | ✅ WIP |
| Tests migrated | ✅ WIP — no `"people"` in test seed JSON; `test_bootstrap_seed_grain_*` added |
| `load_seed_people` / `resolve_seed_grain` removed | ✅ WIP — replaced by `load_seed_rows` / `resolve_bootstrap_grain` |

---

## Compatibility with later slices (1900 / 2000 / 2100)

| Later slice | Overlap with 1800 | Conflict? |
|-------------|-------------------|-----------|
| **1900** source_keys / field aliases | `seed-bootstrap.md` § source_keys documents registry keys | **No** — doc enrichment, not handler change |
| **2000** closed identity / lazy aliases | `seed-bootstrap.md` § `identity_mode` | **No** — orthogonal to seed file shape |
| **2100** query grain router | `architecture.md` runtime-store fan-out line (committed) | **Merge only** — 1800 must update **seed** bullets without reverting 2100 **resolve** bullet |
| **Multi-mvr (1400)** | Removed `resolve_seed_grain()` | **Intentional** — 1800 supersedes 1400 grain preference with manifest-driven `seed_grain` |

**Nothing in 1900–2100 makes `rows[]` or `bootstrap.seed_grain` obsolete.** Committed `main` still uses `people[]` in code and CRM seed — that is **technical debt**, not a reason to abandon 1800.

---

## Diff reviewed (WIP vs `HEAD`)

| File | Assessment |
|------|------------|
| `src/network/bootstrap/config.py` | `BootstrapConfig.seed_grain`, `resolve_bootstrap_grain()` — clean |
| `src/network/bootstrap/handlers/default_seed.py` | `load_seed_rows`, paths/grain inference on `import_seed_rows` — matches spec |
| `src/network/seed_import.py` | `__all__`, structural `count_seed_rows`, drops `_load_seed_people` shim — good |
| `src/network/create.py` | Structural `rows[]` validation only (no hardcoded `name`) — matches S7 |
| `examples/networks/crm/` | `rows`, optional `seed_grain: person` — good |
| `examples/networks/crm-metering/seed.json` | `rows` — good |
| `tests/test_network_bootstrap.py` | New grain tests + renames — good |
| Other test fixture tweaks | Mechanical `rows` / `import_seed_file` paths — good |
| `docs/seed-bootstrap.md` | Canonical doc; exceeds prompt outline |
| `docs/architecture.md` | **Unchanged** — gap |
| `src/network/introspection.py` | **Unchanged** — gap |

---

## Spec compliance

| # | Criterion | Result |
|---|-----------|--------|
| E1 | No `load_seed_people` / `people[]` in `default_seed.py`, `src/`, `tests/` seed fixtures | **Pass** (WIP) |
| E2 | CRM `seed.json` uses `rows`; bootstrap imports 15 entities | **Pass** (smoke-crm-e2e) |
| E3 | `docs/seed-bootstrap.md` — three bootstrap types | **Pass** |
| E4 | `bootstrap.seed_grain` honored; default when omitted | **Pass** (`test_bootstrap_seed_grain_*`) |
| E5 | `./bin/ci-local` green | **Pass** |
| E6 | Breaking changes documented | **Pass** (`output.md`) |
| S11 | `architecture.md` cross-link | **Fail** — not in WIP |
| S12 | `introspection.py` copy | **Fail** — not in WIP |

---

## Design critique

**Strong**

- Manifest-driven bootstrap grain (`seed_grain` → `default_grain`) removes CRM-shaped `resolve_seed_grain()` / `"person"` hack — correct for multi-grain baseball + generic frameworks.
- `import_seed_rows` paths inference from `MYCELIUM_NETWORK_ROOT` or `seed_path.parent` keeps `network_helpers.import_seed_for_test` working without API churn.
- Structural vs full validation split (`create.py` vs `load_seed_rows`) matches locked S7.
- `count_seed_rows` structural parse avoids needing MVR context — sensible for dry-run counts.

**Sub-optimal (non-blocking)**

- `output.md` over-claims `architecture.md` and `introspection.py` updates — Cursor marked slice done prematurely on docs.
- `prepare_seed.py` still reads upstream CSV JSON key `people` — **intentional** (maintainer source format); document in commit message.
- `seed-bootstrap.md` is untracked — breaks `query-grain-router.md` link on clean `main` until 1800 lands.

**Re-do?** **No.** A full re-scope would only be needed if we abandoned `rows[]` or manifest `seed_grain`. Neither applies.

---

## Nits (complete at commit time)

| ID | Item |
|----|------|
| N1 | **`docs/architecture.md` § Seed bootstrap** — replace `people` / `people[]` bullets with `rows[]` + link to `seed-bootstrap.md`; **preserve** 2100 runtime-store fan-out sentence |
| N2 | **`src/network/introspection.py`** — `_POLICY_REGISTRY`: `seed rows[]` not `people[]` |
| N3 | Commit **`docs/seed-bootstrap.md`** with 1800 (already written; includes 1900/2000 sections — keep) |
| N4 | Mark TODO **“Non-person seed schemas”** done after commit (Grok + Paul) |

Polish slice **P6** (seed-bootstrap identity section) largely satisfied by current `seed-bootstrap.md` — can close P6 when 1800 commits.

---

## For Paul

1. **Verdict:** Approved — commit 1800 WIP as one slice; add N1–N2 in same commit (5-minute doc touch).
2. **Suggested commit message** (from prompt, still accurate):

   ```
   refactor(bootstrap): generic DefaultSeedHandler rows[] and seed doc

   Replace people[] with rows[]; bootstrap grain from manifest seed_grain
   or default_grain; add docs/seed-bootstrap.md for three bootstrap patterns.
   ```

3. **Order:** Land **1800 before polish** (or as first commit in polish session) so `seed-bootstrap.md` exists on `main` and P9 link fix is trivial.
4. **Do not** revert 2100 `architecture.md` fan-out line when editing N1.

---

## How we missed this (process)

| Factor | Detail |
|--------|--------|
| Name collision | `1800-specialist-agent-class` was reviewed; `1800-default-seed-handler-generic` was not |
| Queue focus | 1900/2000/2100 baseball program absorbed review bandwidth |
| WIP treatment | 2000/2100 reviews said “don’t mix 1800 hunks” but never scheduled 1800 review |
| Cursor `output.md` | Declared complete + empty `next/` — Grok review gate not invoked before moving on |