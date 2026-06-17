# DefaultSeedHandler generic — `rows[]`, seed grain, seed-bootstrap doc

> **READY** — Claim per `prompts/cursor/WORKFLOW.md` (move to `in-progress/` before starting).

**Priority:** After MVR generic vocabulary (`done/2026-06-18-1400-framework-mvr-generic-vocabulary/`). Makes the framework JSON seed path **grain- and MVR-neutral**; documents the three bootstrap patterns Paul locked (None / JSON→MVR / Custom).

**Parent:** `TODO.md` — “Non-person seed schemas”; [`docs/architecture.md`](../../../docs/architecture.md) § Seed bootstrap; June 2026 Paul thread on `DefaultSeedHandler` vs `LahmanSeedHandler`.

**Principles:**

- **Framework generic; networks specific** — `DefaultSeedHandler` has no `people` / `person`-preferring logic. CRM keeps `name` + `employer` **as MVR field names**, not as framework vocabulary.
- **No backward compatibility** — drop `people[]`, `load_seed_people`, `_load_seed_people`, and `resolve_seed_grain()`’s `"person"` preference. Update every caller and test in-repo; do not accept legacy keys.
- **`LahmanSeedHandler` unchanged** — custom pack handler; not a subclass of `DefaultSeedHandler`. Doc explains the relationship.
- **Breaking changes OK** — list in `output.md` for colleagues.

---

## Problem (posterity)

`DefaultSeedHandler` bind import is already MVR-generic (prior slice G9), but **seed file shape and grain selection** are still CRM-shaped:

| Residue | Location |
|---------|----------|
| `people[]` top-level key | `seed.json`, `load_seed_people`, `validate_seed_file`, tests |
| `resolve_seed_grain()` prefers `"person"` | `default_seed.py` |
| Error messages say `Seed people[i]` | `default_seed.py`, `create.py` |
| `load_seed_people` / `_load_seed_people` names | `default_seed.py`, `seed_import.py` |
| No standalone seed-bootstrap doc | scattered in `architecture.md`, plans, example READMEs |

Paul wants one doc covering **three bootstrap types**:

1. **None** — e.g. `empty-crm`: `DefaultSeedHandler` declared, **no** `seed.json` → 0 entities; growth from query-time binds.
2. **JSON → MVR map** — e.g. `crm`: `DefaultSeedHandler` reads `seed.json` `rows[]`; each row supplies values for the target grain’s `mvr.bind_fields`.
3. **Custom** — e.g. `baseball`: pack handler (`LahmanSeedHandler`) — warehouse ingest, multi-grain, `seed.source.json`, etc.

---

## Locked scope

| # | Decision |
|---|----------|
| S1 | **`seed.json` shape** — top-level object with **`rows`** array (not `people`). Each element is an object; keys are MVR bind field names for the bootstrap grain. No `id` in seed file (uuid assigned on import). |
| S2 | **`load_seed_rows`** — rename from `load_seed_people`; validate `rows[]` + non-empty values for all `bind_fields` of the target grain. Error text: `Seed rows[i]`, `'rows' array`. |
| S3 | **Bootstrap grain** — target grain = `network.json` → `bootstrap.seed_grain` when present, else `mvr.default_grain`. **Remove** `resolve_seed_grain()` and any hardcoded `"person"` preference. |
| S4 | **`BootstrapConfig`** — parse optional `bootstrap.seed_grain` (string, must exist in `mvr.grains`). Reject unknown grain at config load with clear error. |
| S5 | **`DefaultSeedHandler`** — unchanged protocol (`run` → `BootstrapResult`); uses S2–S3 internally. Docstrings: “default JSON seed handler”, not “people”. |
| S6 | **`network.seed_import`** — export `load_seed_rows` only; remove `load_seed_people` and `_load_seed_people`. Update `import_seed_file` / `count_seed_rows` docstrings (“rows”, not “people”). `count_seed_rows`: count `rows` length (structural parse OK without applied MVR when file missing manifest context). |
| S7 | **`validate_seed_file` (`create.py`)** — structural validation for `rows[]` (object root, list of objects). **Do not** require hardcoded `name` at create time (ontology may declare different MVR). Full bind-field validation remains in `load_seed_rows` at import when manifest is applied. |
| S8 | **CRM example** — `examples/networks/crm/seed.json` → `rows`; `prepare_seed.py` emits `rows`. Optional: add `"seed_grain": "person"` to CRM `network.json` bootstrap block (redundant with `default_grain` but documents the knob). |
| S9 | **`empty-crm`** — no `seed.json` in example tree (unchanged). Document as **None** type in new doc. |
| S10 | **New doc `docs/seed-bootstrap.md`** — canonical reference for the three types, manifest fields, handler resolution, file layout, CRM vs baseball examples, cross-link to `BootstrapHandler` protocol. |
| S11 | **Doc cross-links** — short pointer in `docs/architecture.md` § Seed bootstrap (replace `people[]` bullets with `rows[]` + link to `seed-bootstrap.md`); one line in `docs/onboarding.md`. |
| S12 | **Copy surfaces** — `src/main.py` CLI help, `src/network/introspection.py` policy strings: `rows[]` / bind fields, not `people[]`. |
| S13 | **Tests** — all fixtures `{"people": ...}` → `{"rows": ...}`; rename `test_load_seed_people_*` → `test_load_seed_rows_*`; add test that `bootstrap.seed_grain` overrides `default_grain` when they differ (stub manifest). CRM capstones / `./bin/smoke-crm-e2e` / `./bin/ci-local` green. |

---

## Read first

- `prompts/cursor/WORKFLOW.md`
- `src/network/bootstrap/handlers/default_seed.py`
- `src/network/bootstrap/config.py`
- `src/network/seed_import.py`
- `src/network/create.py` — `validate_seed_file`
- `src/network/bootstrap/handlers/resolve.py`, `protocol.py`
- `examples/networks/crm/seed.json`, `prepare_seed.py`, `network.json`
- `examples/networks/empty-crm/network.json`
- `examples/networks/baseball/network.json`, `bootstrap_handlers/lahman_seed.py`, `README.md`
- `tests/test_network_bootstrap.py`, `tests/test_network_create.py`, `tests/test_example_network.py`
- `docs/architecture.md` § Seed bootstrap
- `prompts/cursor/done/2026-06-18-1400-framework-mvr-generic-vocabulary/` — prior generic bind work

---

## Implement

### Handler & config

- Implement S1–S5 in `default_seed.py`.
- Extend `load_bootstrap_config` / `BootstrapConfig` for optional `seed_grain` (S4).
- Wire `DefaultSeedHandler.run` and `import_seed_rows` to resolved bootstrap grain.

### Seed import & create

- `seed_import.py` per S6.
- `validate_seed_file` per S7; ensure `create_network` dry-run `entities_bootstrapped` still works.

### Examples

- CRM `seed.json` + `prepare_seed.py` per S8.
- Do **not** change baseball handler logic; optional README one-liner pointing at `docs/seed-bootstrap.md`.

### Documentation

- Write `docs/seed-bootstrap.md` per S10. Suggested outline:

  ```markdown
  # Seed bootstrap

  ## Three patterns
  ### None (no seed fixture)
  ### JSON → MVR (`DefaultSeedHandler`)
  ### Custom pack handler

  ## Manifest (`network.json` → `bootstrap`)
  ## `seed.json` format (`rows[]`)
  ## Grain selection (`seed_grain` vs `default_grain`)
  ## Handler protocol (`BootstrapContext` / `BootstrapResult`)
  ## Examples (empty-crm, crm, baseball)
  ```

- Trim/update `architecture.md` and `onboarding.md` per S11 (avoid duplicating full content — link to new doc).

### Tests & verification

| Test area | Assert |
|-----------|--------|
| `test_network_bootstrap` | `rows[]`, `load_seed_rows`, optional `seed_grain` |
| `test_network_create` | invalid seed matches `'rows'`; create with seed still bootstraps |
| `test_example_network` | CRM seed uses `rows` |
| All other tests with `people` in seed JSON | Updated fixtures |
| `./bin/ci-local` | Green |
| `./bin/smoke-crm-e2e` | Green (if in CI path) |

---

## Scope boundaries (strict)

**May modify:**

- `src/network/bootstrap/` (handlers, config)
- `src/network/seed_import.py`, `src/network/create.py`
- `src/main.py`, `src/network/introspection.py` (copy only)
- `examples/networks/crm/` (`seed.json`, `prepare_seed.py`, optional `network.json` bootstrap field)
- `tests/`
- `docs/seed-bootstrap.md` (new), `docs/architecture.md` (seed section), `docs/onboarding.md` (one link)

**Do not modify:**

- `examples/networks/baseball/bootstrap_handlers/` (logic)
- `src/agents/`, query graph, MVR validation (done in prior slice)
- `TODO.md`
- `source_keys` / `playerID` bridge (future slice)
- Backward compat shims for `people[]`

---

## Explicit non-goals

- Renaming `seed.json` filename or `seed_bootstrap` actor kind
- New framework handler for “None” type (missing file + `DefaultSeedHandler` is sufficient)
- Baseball `source_keys` on `RegistryEntity`
- Changing `LahmanSeedHandler` to extend `DefaultSeedHandler`

---

## Exit criteria

| # | Criterion |
|---|-----------|
| E1 | No `people` key expectations in `src/network/bootstrap/handlers/default_seed.py` or `load_seed_people` symbol in repo |
| E2 | CRM `seed.json` uses `rows`; refresh imports 15 entities |
| E3 | `docs/seed-bootstrap.md` documents all three bootstrap types with examples |
| E4 | `bootstrap.seed_grain` honored when set; `default_mvr_grain` when omitted |
| E5 | `./bin/ci-local` green |
| E6 | `output.md` lists breaking changes (`people[]` → `rows[]`, renamed APIs, removed `_load_seed_people`) |

---

## Governance (mandatory)

- **Do not edit `TODO.md`.**
- **For Grok + Paul** in `output.md`: suggest marking TODO “Non-person seed schemas” done; note any external doc/README follow-ups.

## When finished

Per `prompts/cursor/WORKFLOW.md` — no commit/push.

**Suggested commit message:**

```
refactor(bootstrap): generic DefaultSeedHandler rows[] and seed doc

Replace people[] with rows[]; bootstrap grain from manifest seed_grain
or default_grain; add docs/seed-bootstrap.md for three bootstrap patterns.
```