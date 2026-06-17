# Manual checks — Program 2 post-program gate (MVR / entity storage)

**Status:** ✅ **CLEAR** (2026-06-14) — Paul manual gate passed; Program 2 verified on `origin/main`

> **Errata (June 2026 — framework MVR generic vocabulary):** Suggestion `reason` strings are now `bind_field_fuzzy_match` (was `employer_sequence_ratio`) and `same_bind_field_conflict` (was `same_name_different_employer`). Retry maps use `suggestions[].suggested_lookup` only (no `suggestion.name` / `suggestion.employer`). Automated CRM check: `./bin/smoke-crm-e2e`.

> **Superseded for status inspect:** Program 3 (slice 1520+) replaced `--entity` with `--lookup-json` / `--id` and added `resolve` JSON on status responses. Use [`2026-06-14-program3-post-program-gate.md`](2026-06-14-program3-post-program-gate.md) for the current protocol checklist after Program 3 gate **CLEAR**.

**Context:** Program 2 (Slices 1–3 + polish P1–P7 + remedial fixes + capstone tests + **step-1 lookup clarity** + **fuzzy bind-field suggestions 1430–1450**) is **on `origin/main`** (`f5cf089` and later). This gate validates hands-on behavior on a synced checkout — **restart MCP** after pulling so suggestion shape matches code.

**What Program 2 proves:**

- MVR bind fields (`name`, `employer`) live in **taxonomy-owned specialist `versions[]`**, not entity-level history
- Unified write on seed import, registry bind, and create-on-deliver
- Read surfaces: `provenance=true`, CLI/admin `entity_fields[].versions[]` for bind fields
- Research operator deference (prompt) + polish fixes (ordering, no-op skip, rollback, empty employer row)
- **Step-1 lookup clarity:** `lookup_incomplete`, `lookup_suggested`, and `confirm_new_entity` — no overloaded `not_found`, no silent create on same-name collision
- **Fuzzy bind-field suggestions:** partial/full 0-hit typos → `lookup_suggested` with `suggestions[].suggested_lookup` (employer suggests canonical employer string; does **not** auto-batch-resolve employees)

**Prereqs:** Framework repo root; `uv sync` done. Live roots under `~/mycelium-networks/` (never test in-place under `examples/networks/…`). Optional checks 8–10 need API keys in `.env`.

**Estimated time:** ~75–90 min (required checks 0–7 + **0c** + **4b**); optional 8–10 add ~20 min.

---

## Step-1 outcomes (know before you run)

Target protocol step 1 now returns **distinct outcomes** — agents should branch on `outcome` before reading `results` or issuing step 2.

| Case | Example lookup | Outcome | `delivery` | Key response fields |
|------|----------------|---------|------------|---------------------|
| Partial lookup, 0 hits | `{"name":"Paul Murphy"}` | `lookup_incomplete` | none | `required_fields: ["employer"]` |
| Partial lookup, ≥1 hit | `{"name":"Andrea Kalmans"}` | `lookup_resolved` | yes | `total_matches: N` |
| Partial lookup, fuzzy employer | `{"employer":"645 Venture"}` | `lookup_suggested` | none | `suggestions[].suggested_lookup: {"employer":"645 Ventures"}` (`employer_sequence_ratio`) |
| Full MVR, same name elsewhere | Andrea @ Wrong Corp (Lontra in seed) | `lookup_suggested` | none | `suggestions[]` (`same_name_different_employer`; may include `suggested_lookup`) |
| Full MVR, fuzzy name | `{"name":"Andrea Kalman","employer":"Acme Corp"}` | `lookup_suggested` | none | `suggestions[].suggested_lookup: {"name":"Andrea Kalmans"}` (`sequence_ratio`) |
| Full MVR, safe create | Road Runner @ Acme (no collision) | `lookup_resolved` | yes | `create_on_deliver: true` |
| Full MVR, intentional new bind | Andrea @ Wrong + `confirm_new_entity` | `lookup_resolved` | yes | `create_on_deliver: true` |
| True dead end | unknown `id`, expired `delivery_id` | `not_found` | none | unchanged |

**MVR bind field names** come from `describe_network` → `policy.mvr.bind_fields` — not from every query response. Responses surface **what is missing** (`required_fields`) or **what is similar** (`suggestions` with **`suggested_lookup`** retry maps — not retired `entity_key`).

**`confirm_new_entity`:** Step-1 only. Re-query the same full MVR lookup with `confirm_new_entity: true` (CLI: `--confirm-new-entity`) after reviewing `lookup_suggested` to intentionally create a new registry row.

---

## Regressions fixed before this gate (know what you are validating)

These bugs slipped past smoke CI until June 2026 remedial work. The checklist below is designed to catch them again.

| Issue | Symptom | Fix / guard |
|-------|---------|-------------|
| **Committed runtime in example tree** | `refresh` copied `examples/networks/crm/entities.json` → seed import saw duplicates → **Entities ✅ but specialists ❌** | Example tree must ship **reference files only** (`seed.json`, `network.json`, `guide.md`, README). Layout tests fail if `entities.json`, `deliveries.json`, or `agents/` exist under `examples/networks/`. **Not gitignored** — stray files show in `git status`. |
| **Seed refresh specialist storage** | Same as above on crm refresh | `refresh` skips copying `entities.json`; seed bootstrap backfills demographic + professional storage with `seed_bootstrap` versions. |
| **empty-crm step 2 MVR bootstrap** | Step 1 OK; step 2 → `not_found` / **"No valid delivery"** (misleading — real error was missing `attribute_map` for `name`/`employer`) | `target_deliver` calls `ensure_categories_for_mvr_bind` before bind write on create-on-deliver. **Check 4b** is the hands-on proof. |
| **Silent create on same-name collision** | Andrea @ Wrong Corp issued `create_on_deliver` without warning | Step 1 returns `lookup_suggested`; create requires `confirm_new_entity`. **Check 0c** is the hands-on proof. |
| **Partial lookup overloads `not_found`** | `{"name":"Paul Murphy"}` → `not_found` | Now `lookup_incomplete` + `required_fields`. **Check 0c** |
| **Test fixtures pre-wired MVR** | CI green while production cold-start failed | Capstone + matrix smoke tests use **negative fixtures** (no `ensure_categories_for_mvr_bind` in setup). See `prompts/cursor/WORKFLOW.md` § Negative fixtures. |

---

## Pre-flight (run once before hands-on)

### A — Repo hygiene

```bash
cd /path/to/mycelium
git fetch origin && git status
git log --oneline -1 origin/main
```

**Pass:**

- `main` matches `origin/main` (or only doc-only commits ahead — code for this gate is already pushed)
- No `examples/networks/**/entities.json`, `deliveries.json`, `agents/`, `categories.json`, or DB files tracked or sitting untracked under `examples/networks/`
- If `entities.json` reappeared under `examples/networks/crm/`, delete it — something wrote runtime data into the example tree

### B — Automated baseline (recommended)

```bash
./bin/ci-local
```

**Pass:** all steps green (~419 smoke tests). This already covers capstones, path matrix A–D, step-1 lookup clarity, and fuzzy bind-field suggestions; manual checks prove **your** deployed roots and UI/MCP surfaces.

| Gate area | Smoke tests (in `./bin/ci-local`) |
|-----------|-------------------------------------|
| crm refresh + specialist storage | `test_crm_refresh_capstone_seed_specialist_storage` |
| empty-crm create-on-deliver | `test_empty_crm_refresh_capstone_create_on_deliver_storage` |
| Seed vs empty contrast | `test_matrix_a_*` + `test_matrix_b_*` |
| CLI bind `versions[]` | `test_status_entity_fields_include_versions_json` |
| Road Runner create-on-deliver | `test_matrix_c_crm_road_runner_create_on_deliver` |
| No duplicate bind version | `test_matrix_d_crm_road_runner_no_duplicate_bind_version` |
| Seed refresh idempotency | `test_refresh_crm_imports_seed_into_entities` + capstone |
| **Step-1 lookup clarity + fuzzy** | `tests/test_target_step1_lookup_clarity.py` (18 tests) |

Full integration (18 tests) was run at Grok review — not part of `ci-local`.

### C — Environment

| Item | Note |
|------|------|
| Network roots | `~/mycelium-networks/crm` and `~/mycelium-networks/empty-crm` (or your paths) |
| Registry | `uv run mycelium network list` — both networks registered after first refresh |
| Admin | `./bin/restart-admin crm` when a check needs UI |
| After **CLEAR** | Tell Grok **"Program 2 gate clear"** — code already on `origin/main`; gate sign-off only |
| MCP | Restart MCP after `git pull` so `lookup_suggested` uses `suggested_lookup` (not retired `entity_key`) |

**Admin UI URLs:**

| URL | Use when |
|-----|----------|
| **http://127.0.0.1:8741/** | Default — built SPA + API; **use if :5173 is blank** |
| http://127.0.0.1:5173/ | Vite dev (hot reload); proxies to :8741 |

View Source showing empty `<div id="root"></div>` is normal until JS runs. Blank *visual* page on :5173 → DevTools Console, or use :8741 / `./bin/restart-admin crm --demo`.

---

## Fresh-start sequence (required checks in order)

Run checks **0 → 0b → 0c → 4b → 1 → 2 → 3 → 4 → 6 → 7**. Check **0c** (lookup clarity) needs seeded `crm`. Check **4b** before **4** because empty-crm is the cold-start path; crm Road Runner in Check 4 assumes seeded network. Check 5 is **automated only** (skip manual).

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

## Check 0c — Step-1 lookup clarity (required)

Proves new step-1 outcomes and `confirm_new_entity`. Run on **seeded crm** after Check 0.

### 0c-i — `lookup_incomplete` (partial lookup, 0 hits)

```bash
uv run mycelium query --network crm \
  --lookup-json '{"name":"Paul Murphy"}'
```

**Pass:**

- `outcome` = `lookup_incomplete`
- `required_fields` includes `employer`
- **No** `delivery` / `delivery_id`
- `total_matches` = 0 (may be present on wire)

**Automated:** `test_partial_lookup_missing_employer_lookup_incomplete`

### 0c-ii — Partial lookup with hit (unchanged R4 search)

```bash
uv run mycelium query --network crm \
  --lookup-json '{"name":"Andrea Kalmans"}'
```

**Pass:**

- `outcome` = `lookup_resolved`
- `total_matches` ≥ 1
- `delivery.delivery_id` present
- **No** `create_on_deliver`

**Automated:** `test_partial_lookup_name_hit_lookup_resolved`

### 0c-iii — `lookup_suggested` (same name, wrong employer)

```bash
uv run mycelium query --network crm \
  --lookup-json '{"name":"Andrea Kalmans","employer":"Wrong Corp"}'
```

**Pass:**

- `outcome` = `lookup_suggested`
- `suggestions[]` non-empty; at least one entry has `reason: same_name_different_employer`, `employer: Lontra Ventures`, and `id` for the seed row
- **No** `delivery` / `delivery_id`
- Message mentions retry with `id`, merged `suggested_lookup`, or `confirm_new_entity`

**Automated:** `test_full_mvr_wrong_employer_lookup_suggested`

### 0c-iv — `confirm_new_entity` (intentional create after warning)

```bash
uv run mycelium query --network crm \
  --lookup-json '{"name":"Andrea Kalmans","employer":"Wrong Corp"}' \
  --confirm-new-entity
```

**Pass:**

- `outcome` = `lookup_resolved`
- `total_matches` = 0
- `delivery.create_on_deliver` = true
- `delivery.delivery_id` present

Optional: run step 2 with that `delivery_id` — should create Andrea @ Wrong Corp (distinct UUID from seed Andrea).

**Automated:** `test_full_mvr_wrong_employer_confirm_creates`

### 0c-v — Fuzzy name suggestion

```bash
uv run mycelium query --network crm \
  --lookup-json '{"name":"Andrea Kalman","employer":"Acme Corp"}'
```

**Pass:**

- `outcome` = `lookup_suggested`
- `suggestions[0].reason` = `sequence_ratio`
- `suggestions[0].suggested_lookup` = `{"name": "Andrea Kalmans"}` (or equivalent normalized map)

**Automated:** `test_fuzzy_name_lookup_suggested`, `test_name_fuzzy_suggested_lookup_shape`

### 0c-vii — Fuzzy employer suggestion (partial lookup)

```bash
uv run mycelium query --network crm \
  --lookup-json '{"employer":"645 Venture"}'
```

**Pass:**

- `outcome` = `lookup_suggested` (not `lookup_resolved` with a single employee)
- `suggestions[0].reason` = `employer_sequence_ratio`
- `suggestions[0].suggested_lookup` = `{"employer": "645 Ventures"}`
- **No** `delivery` / `delivery_id`

Retry with corrected employer — should resolve multiple employees:

```bash
uv run mycelium query --network crm \
  --lookup-json '{"employer":"645 Ventures"}'
```

**Pass:** `lookup_resolved`, `total_matches` ≥ 1 (e.g. Aaron Holiday and others at 645 Ventures).

**Automated:** `test_partial_fuzzy_employer_lookup_suggested`, `test_partial_fuzzy_employer_plural_typo_suggests_employer`, `test_employer_fuzzy_suggested_lookup_shape`, `test_partial_fuzzy_employer_retry_then_resolved`

### 0c-viii — Admin UI (recommended)

```bash
./bin/restart-admin crm
```

**Entity lookup** — Inspect only (no `POST /query`):

1. MVR mode: name `Andrea Kalmans` → **Inspect** → drill-down table via `GET /status`.
2. Full MVR: name + employer `Lontra Ventures` → **Inspect** uses `GET /status?lookup=…`.

**Run query** — separate step buttons:

1. Step 1 **Run**: Andrea @ Wrong Corp → `lookup_suggested`, suggestions visible (`suggested_lookup` or `id`).
2. Click suggestion → fields populate from `suggested_lookup`; **Confirm new entity** → Step 1 **Run** → `lookup_resolved` + `create_on_deliver`.
3. Partial employer typo `645 Venture` → `lookup_suggested` with employer correction; retry → multiple matches.
4. Step 2 **Deliver** with `delivery_id` (not the only Run on the page).

**Automated:** `test_admin_query_lookup_suggested_shape`, `test_status_lookup_map_single_match`

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

**Automated:** `test_empty_crm_refresh_capstone_create_on_deliver_storage`, `test_empty_crm_safe_create_without_confirm`

---

## Check 1 — CLI status: bind field `versions[]` (required)

```bash
uv run mycelium network status --network crm --lookup-json '{"name":"Andrea Kalmans"}' --json
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

Seeded network; entity not in seed; **no name collision** → safe create without `confirm_new_entity`.

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

**Automated:** `test_matrix_c_crm_road_runner_create_on_deliver`, `test_full_mvr_no_collision_create`

---

## Check 5 — Empty employer row in status (automated only — skip manual)

**Do not run this check by hand.** There is no legitimate production path that produces the state this test exercises.

**What it guards (polish P5):** `_bind_field_statuses` used to **skip** the `employer` row when the cached value was empty, so admin/CLI status hid a bind field that MVR declares. The fix: always emit every `mvr.bind_fields` row; `value` may be `null`.

**Why manual reproduction is misleading:** Empty employer is blocked in real flows:

- Query step 1 requires a **full MVR** lookup (non-empty `employer`) before issuing `delivery_id` for create
- Partial lookup with only `name` returns `lookup_incomplete` — not create
- `validate_entity` fails employer &lt; 2 characters on provisional binds

The smoke test uses a **fixture shortcut** (`bind_provisional` + `promote_validated`, bypassing validation) to manufacture a registry row that query flow would never create. That is a regression test for introspection code, not proof that empty employer is valid CRM data.

**Automated:** `test_status_bind_rows_include_empty_employer` in `tests/test_network_status.py` (smoke; `./bin/ci-local`)

**Optional:** `uv run pytest tests/test_network_status.py::test_status_bind_rows_include_empty_employer -q` if you want to re-run that single test while debugging CI.

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
uv run mycelium network status --network crm --lookup-json '{"name":"Andrea Kalmans"}' --json | \
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

### Check 8b — MCP / `describe_network` step-1 policy (optional)

```bash
# Via MCP describe_network or introspection output
```

**Pass:** Policy text mentions `lookup_incomplete`, `lookup_suggested`, and `confirm_new_entity` under target protocol rules.

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
| Step 2 **"No valid delivery"** on empty-crm | MVR bootstrap regression (pre-fix) or stale code | Confirm remedial slices on branch; re-run **4b** |
| Partial lookup `{"name":"…"}` → `not_found` | Pre–lookup-clarity code | Expect `lookup_incomplete` + `required_fields`; re-run **0c-i** |
| Andrea @ Wrong Corp → silent `create_on_deliver` | Pre–lookup-clarity code | Expect `lookup_suggested`; re-run **0c-iii** |
| `645 Venture` → one employee auto-resolved | Pre–fuzzy-employer code | Expect `lookup_suggested` + `suggested_lookup`; re-run **0c-vii** |
| Suggestions expose `entity_key` not `suggested_lookup` | Stale MCP or pre–1450 code | Restart MCP; `git pull`; re-run **0c-v** / **0c-vii** |
| Step 1 `not_found`, `employer: ""` in lookup | Empty employer — not full MVR | Expected; use `lookup_incomplete` path or supply employer |
| Bind rows without `versions` | Specialist storage empty | Re-refresh crm; verify Check 0 spot-check |
| `provenance` missing bind attrs | Slice 2 / step 1 binding | Re-run Check 2 with fresh delivery |
| Extra Road Runner version (Check 6) | Polish P3 regression | Report check number + `jq` output |
| Admin blank on :5173 | Vite/JS error | Use **:8741** or `--demo` |

Report failures to Grok with **check number + command output**.

---

## When done

1. Change **Status** at top to **✅ CLEAR (YYYY-MM-DD)** — or tell Grok **"Program 2 gate clear."**
2. Grok + Paul: update `TODO.md` — Program 2 gate **CLEAR** (code already on `origin/main`).
3. Optional: website sync per [`next-chunk-prep.md`](../plans/next-chunk-prep.md).

---

*Created: 2026-06-13 · Rewritten: 2026-06-14 (seed-refresh, empty-crm MVR, capstone tests) · Updated: 2026-06-14 (step-1 lookup clarity, fuzzy suggestions 1430–1450, `suggested_lookup`) · **CLEAR** 2026-06-14*