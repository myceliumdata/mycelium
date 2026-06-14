# Manual checks — Program 2 post-program gate (MVR / entity storage)

**Status:** ⏳ **PENDING** — run this checklist from scratch; mark **CLEAR** when all required checks pass.

**Context:** Program 2 (Slices 1–3 + polish P1–P7 + remedial fixes + capstone tests) is **committed locally** on `main` — **14 commits ahead of `origin/main`**. This gate validates hands-on behavior before **pushing** to `origin/main`.

**What Program 2 proves:**

- MVR bind fields (`name`, `employer`) live in **taxonomy-owned specialist `versions[]`**, not entity-level history
- Unified write on seed import, registry bind, and create-on-deliver
- Read surfaces: `provenance=true`, CLI/admin `entity_fields[].versions[]` for bind fields
- Research operator deference (prompt) + polish fixes (ordering, no-op skip, rollback, empty employer row)

**Prereqs:** Framework repo root; `uv sync` done. Live roots under `~/mycelium-networks/` (never test in-place under `examples/networks/…`). Optional checks 8–10 need API keys in `.env`.

**Estimated time:** ~60–75 min (required checks 0–7 + **4b**); optional 8–10 add ~20 min.

---

## Regressions fixed before this gate (know what you are validating)

These bugs slipped past smoke CI until June 2026 remedial work. The checklist below is designed to catch them again.

| Issue | Symptom | Fix / guard |
|-------|---------|-------------|
| **Committed runtime in example tree** | `refresh` copied `examples/networks/crm/entities.json` → seed import saw duplicates → **Entities ✅ but specialists ❌** | Example tree must ship **reference files only** (`seed.json`, `network.json`, `guide.md`, README). Layout tests fail if `entities.json`, `deliveries.json`, or `agents/` exist under `examples/networks/`. **Not gitignored** — stray files show in `git status`. |
| **Seed refresh specialist storage** | Same as above on crm refresh | `refresh` skips copying `entities.json`; seed bootstrap backfills demographic + professional storage with `seed_bootstrap` versions. |
| **empty-crm step 2 MVR bootstrap** | Step 1 OK; step 2 → `not_found` / **"No valid delivery"** (misleading — real error was missing `attribute_map` for `name`/`employer`) | `target_deliver` calls `ensure_categories_for_mvr_bind` before bind write on create-on-deliver. **Check 4b** is the hands-on proof. |
| **Test fixtures pre-wired MVR** | CI green while production cold-start failed | Capstone + matrix smoke tests use **negative fixtures** (no `ensure_categories_for_mvr_bind` in setup). See `prompts/cursor/WORKFLOW.md` § Negative fixtures. |

---

## Pre-flight (run once before hands-on)

### A — Repo hygiene

```bash
cd /path/to/mycelium
git log --oneline origin/main..HEAD | wc -l   # expect 14
git status
```

**Pass:**

- No `examples/networks/**/entities.json`, `deliveries.json`, `agents/`, `categories.json`, or DB files tracked or sitting untracked under `examples/networks/`
- If `entities.json` reappeared under `examples/networks/crm/`, delete it — something wrote runtime data into the example tree

### B — Automated baseline (recommended)

```bash
./bin/ci-local
```

**Pass:** all steps green (~390 smoke tests). This already covers capstones and path matrix A–D; manual checks prove **your** deployed roots and UI/MCP surfaces.

| Gate area | Smoke tests (in `./bin/ci-local`) |
|-----------|-------------------------------------|
| crm refresh + specialist storage | `test_crm_refresh_capstone_seed_specialist_storage` |
| empty-crm create-on-deliver | `test_empty_crm_refresh_capstone_create_on_deliver_storage` |
| Seed vs empty contrast | `test_matrix_a_*` + `test_matrix_b_*` |
| CLI bind `versions[]` | `test_status_entity_fields_include_versions_json` |
| Road Runner create-on-deliver | `test_matrix_c_crm_road_runner_create_on_deliver` |
| No duplicate bind version | `test_matrix_d_crm_road_runner_no_duplicate_bind_version` |
| Seed refresh idempotency | `test_refresh_crm_imports_seed_into_entities` + capstone |

Full integration (18 tests) was run at Grok review — not part of `ci-local`.

### C — Environment

| Item | Note |
|------|------|
| Network roots | `~/mycelium-networks/crm` and `~/mycelium-networks/empty-crm` (or your paths) |
| Registry | `uv run mycelium network list` — both networks registered after first refresh |
| Admin | `./bin/restart-admin crm` when a check needs UI |
| After **CLEAR** | Tell Grok **"Program 2 gate clear"** → push `origin/main` on request |

**Admin UI URLs:**

| URL | Use when |
|-----|----------|
| **http://127.0.0.1:8741/** | Default — built SPA + API; **use if :5173 is blank** |
| http://127.0.0.1:5173/ | Vite dev (hot reload); proxies to :8741 |

View Source showing empty `<div id="root"></div>` is normal until JS runs. Blank *visual* page on :5173 → DevTools Console, or use :8741 / `./bin/restart-admin crm --demo`.

---

## Fresh-start sequence (required checks in order)

Run checks **0 → 0b → 4b → 1 → 2 → 3 → 4 → 5 → 6 → 7**. Checks 4b before 4 because empty-crm is the cold-start path; crm Road Runner in Check 4 assumes seeded network.

Set once:

```bash
CRM_ROOT=~/mycelium-networks/crm
EMPTY_ROOT=~/mycelium-networks/empty-crm
```

---

## Check 0 — Clean crm deploy (required)

Wipe CRM runtime and recopy from the **clean** example tree:

```bash
./bin/refresh-example-network crm --yes
uv run mycelium network list
```

**Pass:**

- Exit 0; `crm` registered (default)
- `$CRM_ROOT/categories.json` exists
- `$CRM_ROOT/agents/demographic/storage.json` and `…/professional/storage.json` exist
- Refresh output includes seed import (15 entities)

**Automated:** `test_crm_refresh_capstone_seed_specialist_storage`

**Spot-check (optional):**

```bash
jq '.attribute_map | {name, employer}' "$CRM_ROOT/categories.json"
jq '.records | to_entries[0] | {id: .key, kind: .value.name.versions[0].actor.kind}' \
  "$CRM_ROOT/agents/demographic/storage.json"
```

Expect `name` → `demographic`, `employer` → `professional`; first name version `actor.kind` = `seed_bootstrap`.

```bash
./bin/restart-admin crm
```

---

## Check 0b — Seed vs empty contrast (required)

Proves the two example networks behave differently after refresh — the regression that confused "entities without specialists."

```bash
./bin/refresh-example-network empty-crm --yes
./bin/refresh-example-network crm --yes

uv run mycelium network status --network empty-crm
echo "---"
uv run mycelium network status --network crm
```

**Pass:**

| Network | Entities | Specialists | Seed line |
|---------|----------|-------------|-----------|
| `empty-crm` | ❌ | ❌ | No seed import |
| `crm` | ✅ (15) | `demographic (15)` + `professional (15)` | Refresh printed `seed: … → 15 entities imported` |

**Automated:** `test_matrix_a_crm_refresh_seed_bootstrap_storage` + `test_matrix_b_empty_crm_refresh_create_on_deliver_bind`

**On disk (optional):**

```bash
test ! -f "$EMPTY_ROOT/seed.json"
test ! -s "$EMPTY_ROOT/entities.json" 2>/dev/null || test ! -f "$EMPTY_ROOT/entities.json"
jq '.entities | length' "$CRM_ROOT/entities.json"   # 15
```

---

## Check 4b — empty-crm Paul Murphy create-on-deliver (required)

**Gate blocker fix (June 2026).** Cold-start network: no seed, no pre-existing MVR mappings in `categories.json`. Step 2 must bootstrap MVR mappings and write bind versions.

```bash
./bin/refresh-example-network empty-crm --yes

uv run mycelium query --network empty-crm \
  --lookup-json '{"name":"Paul Murphy","employer":"Acme Corp"}'
# → lookup_resolved, create_on_deliver: true, delivery_id d_…

uv run mycelium query --network empty-crm --delivery-id <delivery_id>
```

**Pass:**

- Step 1: `total_matches` = 0, `delivery.create_on_deliver` = true
- Step 2: `outcome` = `found`, `results[0].name` = `Paul Murphy`, `employer` = `Acme Corp`
- **Not** `not_found` / "No valid delivery"
- `uv run mycelium network status --network empty-crm` → Entities ✅ (1)
- On disk: UUID has `bind` versions in demographic + professional storage:

```bash
ID=<uuid-from-step-2>
jq --arg id "$ID" '.records[$id].name.versions[0].actor.kind' \
  "$EMPTY_ROOT/agents/demographic/storage.json"
jq --arg id "$ID" '.records[$id].employer.versions[0].actor.kind' \
  "$EMPTY_ROOT/agents/professional/storage.json"
```

Expect both `bind`.

**Automated:** `test_empty_crm_refresh_capstone_create_on_deliver_storage`

---

## Check 1 — CLI status: bind field `versions[]` (required)

```bash
uv run mycelium network status --network crm --entity "Andrea Kalmans" --json
```

**Pass:**

- `entity_matches` = 1
- `entity_fields` includes `field_kind` = `"bind"` for `name` and `employer`
- Both bind rows have non-empty `versions[]`
- At least one version `actor.kind` in `seed_bootstrap`, `bind`, or `research`
- `value` on bind rows matches entity cache

**Automated:** `test_status_entity_fields_include_versions_json`

---

## Check 2 — `provenance=true` includes bind fields (required)

```bash
uv run mycelium query --network crm \
  --lookup-json '{"name": "Andrea Kalmans", "employer": "Lontra Ventures"}' \
  --attributes linkedin --provenance

uv run mycelium query --network crm --delivery-id <delivery_id>
```

**Pass (step 2):**

- `outcome` = `found` or `assembled`
- `provenance.entities[0].attributes` includes **`name`** and **`employer`** with `versions[]` (not only `linkedin`)
- `results[]` stays flat — provenance separate from display fields

Re-run for **Nichanan Kesonpat** / `1k(x)` if Andrea has stale state.

**Automated:** manual only (provenance shape covered in unit/integration tests)

---

## Check 3 — Admin UI: bind version timeline (required)

```bash
./bin/restart-admin crm
```

Open **http://127.0.0.1:8741/** → Status → **Andrea Kalmans** → entity drill-down.

**Pass:**

- **Kind** column shows `bind` for name / employer
- Expandable version history on bind rows (timestamp, actor, value)
- No edit controls on bind rows (Program 3)

**Optional:** Run query tab two-step for Nichanan — MVR + Program 2 coexistence.

**Automated:** manual only

---

## Check 4 — crm Road Runner create-on-deliver (required)

Seeded network; entity not in seed.

```bash
uv run mycelium query --network crm \
  --lookup-json '{"name": "Road Runner", "employer": "Acme Corp"}'

uv run mycelium query --network crm --delivery-id <delivery_id>
```

Copy `results[0].id` → `ID` for Check 6.

**Pass:**

- Step 1: `total_matches` = 0, `create_on_deliver` = true
- Step 2: `found`, `name` = `Road Runner`
- Disk: UUID has `bind` in demographic + professional storage

```bash
jq --arg id "$ID" '.records[$id].name.versions[0].actor.kind' \
  "$CRM_ROOT/agents/demographic/storage.json"
```

**Automated:** `test_matrix_c_crm_road_runner_create_on_deliver`

---

## Check 5 — Empty employer row in status (required)

```bash
uv run mycelium query --network crm \
  --lookup-json '{"name": "Solo Gate", "employer": ""}'
uv run mycelium query --network crm --delivery-id <delivery_id>

uv run mycelium network status --network crm --entity "Solo Gate" --json
```

**Pass:**

- Step 2 creates/finds Solo Gate
- `entity_fields` includes `employer` with `field_kind` = `bind` and `value` = null (row present, not omitted)
- `name` bind row = `Solo Gate`

**Automated:** manual only

---

## Check 6 — No duplicate bind version on repeat (required)

Re-run Road Runner (already bound in Check 4):

```bash
uv run mycelium query --network crm \
  --lookup-json '{"name": "Road Runner", "employer": "Acme Corp"}'
uv run mycelium query --network crm --delivery-id <delivery_id>
```

**Pass:**

- Step 1: `total_matches` = 1 (not `create_on_deliver`)
- Step 2 succeeds
- Name version count still **1**:

```bash
jq --arg id "$ID" '.records[$id].name.versions | length' \
  "$CRM_ROOT/agents/demographic/storage.json"
```

**Automated:** `test_matrix_d_crm_road_runner_no_duplicate_bind_version`

---

## Check 7 — Seed refresh idempotency (required)

```bash
./bin/refresh-example-network crm --yes
uv run mycelium network status --network crm --entity "Andrea Kalmans" --json | \
  jq '[.entity_fields[] | select(.field_kind=="bind") | {field, versions: (.versions|length)}]'
```

**Pass:**

- Both bind fields `versions` length ≥ 1
- Overview: 15 entities, healthy ontology + specialist counts

**Automated:** `test_refresh_crm_imports_seed_into_entities` + `test_crm_refresh_capstone_seed_specialist_storage`

---

## Optional checks (8–10)

### Check 8 — MCP `provenance` with bind fields

Restart MCP for **crm**. Step 1 `query_entity` with `lookup`, `requested_attributes: ["linkedin"]`, `provenance: true`; step 2 with `delivery_id`.

**Pass:** step 2 includes `provenance.entities[].attributes.name` and `.employer` with `versions[]`.

### Check 9 — `crm-metering` provenance quote

```bash
./bin/refresh-example-network crm-metering --yes
uv run mycelium query --network crm-metering \
  --lookup-json '{"name": "Paul Murphy", "employer": "Acme Corp"}' \
  --attributes email --provenance
```

**Pass:** quote + delivered provenance coexist post–Program 2.

### Check 10 — Operator deference prompt (needs API keys)

Skip unless deep validation desired. Automated: `tests/test_research.py` operator deference tests.

---

## Failures → what to do

| Symptom | Likely cause | Action |
|---------|--------------|--------|
| `entities.json` under `examples/networks/crm/` | Runtime leaked into example tree | Delete file; fix whatever wrote it; re-run pre-flight A |
| No `categories.json` after refresh | `category_mvr_bootstrap` regression | Report to Grok with `git log -1` |
| **Entities ✅ but specialists ❌** (crm) | Stale example tree or old refresh copy path | Confirm example tree clean; re-refresh on current `main`; re-run **0b** |
| **empty-crm has entities/specialists after refresh only** | Should never happen (no seed) | Re-refresh empty-crm; check you are not pointing at `crm` root |
| Step 2 **"No valid delivery"** on empty-crm | MVR bootstrap regression (pre-fix) or stale code | Confirm `848ba02`+ on branch; re-run **4b** |
| Bind rows without `versions` | Specialist storage empty | Re-refresh crm; verify Check 0 spot-check |
| `provenance` missing bind attrs | Slice 2 / step 1 binding | Re-run Check 2 with fresh delivery |
| Extra Road Runner version (Check 6) | Polish P3 regression | Report check number + `jq` output |
| Admin blank on :5173 | Vite/JS error | Use **:8741** or `--demo` |

Report failures to Grok with **check number + command output**. Do **not** push until resolved or waived.

---

## When done

1. Change **Status** at top to **✅ CLEAR (YYYY-MM-DD)** — or tell Grok **"Program 2 gate clear."**
2. Tell Grok to **push** `origin/main` when ready ("we're ready to deliver").
3. Grok + Paul: update `TODO.md` — Program 2 complete on `origin/main`.
4. Optional: website/onboarding sync per [`next-chunk-prep.md`](../plans/next-chunk-prep.md).

```bash
git push origin main
```

---

*Created: 2026-06-13 · Rewritten: 2026-06-14 (post seed-refresh, empty-crm MVR, capstone tests)*