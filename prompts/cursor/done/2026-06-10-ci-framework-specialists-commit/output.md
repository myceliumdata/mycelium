# CI fix — commit framework fallback specialists

## Summary

CI smoke failed on fresh clones because `src/agents/specialists/*_specialist.py` was gitignored while tests assert on-disk presence. Removed gitignore rule, regenerated four framework modules from current template, and staged them for commit.

## Changes

| File | Change |
|------|--------|
| `.gitignore` | Removed `*_specialist.py` ignore; added maintainer comment |
| `src/agents/specialists/base.py` | Docstring note: committed modules, regen when template changes |
| `src/agents/specialists/contact_specialist.py` | Added (regenerated) |
| `src/agents/specialists/demographic_specialist.py` | Added (regenerated) |
| `src/agents/specialists/professional_specialist.py` | Added (regenerated) |
| `src/agents/specialists/social_specialist.py` | Added (regenerated) |

All four use `IdentityRecord` / `identity_record` / `entity_id`+`bind` (no `SeedRecord`).

## Staging

```bash
git add src/agents/specialists/{contact,demographic,professional,social}_specialist.py .gitignore src/agents/specialists/base.py
```

Six paths staged; **not committed** per governance.

## Verification

```bash
git check-ignore src/agents/specialists/demographic_specialist.py; test $? -ne 0   # not ignored (exit 1)
rg 'SeedRecord|seed_record' src/agents/specialists/   # no matches
uv run ruff check src tests   # All checks passed
LANGCHAIN_TRACING_V2=false uv run pytest -m smoke -q   # 279 passed, 26 deselected in 11.75s
```

## For Grok + Paul

- **CI failure resolved** — `test_framework_specialists_on_disk_use_identity_record_vocab` and `test_framework_demographic_specialist_import_module_single_match` pass on fresh tree once committed.
- Re-run `gh run list` after Paul commits this slice.
- Suggested commit message in `prompt.md`.
