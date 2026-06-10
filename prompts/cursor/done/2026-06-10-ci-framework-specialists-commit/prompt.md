# Task: CI fix — commit framework fallback specialists

> **BLOCKING CI** — Smoke fails on GitHub: missing gitignored `src/agents/specialists/*_specialist.py`. Move to `in-progress/` before starting.

**Read first:**

- [`docs/plans/ci-framework-specialists-commit.md`](../../docs/plans/ci-framework-specialists-commit.md)
- [`tests/test_specialist_entity_vocab.py`](../../tests/test_specialist_entity_vocab.py) (failing tests)
- [`src/agents/factory/templates/specialist_agent.py.j2`](../../src/agents/factory/templates/specialist_agent.py.j2) (canonical)
- [`prompts/cursor/done/2026-06-10-entity-identity-vocabulary-rename-fix/output.md`](../done/2026-06-10-entity-identity-vocabulary-rename-fix/output.md)

**Depends on:** `main` at `650cd7d` (identity rename + network create v2 shipped).

---

## Objective

Make CI smoke green by **tracking** the four framework fallback specialist modules in git. Fresh clones (including GitHub Actions) must have `agents.specialists.demographic_specialist` importable without a local regen step.

---

## Requirements

### 1. Stop gitignoring framework specialists

In [`.gitignore`](../../.gitignore), **remove** (or replace with a comment):

```
src/agents/specialists/*_specialist.py
```

Do **not** change ignore rules for `<network_root>/specialists/` or other runtime paths.

### 2. Regenerate and commit four modules

Ensure these exist, match current template (`IdentityRecord` / `identity_record`, `entity_id`/`bind` — no `SeedRecord`):

- `src/agents/specialists/contact_specialist.py`
- `src/agents/specialists/demographic_specialist.py`
- `src/agents/specialists/professional_specialist.py`
- `src/agents/specialists/social_specialist.py`

Use `AgentFactory.render_specialist_py` with the same categories/agents as CRM six-pack subset (contact, demographic, professional, social). Copy metadata from existing on-disk files or prior slice `1605` if present locally.

**Add files to git** (`git add` the four paths — they must appear in the commit).

### 3. Brief maintainer note (one place only)

Add a short comment at top of `.gitignore` where the line was removed, **or** a 2-line note in [`src/agents/specialists/base.py`](../../src/agents/specialists/base.py) docstring:

> Framework `*_specialist.py` modules are **committed** (import_module fallback + CI). Regenerate from template when `specialist_agent.py.j2` changes.

Do not add a new markdown doc.

### 4. Tests

Existing smoke tests must pass unchanged:

- `test_framework_specialists_on_disk_use_identity_record_vocab`
- `test_framework_demographic_specialist_import_module_single_match`

No test edits unless a category name in regen metadata was wrong.

---

## Out of scope

- `.github/workflows/ci.yml` changes
- `TODO.md`
- Identity rename / network create code
- Admin UI

---

## Governance (mandatory)

- **Do not edit `TODO.md`.**
- **Do not create `review.md`.**
- In `output.md`, note CI failure resolved; Grok will re-run `gh run list` after commit.
- **Do not commit** before Grok + Paul review.

---

## Verify

```bash
git check-ignore src/agents/specialists/demographic_specialist.py; test $? -ne 0
rg 'SeedRecord|seed_record' src/agents/specialists/
uv run ruff check src tests
LANGCHAIN_TRACING_V2=false uv run pytest -m smoke -q
```

Report smoke count in `output.md`.

---

## Suggested commit message

```
Fix CI: commit framework fallback specialist modules.

Track src/agents/specialists/*_specialist.py for import_module fallback;
remove gitignore so smoke tests pass on fresh clone.
```
