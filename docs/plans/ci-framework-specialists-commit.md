# CI fix — commit framework fallback specialists

**Status:** Shipped (June 2026)  
**Trigger:** CI smoke failed on `538867e` / `650cd7d` — `test_specialist_entity_vocab` expects four modules under `src/agents/specialists/` that are **gitignored** and absent on GitHub runners.

## Problem

Identity rename fix (`entity-identity-vocabulary-rename-fix`) added smoke tests:

- `test_framework_specialists_on_disk_use_identity_record_vocab`
- `test_framework_demographic_specialist_import_module_single_match`

These require on-disk `contact_specialist.py`, `demographic_specialist.py`, `professional_specialist.py`, `social_specialist.py`. Local dev has them (regenned manually); **CI clone does not**.

Historical slices (`1350`, `1605`, identity fix) treated these as gitignored on-disk contract — that pattern breaks CI now that tests assert committed presence.

## Fix (recommended)

**Commit the four framework fallback specialists** and **remove** them from `.gitignore`.

- Per-network specialists remain under `<network_root>/specialists/` (unchanged).
- Framework path `src/agents/specialists/` is the `import_module("agents.specialists.<name>")` fallback for CRM registry entries — same role as `examples/networks/crm/specialists/contact_specialist.py` (reference copy).

When `specialist_agent.py.j2` changes, regen these four and commit (document one line in `src/agents/specialists/README` or comment in `.gitignore` removal note — optional).

## Out of scope

- CI workflow changes (not needed once files are tracked)
- Regenerating all network-root specialists
- Template changes

## Verify

```bash
git check-ignore -v src/agents/specialists/demographic_specialist.py  # should fail (not ignored)
uv run pytest -m smoke tests/test_specialist_entity_vocab.py -q
LANGCHAIN_TRACING_V2=false uv run pytest -m smoke -q
```