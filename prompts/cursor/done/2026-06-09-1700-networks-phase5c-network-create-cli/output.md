# Output: Networks Phase 5c — `mycelium network create` CLI

## Summary

Implemented `mycelium network create` — single command to stand up a custom-domain network with LLM-generated skeleton ontology, seed copy, specialist modules, registry registration, and MCP snippet output.

## Files changed

| File | Change |
|------|--------|
| `src/network/create.py` | New — `create_network()`, validation, artifact writes |
| `src/main.py` | `network create` subcommand + flags |
| `src/network/__init__.py` | Export `create_network`, `CreateNetworkResult` |
| `tests/test_network_create.py` | 6 smoke + 1 full integration test |

## Network name rules

Registry names must match `^[a-z][a-z0-9_]*$` (lowercase letter first; letters, digits, underscores only). Examples: `wheat_farm`, `prm_crm`, `query_net`.

## Verification

```bash
uv run pytest -m smoke -q tests/test_network_create.py   # 6 passed
uv run pytest -m full -q tests/test_network_create.py    # 7 passed
uv run pytest -m smoke -q                                 # 102 passed
uv run ruff check src tests bin/                          # clean
```

## Automated test checklist

| Test | Status |
|------|--------|
| Dry run (no writes) | **PASS** |
| Happy path artifacts + registry | **PASS** |
| Existing `network.json` without `--force` | **PASS** |
| Invalid seed before ontology | **PASS** |
| `--force` overwrite | **PASS** |
| MCP snippet contains `MYCELIUM_NETWORK_ROOT` | **PASS** |
| Integration: custom ontology query (not CRM six) | **PASS** |

## Manual checklist (Paul — after slice `1800`, not merge blocker)

| Step | Command / check | Pass? |
|------|-----------------|-------|
| 1 | `cp .env.example .env` and set `OPENAI_API_KEY` | ☐ |
| 2 | Prepare seed JSON with `people` array (name + optional employer) | ☐ |
| 3 | `uv run mycelium network create my_test --root /abs/path --seed /path/seed.json --prompt "Describe your domain..." --display-name "My Test" --default` | ☐ |
| 4 | Confirm `<root>/network.json`, `categories.json`, `agent_registry.json`, `seed.json`, `specialists/*.py` exist | ☐ |
| 5 | `uv run mycelium network list` shows `my_test` (default) | ☐ |
| 6 | `uv run mycelium query --person-key "<name from seed>" --attributes <example from categories>` | ☐ |
| 7 | MCP snippet from create output works in Claude Desktop (optional) | ☐ |
| 8 | `--dry-run` prints ontology preview without writes | ☐ |

## Next queue item

`prompts/cursor/next/2026-06-09-1750-networks-phase5-polish.md` (if present) or `2026-06-09-1800-networks-phase5d-docs.md`
