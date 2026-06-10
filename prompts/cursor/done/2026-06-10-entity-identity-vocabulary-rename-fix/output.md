# Identity vocabulary rename — fix framework specialists

## Summary

Closed review **B1**: regenerated all four framework fallback specialists under `src/agents/specialists/` from the updated `specialist_agent.py.j2` template. Modules now use `IdentityRecord` / `identity_record` on the single-match return path (no lazy `SeedRecord` import). Added smoke guards and README table fix.

## Files changed

| File | Change |
|------|--------|
| `src/agents/specialists/contact_specialist.py` | Regenerated |
| `src/agents/specialists/demographic_specialist.py` | Regenerated |
| `src/agents/specialists/professional_specialist.py` | Regenerated |
| `src/agents/specialists/social_specialist.py` | Regenerated |
| `tests/test_specialist_entity_vocab.py` | On-disk vocab scan + `import_module` single-match invoke |
| `README.md` | Models table: `IdentityRecord` |

**Note:** `src/agents/specialists/*_specialist.py` is gitignored (on-disk contract for `import_module` fallback, same as slices `1350` / `1605`).

## Verification

```bash
uv run ruff check src tests                    # All checks passed
rg 'SeedRecord|seed_records|seed_record|schema/seed-record' src/agents/specialists/   # no matches
rg 'SeedRecord|seed_records|seed_record|schema/seed-record' src/ tests/               # no matches
uv run pytest tests/test_specialist_entity_vocab.py -m smoke -q   # 9 passed
LANGCHAIN_TRACING_V2=false uv run pytest -q   # 302 passed in 331.07s
```

## For Grok + Paul

- **B1 closed** — single-match specialist path no longer raises `ImportError` via framework modules.
- **Parent slice + fix ready for combined Grok re-review and commit** (squash or amend per `prompt.md`).
- Suggested combined commit message in parent `prompt.md`; fix line: `Fix: regen framework specialists for IdentityRecord rename.`
