# Review: Identity vocabulary rename — fix framework specialists

**Verdict: Approved**

**Reviewer:** Grok (June 2026)  
**Parent:** [`../2026-06-10-entity-identity-vocabulary-rename/review.md`](../2026-06-10-entity-identity-vocabulary-rename/review.md) (B1)

---

## Summary

Fix closes the only blocking nit from the parent review. All four framework fallback specialists under `src/agents/specialists/` now use `IdentityRecord` / `identity_record`. New smoke tests guard on-disk source and `import_module` single-match invoke. README table updated.

**Verified independently:** ruff clean, **302 passed** (+2 tests), no `SeedRecord` / `seed_record` in `src/` or `tests/` (except negative assertions in new test).

---

## Checklist

| Item | Status |
|------|--------|
| B1 — regen `contact`, `demographic`, `professional`, `social` specialists | Pass |
| On-disk vocab smoke test | Pass |
| `import_module` single-match invoke (no ImportError) | Pass |
| README `IdentityRecord` | Pass |
| `rg` clean under `src/agents/specialists/` | Pass |

---

## Combined program verdict

**Parent + fix: Approved — ready to commit** (single squash commit recommended).

Suggested message:

```
Breaking: rename SeedRecord to IdentityRecord and seed_* state fields.

Registry identity vocabulary; MCP schema identity-record; matched_records
canonical; regen framework specialists.
```

**Post-commit:** fresh `thread_id` for demos; MCP clients update schema URI. Next Cursor slice: `network-create-optional-seed`.