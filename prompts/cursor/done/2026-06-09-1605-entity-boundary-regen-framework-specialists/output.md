# Output — Entity boundary fixup: regenerate framework specialists (`1605`)

## Summary

Slice 7 review blocking nit (Q7b): regenerated all four **framework fallback** specialist modules under `src/agents/specialists/` from the current `specialist_agent.py.j2` template. Modules now use `entity_id` / `bind` / `_research_context` — no `context.seed` references. Unblocks Grok commit of `1600` + `1605` together.

## Files changed

| File | Change |
|------|--------|
| `src/agents/specialists/contact_specialist.py` | Regenerated |
| `src/agents/specialists/demographic_specialist.py` | Regenerated |
| `src/agents/specialists/professional_specialist.py` | Regenerated |
| `src/agents/specialists/social_specialist.py` | Regenerated |
| `tests/test_specialist_entity_vocab.py` | `import_module` bind-context test + on-disk no-seed scan |

## Verification

```bash
uv run pytest tests/test_specialist_entity_vocab.py -m smoke -q   # 7 passed
uv run pytest -m smoke -q                                         # 210 passed
```

- `ctx.get("seed")` / `context.get("seed")` → no matches in `src/agents/specialists/*_specialist.py`
- `agents.specialists.demographic_specialist` resolves identity from `bind` without `seed` key

## For Grok + Paul

- **Commit `1600` + `1605` together** when approved (per governance).
- Slice 8 (`1700`) can proceed after combined commit.

## Exit criteria

- [x] Four framework specialists regenerated from canonical template
- [x] No `context.seed` in framework specialist modules
- [x] Smoke tests for `import_module` bind path
- [x] Full smoke green (210)
