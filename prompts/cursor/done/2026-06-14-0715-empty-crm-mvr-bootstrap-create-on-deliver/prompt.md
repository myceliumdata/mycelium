# Fix: empty-crm create-on-deliver — MVR bootstrap before bind write

> **READY** — Move to `in-progress/` before starting (see `prompts/cursor/WORKFLOW.md`).

**Context:** Program 2 manual gate — `empty-crm` two-step query fails on step 2 after a valid step-1 `delivery_id`.

---

## Bug (repro)

```bash
./bin/refresh-example-network empty-crm --yes

uv run mycelium query --network empty-crm \
  --lookup-json '{"name":"Paul Murphy","employer":"Acme Corp"}'
# → lookup_resolved, create_on_deliver: true, delivery_id d_…

uv run mycelium query --network empty-crm --delivery-id <delivery_id>
# → outcome not_found, message "No valid delivery for delivery_id …"
```

**Root cause (confirmed):** Step 1 bootstraps `categories.json` from the classification engine sample tree **without** MVR `attribute_map` entries for `name` and `employer`. Step 2 `bind_provisional_from_scope` → `ensure_entity_bind_fields` raises:

`MVR bind field 'name' is not mapped in categories.json attribute_map`

`target_resolve` maps that `ValueError` to the misleading **"No valid delivery"** message (delivery scope is still valid on disk).

**Works today:** Seeded `crm` refresh calls `ensure_categories_for_mvr_bind` inside `bootstrap_seed_at_paths` (`src/network/seed_import.py`). No-seed networks never hit that path.

Verify on a failing root:

```bash
jq '.attribute_map | {name, employer}' ~/mycelium-networks/empty-crm/categories.json
# expect null/null after step 1 only
```

---

## Read first

- `prompts/cursor/WORKFLOW.md`
- `docs/architecture.md` — MVR bind / unified write (Program 2)
- `src/network/category_mvr_bootstrap.py` — `ensure_categories_for_mvr_bind`, `ensure_mvr_fields_in_category_tree`
- `src/agents/target_deliver.py` — `bind_provisional_from_scope`, `hydrate_matches_for_deliver`
- `src/agents/dispatch.py` — step-2 deliver error mapping (~lines 133–156)
- `examples/networks/empty-crm/README.md`
- `docs/manual-checks/2026-06-13-program2-post-program-gate.md` — Check 4 (create-on-deliver; uses seeded `crm` today)

---

## Objective

Ensure **create-on-deliver** (step 2) can write MVR bind fields to specialist storage on **no-seed** networks (`empty-crm`), same unified write path as seed bootstrap.

---

## Implement

### 1 — Call MVR category bootstrap before provisional bind

Before `ensure_entity_bind_fields` runs for create-on-deliver, ensure `categories.json` maps MVR bind fields.

**Preferred locus:** `bind_provisional_from_scope` in `src/agents/target_deliver.py` (or `hydrate_matches_for_deliver` immediately before bind) — call:

```python
from network.category_mvr_bootstrap import ensure_categories_for_mvr_bind
from network.paths import NetworkPaths, runtime_path  # or equivalent paths helper

ensure_categories_for_mvr_bind(NetworkPaths.from_root(runtime_path("MYCELIUM_NETWORK_ROOT").parent))
# use the same NetworkPaths resolution pattern the codebase already uses for runtime roots
```

Use existing `ensure_categories_for_mvr_bind` — **do not duplicate** merge logic. After merge, `reset_category_tree()` inside that helper already reloads the tree.

**Idempotent:** Safe when `name`/`employer` already mapped (seeded CRM must not regress).

### 2 — Smoke test (required)

Add a test that reproduces the **empty-crm** gap: categories exist **without** MVR bind keys in `attribute_map`, then step 1 + step 2 succeed.

Suggested approach (pick one clean path):

- New test in `tests/test_mvr_create_on_deliver.py` or `tests/test_example_network.py`, **or**
- Extend empty-crm coverage in a focused new file `tests/test_empty_crm_create_on_deliver.py`

Test sketch:

1. `tmp_path` network root with `network.json` from `examples/networks/empty-crm/`
2. **No** `seed.json`; **no** upfront `ensure_categories_for_mvr_bind` in fixture
3. Copy or synthesize a `categories.json` like step-1 produces (sample tree **missing** `attribute_map.name` / `.employer`) — mirror Paul's failing state
4. `run_query` step 1 full MVR lookup → `lookup_resolved`, `create_on_deliver`
5. `run_query` step 2 with `delivery_id` → `found`, one result
6. Assert `agents/demographic/storage.json` and `agents/professional/storage.json` each have one record; `name` version `actor.kind` == `bind`

Mark `@pytest.mark.smoke`.

### 3 — Optional (only if trivial)

Improve step-2 error when hydration/bind fails: surface the underlying `ValueError` message in `audit_log` or `debug` instead of only "No valid delivery" — **do not** change public `outcome` enum. Skip if it widens scope.

### 4 — Doc touch (one line)

`examples/networks/empty-crm/README.md` — note that step 2 requires MVR mappings in `categories.json` (now ensured automatically on create-on-deliver).

---

## Scope boundaries (strict)

**You may modify:**

- `src/agents/target_deliver.py`
- `tests/test_mvr_create_on_deliver.py` and/or `tests/test_example_network.py` and/or new test file under `tests/`
- `examples/networks/empty-crm/README.md` (one-line note only)

**Out of scope — do not touch:**

- `TODO.md`
- Program 3 operator UI
- Seed refresh / `entities.json` copy logic (separate fix already on `main`)
- Changing MVR bind field definitions or `CRM_MVR_FIELD_CATEGORY` semantics
- `src/network/seed_import.py` unless a one-line shared helper call is clearly DRY (prefer target_deliver only)

If you believe another file is required, stop and document in `output.md` — do not expand scope silently.

---

## Verification

```bash
./bin/ci-local
```

Manual sanity (document in `output.md`):

```bash
./bin/refresh-example-network empty-crm --yes
# step 1 + step 2 as in Bug section → found, specialists on disk
```

---

## Governance (mandatory)

- **Do not edit `TODO.md`.** Roadmap updates are for Grok + Paul after review.
- In `output.md`, add **"For Grok + Paul"**: gate doc note (empty-crm step 2), any manual-check follow-up.
- Cursor delivers: code, tests, task-scoped docs, and `output.md` only.

## When finished (mandatory — see WORKFLOW.md §3)

1. `./bin/ci-local` green
2. `prompts/cursor/done/2026-06-14-0715-empty-crm-mvr-bootstrap-create-on-deliver/` with `prompt.md` + `output.md`
3. Remove claimed file from `in-progress/` **and** ensure no duplicate remains in `next/`
4. **Do not commit or push** — tell Paul **"slice ready for review"**

---

## Exit criteria

- Step 2 create-on-deliver on no-seed network writes bind versions to demographic + professional storage
- Seeded CRM refresh + existing create-on-deliver tests still pass
- New smoke test covers categories-without-MVR → step 2 success path
- `./bin/ci-local` green