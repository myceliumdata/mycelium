# Output: MCP slice 1 fixup — framework specialist modules entity rename

## Summary

Regenerated the four **framework specialist modules** under `src/agents/specialists/` from the updated `specialist_agent.py.j2` template (slice 1 vocabulary: `entity_key`, `matched_records`). The files were missing from the repo (only `base.py` remained); registry fallback `import_module("agents.specialists.<name>")` would have failed for attribute queries.

Added smoke regression tests in `tests/test_specialist_entity_vocab.py`.

## Files changed

| File | Change |
|------|--------|
| `src/agents/specialists/contact_specialist.py` | Regenerated (entity vocab) |
| `src/agents/specialists/demographic_specialist.py` | Regenerated (new) |
| `src/agents/specialists/professional_specialist.py` | Regenerated (new) |
| `src/agents/specialists/social_specialist.py` | Regenerated (new) |
| `tests/test_specialist_entity_vocab.py` | New — 4 parametrized smoke tests |

## Verification

```text
uv run pytest -m smoke -q tests/test_specialist_entity_vocab.py tests/test_entity_rename.py tests/test_specialist_sync_research.py  → 14 passed
uv run ruff check src/agents/specialists tests/test_specialist_entity_vocab.py  → clean
grep person_key|matched_persons src/agents/specialists/*.py  → no matches
```

### Manual CLI (attribute query)

```bash
uv run mycelium query --entity-key "Nichanan Kesonpat" --attributes email --network-dir examples/networks/crm
```

In review environment: query progressed into specialist/research path (no `AttributeError` on `entity_key`); failed later on network proxy when LLM keys are set. With research unavailable, specialists return pending/non-core responses as before.

## Unblocks

MCP slice 2 (`describe_network`, onboarding surface).
