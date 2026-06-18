# Baseball committed ontology (M1a) — schema-informed routing

> **READY** — Claim per `prompts/cursor/WORKFLOW.md` (move to `in-progress/` before starting).

**Priority:** **Before** any warehouse specialist or computation-provenance slice (M1b). Unblocks supervisor `requested_attributes` → category → `assigned_agent` for baseball.

**Parent:** [`docs/plans/conversations/2026-06-18-computation-centric-provenance.md`](../../docs/plans/conversations/2026-06-18-computation-centric-provenance.md); [`docs/plans/baseball-example-program.md`](../../docs/plans/baseball-example-program.md) checklist #3 (table→specialist routing — committed v1, not auto-gen).

**Principles:**

- **Framework generic** — install committed pack ontology by convention; no Lahman strings in `src/agents/supervisor.py` or classification engine.
- **No specialist business logic** — generated/stub specialists may return `empty`/`pending`; this slice proves **routing only**.
- **CRM unchanged** — CRM / empty-crm refresh and bootstrap still use sample CRM taxonomy when no pack ontology is present.
- **Do not edit `TODO.md`.**

---

## Objective

Ship a **fixed, schema-informed** `categories.json` for the baseball example pack and wire refresh/bootstrap so live baseball roots load it (instead of CRM `sample-categories.json`). Add tests proving step-2 classification routes baseball attributes to baseball specialists, not `professional_specialist`.

---

## Locked ontology (commit verbatim — adjust only if validation fails)

**File:** `examples/networks/baseball/categories.json`

Derived from Lahman 2025 schema pass ([`baseball-example-program.md`](../../docs/plans/baseball-example-program.md) § Lahman schema): parallel player fact families + team-season facts + MVR bind fields. **No CRM categories** (`contact`, `social`, `professional`, …).

```json
{
  "version": "1.0",
  "last_updated": "2026-06-19T00:00:00+00:00",
  "model_used": "committed-pack-v1",
  "ontology_pack": "baseball",
  "categories": {
    "player_identity": {
      "description": "Player registry bind fields (display name and debut-season disambiguator).",
      "assigned_agent": "player_identity_specialist",
      "examples": ["player", "debut_team", "debut_year"]
    },
    "team_identity": {
      "description": "Fan-facing team registry bind field (full canonical city+name label).",
      "assigned_agent": "team_identity_specialist",
      "examples": ["team"]
    },
    "bio": {
      "description": "Player biographical facts from Lahman People (and supplemental web research later).",
      "assigned_agent": "bio_specialist",
      "examples": [
        "birth_date",
        "birth_city",
        "birth_country",
        "death_date",
        "height",
        "weight",
        "bats",
        "throws",
        "debut",
        "final_game"
      ]
    },
    "batting": {
      "description": "Player batting statistics and career batting derivatives (Lahman Batting).",
      "assigned_agent": "batting_specialist",
      "examples": [
        "career_hr",
        "career_rbi",
        "career_hits",
        "career_avg",
        "career_sb",
        "home_runs",
        "rbi",
        "batting_average",
        "at_bats",
        "games"
      ]
    },
    "pitching": {
      "description": "Player pitching statistics and career pitching derivatives (Lahman Pitching).",
      "assigned_agent": "pitching_specialist",
      "examples": [
        "career_wins",
        "career_losses",
        "career_era",
        "career_strikeouts",
        "career_saves",
        "wins",
        "era",
        "strikeouts",
        "walks",
        "games_pitched"
      ]
    },
    "team_season": {
      "description": "Year-scoped team facts (Lahman Teams): standings, park, attendance.",
      "assigned_agent": "team_season_specialist",
      "examples": [
        "season_wins",
        "season_losses",
        "finish_rank",
        "park",
        "attendance",
        "runs_scored",
        "runs_allowed"
      ]
    }
  },
  "attribute_map": {
    "player": "player_identity",
    "debut_team": "player_identity",
    "debut_year": "player_identity",
    "team": "team_identity",
    "birth_date": "bio",
    "birth_city": "bio",
    "birth_country": "bio",
    "death_date": "bio",
    "height": "bio",
    "weight": "bio",
    "bats": "bio",
    "throws": "bio",
    "debut": "bio",
    "final_game": "bio",
    "career_hr": "batting",
    "career_rbi": "batting",
    "career_hits": "batting",
    "career_avg": "batting",
    "career_sb": "batting",
    "home_runs": "batting",
    "rbi": "batting",
    "batting_average": "batting",
    "at_bats": "batting",
    "games": "batting",
    "career_wins": "pitching",
    "career_losses": "pitching",
    "career_era": "pitching",
    "career_strikeouts": "pitching",
    "career_saves": "pitching",
    "wins": "pitching",
    "era": "pitching",
    "strikeouts": "pitching",
    "walks": "pitching",
    "games_pitched": "pitching",
    "season_wins": "team_season",
    "season_losses": "team_season",
    "finish_rank": "team_season",
    "park": "team_season",
    "attendance": "team_season",
    "runs_scored": "team_season",
    "runs_allowed": "team_season"
  }
}
```

**Naming note:** use `birth_date` not `bio` as an attribute key — CRM sample maps `bio` → `professional`; baseball biographical attrs are explicit Lahman-shaped names.

**Deferred categories (do not add in this slice):** `fielding`, `franchise`, `awards`, `appearances`, `salaries`.

---

## Problem (today)

- `examples/networks/baseball/README.md` — live roots get CRM-copy taxonomy via `ensure_categories_for_mvr_bind` → `sample-categories.json`; `team` maps to `professional`.
- `copy_example_network` **skips** `categories.json` (`_SKIP_NAMES` in `src/network/example.py`).
- `career_hr` would classify to `unknown` or wrong CRM category.

---

## Implement

### 1 — Committed pack file

Add `examples/networks/baseball/categories.json` (locked JSON above).

### 2 — Generic pack ontology install (framework)

Add a small module (e.g. `src/network/pack_ontology.py`) or extend `src/network/category_mvr_bootstrap.py` with:

- `is_pack_ontology(categories_path) -> bool` — true when JSON has non-empty string `ontology_pack`.
- `install_pack_ontology_from_example(example_name: str, paths: NetworkPaths) -> bool` — if `examples/networks/<name>/categories.json` exists, copy to `paths.categories_path`, then:
  - `ensure_mvr_fields_in_category_tree` for manifest bind fields (player/debut_team/debut_year/team).
  - Build/register agents from categories (reuse logic from `network/create.py` — `_write_agent_registry` / agent list from `assigned_agent` per category).
  - Render stub `specialists/*_specialist.py` via `AgentFactory.render_specialist_py` (same as `network create`) when missing — **framework template is fine** for M1a.
- `reset_category_tree()` + `get_category_tree()` after install.

**`ensure_categories_for_mvr_bind` behavior:**

- If `paths.categories_path` is already a pack ontology (`ontology_pack` set) and maps all required MVR bind fields → **do not** replace with CRM sample; only merge missing bind fields.
- Else — existing CRM sample / merge behavior unchanged.

### 3 — Refresh + bootstrap hooks

- **`refresh_example_network`** (full and `--sync-only`): after `copy_example_network`, call `install_pack_ontology_from_example(name, paths)` when example pack has `categories.json`.
- **`run_network_bootstrap`**: after paths applied, call install if pack file exists at example dir **or** if live root already has pack ontology — ensure categories loaded before handler (order: install/ensure categories → registry reset → handler). Avoid double-wipe on full refresh: install runs on copied/live root post-copy in refresh path; bootstrap should respect existing pack ontology.

Do **not** remove `categories.json` from global `_SKIP_NAMES` without guarding CRM — prefer explicit `install_pack_ontology_from_example` over copying runtime artifacts blindly.

### 4 — Remove baseball → CRM fallback footgun (generic)

In `category_mvr_bootstrap.py`, `EXAMPLE_BIND_FIELD_CATEGORY_FALLBACK` maps `team` → `professional`. Pack ontology install must override this for baseball. **Do not** add baseball-specific keys to that dict; pack file + install path is the fix.

### 5 — Tests

Add `tests/test_baseball_pack_ontology.py` (or extend `tests/test_example_network.py`):

| Test | Assert |
|------|--------|
| Pack file validates | `CategoryTreeData.model_validate` on committed JSON |
| Refresh fixture installs ontology | Minimal baseball fixture root gets `ontology_pack: baseball` |
| `career_hr` classifies | category `batting`, agent `batting_specialist` |
| `birth_date` classifies | category `bio`, agent `bio_specialist` |
| `team` bind classifies | category `team_identity`, not `professional` |
| CRM refresh unchanged | CRM example refresh still CRM taxonomy (no `ontology_pack`) |

Extend `bin/smoke-baseball-e2e` **lightly** if cheap: after player resolve, step-2 query with `requested_attributes: ["career_hr"]` asserts supervisor routes to `batting_specialist` (audit_log or `response.debug` / classifications) — **outcome may be `found` with empty/pending attrs**; routing is the gate.

### 6 — Docs (task-scoped)

Update `examples/networks/baseball/README.md` — committed ontology, categories table, note that specialists are stubs until M1b.

---

## Non-goals

- Warehouse reads, computation provenance, dataset manifest.
- Auto-generated ontology from warehouse introspection.
- Fielding / franchise / awards categories.
- Changing CRM `sample-categories.json` or embedded `_SEED_CATEGORIES` (baseball live roots must not depend on those).
- `TODO.md` edits.

---

## Read first

- `prompts/cursor/WORKFLOW.md`
- [`docs/plans/conversations/2026-06-18-computation-centric-provenance.md`](../../docs/plans/conversations/2026-06-18-computation-centric-provenance.md)
- `src/network/example.py`, `src/network/category_mvr_bootstrap.py`, `src/network/bootstrap/run.py`
- `src/network/create.py` — `_write_agent_registry`, `_render_specialists`
- `src/agents/supervisor.py` — `_classify_requested_attributes`
- `examples/networks/baseball/network.json`, `guide.md`

---

## Verification

```bash
./bin/ci-local
uv run pytest tests/test_baseball_pack_ontology.py -q
./bin/smoke-baseball-e2e
```

---

## For Grok + Paul (output.md)

- Mark M1a done in TODO when approved.
- M1b next: first warehouse specialist + computation-centric provenance writer.
- Note whether full Lahman re-bootstrap required on existing `~/mycelium-networks/baseball` roots (likely `--sync-only` or refresh to pick up ontology).

**Suggested commit message:** `baseball: committed pack ontology (M1a) + refresh install`