# Task: Networks Phase 5d — Phase 5 documentation + roadmap closure

**Read these first (mandatory):**
- `prompts/cursor/WORKFLOW.md`
- `docs/plans/networks-phase5.md`
- `prompts/cursor/done/2026-06-09-1700-networks-phase5c-network-create-cli/output.md` (what shipped)
- `prompts/cursor/done/2026-06-09-1760-networks-remove-reset-mycelium/output.md` (replacement workflows for docs)
- `docs/plans/networks-terminology.md`, `TODO.md`, `README.md`, `docs/architecture.md`

**Depends on:** 5c (`1700`), polish (`1750`), and remove reset (`1760`) in `prompts/cursor/done/`.

---

## Objective

Close the **documentation loop** for Networks Phase 5: users and future agents can discover `network create`, understand ontology vs classification, and see accurate roadmap status.

No runtime behavior changes unless a doc lie requires a one-line comment fix.

**Testing policy:** Paul defers hands-on testing until **after this slice**. Automated pytest is sufficient for merge. Shipping to `main` happens after Grok + Paul review all four Phase 5 slices (+ any polish follow-ups).

---

## Updates required

### `README.md` — **first priority**

A prominent **testing disclaimer** must remain at the **very top** of `README.md` (immediately under the `# Mycelium` heading), stating:

- Code is **not yet hands-on tested by Paul**
- Phase 5 slices `1500`–`1800` may be on `main` with CI green but **unverified by maintainer**
- Readers should treat the branch as implement-but-unverified until Paul removes the notice after manual testing

Then add Phase 5 quick-start content (below).

### `docs/plans/networks-terminology.md`

- Status line: Phase 5 queued → **delivered** (after 5a–5c)
- Phase 5 section: align with `docs/plans/networks-phase5.md` (skeleton ontology, `specialists/` layout)
- **Resolve open questions:**
  - #1 config location → decided (remove or strike)
  - #4 generated specialists → `<network_root>/specialists/`
  - #5 Phase 5 queue → done
- Fix table inconsistency: inter-network handoff = **Phase 6** (not Phase 5)
- Standard layout diagram: add `specialists/`

### `docs/plans/networks-phase5.md`

- Status → **Delivered** (June 2026) with slice IDs `1500`–`1800`

### `TODO.md`

- Mark **Network launch v1 (Phase 5)** and **Custom specialists per network** complete (with slice refs)
- Update cursor queue line → Phase 5 done; next items unchanged
- Add explicit deferred items if missing:
  - Per-network LangSmith projects (design discussion)
  - Non-person seed schemas
  - `network regen-ontology`
- `Last updated` date

### `README.md` (continued)

- Quick start: document **`mycelium network create`** alongside `copy-example-network`
- When to use which:
  - **CRM example** → `bin/copy-example-network`
  - **Custom domain** → `network create` with `--prompt`
- Minimal example command (fake paths OK)
- Roadmap blurb: Phase 5 complete

### `docs/architecture.md`

- Networks section: mention `<network_root>/specialists/` and skeleton ontology at create
- One sentence: classification still grows `attribute_map` lazily at query time

### `docs/full-code-walkthrough.md` (if it lists Phase 5 as future)

- Brief update only — do not rewrite the walkthrough

---

## Verification

- Grep docs for stale "Phase 5 not queued" / "before Phase 5" gate language — fix stragglers in files above
- `uv run pytest -m smoke -q` (sanity; no code changes expected)

---

## Scope boundaries

**May modify:** docs listed above only

**Out of scope:** new features, test changes (unless fixing a broken doc reference), query-as-seed implementation

---

## Deliverables

`prompts/cursor/done/2026-06-09-1800-networks-phase5d-docs/` with `prompt.md`, `output.md` (checklist of doc files touched).