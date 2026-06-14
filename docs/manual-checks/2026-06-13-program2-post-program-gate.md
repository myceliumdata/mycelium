# Manual checks — Program 2 post-program gate (MVR / entity storage)

**Status:** ⏳ **PENDING** — run morning checklist; mark **CLEAR** when all required checks pass.

**Context:** Program 2 (Slices 1–3 + polish P1–P7) is **committed locally** on `main` — **5 commits ahead of `origin/main`**. This gate validates hands-on behavior before **pushing** that chunk to `origin/main`. Automated baseline: `./bin/ci-local` (382 smoke passed at last review).

**What Program 2 proves:**

- MVR bind fields (`name`, `employer`) live in **taxonomy-owned specialist `versions[]`**, not entity-level history
- Unified write on seed import, registry bind, and create-on-deliver
- Read surfaces: `provenance=true`, CLI/admin `entity_fields[].versions[]` for bind fields
- Research operator deference (prompt) + polish fixes (ordering, no-op skip, rollback, empty employer row)

**Prereqs:** Framework repo root; `uv sync` done. **Deployed** live roots under `~/mycelium-networks/` (not `examples/networks/…` in place). Optional checks need `OPENAI_API_KEY` + `TAVILY_API_KEY` in `.env`.

**Estimated time:** ~45–60 min (required checks 0–7); optional 8–10 add ~20 min.

---

## Before you start

| Item | Note |
|------|------|
| Local git | `git log origin/main..HEAD` should show 5 commits (Program 2 + polish). No push yet. |
| After **CLEAR** | Paul tells Grok **“Program 2 gate clear”** or updates **Status** below → Grok pushes `origin/main` on request. |
| `TODO.md` | Grok + Paul bump after gate clear (Cursor does not edit). |

---

## 0 — Clean deploy (required)

Wipe CRM runtime and recopy from examples:

```bash
./bin/refresh-example-network crm --yes
uv run mycelium network list
# expect: crm registered (default)
```

**Pass:**

- Command exits 0
- `~/mycelium-networks/crm/categories.json` exists
- `~/mycelium-networks/crm/agents/demographic/storage.json` and `…/professional/storage.json` exist (seed import wrote MVR bind versions)

**Spot-check on disk (optional):**

```bash
CRM_ROOT=~/mycelium-networks/crm   # adjust if your root differs
jq '.attribute_map | {name, employer}' "$CRM_ROOT/categories.json"
jq '.records | to_entries[0] | {id: .key, name: .value.name.versions[0].actor.kind}' \
  "$CRM_ROOT/agents/demographic/storage.json"
```

Expect `name` → `demographic`, `employer` → `professional`; first name version `actor.kind` = `seed_bootstrap`.

Restart surfaces after refresh:

```bash
./bin/restart-admin crm
# Restart MCP for crm if you run optional Check 8
```

**Admin UI URL:** Default dev stack runs **two** URLs:

| URL | What it is |
|-----|------------|
| **http://127.0.0.1:8741/** | Built SPA + API (same process) — **use this if :5173 is blank** |
| http://127.0.0.1:5173/ | Vite dev (hot reload); proxies API to :8741 |

View Source on either URL always shows empty `<div id="root"></div>` until JS runs — that is normal. A **visually** blank page on :5173 usually means a browser JS error; open DevTools → **Console**. **Workaround:** open **:8741** (no Vite), or `./bin/restart-admin crm --demo` (rebuild + single process on :8741).

---

## Quick smoke (optional)

```bash
./bin/ci-local
```

**Pass:** all steps green.

---

## Check 1 — CLI status: bind field `versions[]` (Slice 2)

Confirms admin/CLI introspection exposes MVR history from specialist storage.

```bash
uv run mycelium network status --network crm --entity "Andrea Kalmans" --json
```

**Pass criteria:**

- `entity_matches` = 1
- `entity_fields` includes rows with `field_kind` = `"bind"` for `name` and `employer`
- Both bind rows have non-empty `versions` arrays
- At least one version has `actor.kind` in `seed_bootstrap`, `bind`, or `research`
- `value` on bind rows matches entity cache (display from registry, history from specialist)

---

## Check 2 — `provenance=true` includes bind fields (Slice 2)

Confirms `QueryResponse.provenance` attaches MVR attrs when step 1 bound them.

```bash
# Step 1 — bind provenance + attrs on step 1 only
uv run mycelium query --network crm \
  --lookup-json '{"name": "Andrea Kalmans", "employer": "Lontra Ventures"}' \
  --attributes linkedin --provenance

# Step 2 — paste delivery_id from step 1 JSON
uv run mycelium query --network crm --delivery-id <delivery_id>
```

**Pass criteria (step 2 JSON):**

- `outcome` = `found` or `assembled`
- `provenance` is non-null
- `provenance.entities[0].attributes` includes **`name`** and **`employer`** with `versions[]` (not only `linkedin`)
- `results[]` remains flat — provenance is separate from `results[0].name` / employer display
- Re-run step 1 + 2 for **Nichanan Kesonpat** / `1k(x)` if Andrea already had stale state — same provenance shape expected

---

## Check 3 — Admin UI: bind version timeline (Slice 2)

```bash
./bin/restart-admin crm
```

Open **http://127.0.0.1:8741/** (recommended — built SPA). Fallback: http://127.0.0.1:5173/ (Vite dev).

1. **Status** tab → search **Andrea Kalmans** → open entity drill-down
2. Confirm **Kind** column shows `bind` for name / employer
3. Expand version history on a bind row (same disclosure UI as extended fields)

**Pass criteria:**

- Bind rows visible with values
- Expandable version panel shows at least one version (timestamp, actor, value)
- No edit controls on bind rows (Program 3)

**Optional UI flow:** Two-step query for Nichanan in **Run query** tab (step 1 `lookup_resolved`, step 2 `found`) — regression guard for MVR + Program 2 coexistence.

---

## Check 4 — Create-on-deliver writes specialist bind versions (Slice 1 + 3)

Confirms unified write on step-2 provisional bind (not in seed).

```bash
# Step 1 — 0 matches, create_on_deliver
uv run mycelium query --network crm \
  --lookup-json '{"name": "Road Runner", "employer": "Acme Corp"}'

# Step 2
uv run mycelium query --network crm --delivery-id <delivery_id>
```

Copy `results[0].id` (UUID) from step 2.

**Pass criteria:**

- Step 1: `total_matches` = 0, `delivery.create_on_deliver` = true
- Step 2: `outcome` = `found`, `results[0].name` = `Road Runner`
- On disk, that UUID has `name` / `employer` entries in demographic + professional storage with `actor.kind` = `bind`:

```bash
ID=<uuid-from-step-2>
jq --arg id "$ID" '.records[$id].name.versions[0].actor.kind' \
  "$CRM_ROOT/agents/demographic/storage.json"
jq --arg id "$ID" '.records[$id].employer.versions[0].actor.kind' \
  "$CRM_ROOT/agents/professional/storage.json"
```

---

## Check 5 — Empty employer row in status (polish P5)

Confirms introspection no longer hides empty `employer`.

```bash
# Step 1
uv run mycelium query --network crm \
  --lookup-json '{"name": "Solo Gate", "employer": ""}'

# Step 2
uv run mycelium query --network crm --delivery-id <delivery_id>
```

```bash
uv run mycelium network status --network crm --entity "Solo Gate" --json
```

**Pass criteria:**

- Step 2 creates/finds Solo Gate
- `entity_fields` includes `employer` with `field_kind` = `bind` and `value` = null (or omitted/null — not absent from the list)
- `name` bind row present with value `Solo Gate`

---

## Check 6 — No duplicate bind version on repeat (polish P3)

Re-run create flow for **Road Runner** (already bound in Check 4).

```bash
uv run mycelium query --network crm \
  --lookup-json '{"name": "Road Runner", "employer": "Acme Corp"}'
uv run mycelium query --network crm --delivery-id <delivery_id>
```

**Pass criteria:**

- Step 1: `total_matches` = 1 (existing row — not create_on_deliver)
- Step 2 succeeds
- Name version count still **1** (no spurious append):

```bash
jq --arg id "$ID" '.records[$id].name.versions | length' \
  "$CRM_ROOT/agents/demographic/storage.json"
```

Expect `1`. (Registry duplicate short-circuit without backfill is documented in CRM README — Check 6 validates no-op append only when write path runs.)

---

## Check 7 — Seed refresh idempotency (Slice 1 + P7 doc)

Re-run refresh (destructive) and confirm seed bootstrap still populates specialist storage:

```bash
./bin/refresh-example-network crm --yes
uv run mycelium network status --network crm --entity "Andrea Kalmans" --json | \
  jq '[.entity_fields[] | select(.field_kind=="bind") | {field, versions: (.versions|length)}]'
```

**Pass criteria:**

- Both bind fields show `versions` length ≥ 1
- No errors; ontology + specialist counts healthy on `network status` overview

---

## Check 8 — MCP `provenance` with bind fields (optional)

Restart MCP for **crm**. **Step 1** `query_entity`:

```json
{
  "lookup": {"name": "Andrea Kalmans", "employer": "Lontra Ventures"},
  "requested_attributes": ["linkedin"],
  "provenance": true
}
```

**Step 2:**

```json
{
  "delivery_id": "d_…"
}
```

**Pass:** step 2 response includes `provenance.entities[].attributes.name` and `.employer` with `versions[]`.

---

## Check 9 — `crm-metering` provenance quote (optional)

Confirms metering + provenance still works post–Program 2.

```bash
./bin/refresh-example-network crm-metering --yes

uv run mycelium query --network crm-metering \
  --lookup-json '{"name": "Paul Murphy", "employer": "Acme Corp"}' \
  --attributes email --provenance
```

If `quote_required`, accept with `--quote-id` and re-run step 2 deliver.

**Pass:** quote line items include `query_provenance` when applicable; delivered response has provenance block (extended + bind if storage populated).

---

## Check 10 — Operator deference prompt (optional, needs API keys)

Program 3 will add operator **writes**; Slice 3 only adds **prompt** deference. Manual proof requires seeding an operator version in storage (advanced).

**Skip unless you want deep validation.** Automated coverage: `tests/test_research.py` (`test_build_research_prompts_injects_operator_deference`, `test_persist_proposal_appends_after_operator_version`).

If attempting manually: edit one field in `agents/contact/storage.json` to set current version `actor.kind` = `operator`, then trigger research for that field and inspect logs/prompt — expect `OPERATOR OVERRIDE` block before peer context.

---

## Failures → what to do

| Symptom | Likely cause |
|---------|----------------|
| No `categories.json` after refresh | Slice 1 bootstrap regression — check `category_mvr_bootstrap` |
| Bind rows without `versions` | Specialist storage empty — seed import path or hard-cutover duplicate hit |
| `provenance` missing bind attrs | Slice 2 — requested attrs not bound on step 1 or no specialist versions |
| Road Runner step 2 fails | MVR / deliver regression — check daemon logs |
| Extra version on Check 6 | Polish P3 regression |
| Admin UI blank on :5173 | Use **:8741** or `--demo`; check browser Console on :5173; `cd admin-ui && rm -rf node_modules/.vite && npm run dev` |

Report failures to Grok with check number + command output; do **not** push until resolved or waived.

---

## When done

1. Change **Status** at top to **✅ CLEAR (YYYY-MM-DD)** — or tell Grok **“Program 2 gate clear.”**
2. Tell Grok to **push** `origin/main` when ready to deliver (Paul: “we’re ready to deliver”).
3. Grok + Paul: update `TODO.md` — Program 2 complete on `origin/main`.
4. Optional: website/onboarding sync per [`next-chunk-prep.md`](../plans/next-chunk-prep.md).

**Push command (Grok/Paul when delivering):**

```bash
git push origin main
```

---

*Created: 2026-06-13 · Program 2 Slices 1–3 + polish · Local commits awaiting gate*