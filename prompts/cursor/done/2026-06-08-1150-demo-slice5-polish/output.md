# Output: Demo slice 5 — polish (pre hands-on test)

## Fixes applied

| # | Fix | Files |
|---|-----|-------|
| 1 | Plain JSON for `network status --json` (`print`, not Rich) | `src/main.py` |
| 2 | `test_status_cli_json` parses JSON; `NO_COLOR=1` | `tests/test_network_status.py` |
| 3 | Specialists empty-state when ontology without storage | `src/network/introspection.py`, test |
| 4 | `network_configure_hint` in `health_check` info | `src/mycelium_mcp/server.py`, `tests/test_network_polish.py` |
| 5 | `allow_no_default` only on `--no-default` | `src/network/example.py`, `tests/test_example_network.py` |
| 6 | Plan docs `refresh-example-network` | `docs/plans/networks-terminology.md`, `networks-phase5.md` |

Slice 2 `review.md` issues 1–3 marked **fixed** (1150).

## Verification

```text
uv run pytest -m smoke -q  → 119 passed
uv run ruff check src tests bin/  → clean
uv run mycelium network status --network-dir examples/networks/crm --json | jq .seed_people_count  → 15
```

## Ready for hands-on test

```bash
./bin/refresh-example-network crm --yes
uv run mycelium network status --network crm
uv run mycelium query --person-key "Nichanan Kesonpat" --attributes email --thread-id demo-$(date +%s)
uv run mycelium network status --network crm --person "Nichanan Kesonpat"
```

## Unblocks

Paul + Grok hands-on test; then Demo slice 3 (admin daemon).
