# CLI delivery_id network hints — output

## Done

| Item | Change |
|------|--------|
| **A** | Step-1 stderr hint with `--network` + `delivery_id` (+ `--quote-id` when quoted) |
| **B** | Cross-network / expired / fallback messages on step-2 deliver miss |
| **Helper** | `src/network/delivery_hints.py` — `format_step2_cli_hint`, `delivery_not_found_message`, `find_delivery_on_other_network` |
| **Wiring** | `src/main.py` (stderr after lookup_resolved/quote_required); `src/agents/dispatch.py` (deliver not_found only) |
| **Tests** | `tests/test_delivery_network_hints.py` — 5 smoke tests |
| **Docs** | `README.md` step-2 examples use `--network crm`; live-gate doc footnote |

## Verification

```text
./bin/ci-local                                    # 605 smoke passed
uv run pytest tests/test_delivery_network_hints.py -m smoke -q  # 5 passed
```

## Example messages

**Step-1 stderr:**
```text
Step 2 (same network): uv run mycelium query --network baseball --delivery-id d_abc123
```

**Cross-network step-2 miss:**
```text
No valid delivery for 'd_…' on network 'crm'.
This delivery_id was issued on network 'baseball'.
Retry: uv run mycelium query --network baseball --delivery-id d_…
```

## For Grok + Paul

- CLI-only UX; MCP unchanged.
- Manual check: step 1 with `--network baseball`, step 2 without `--network` on default CRM → B message names baseball.
- Next in queue: `2026-06-20-1995-baseball-fresh-derive-default-on.md`

## Suggested commit message

```
feat(cli): delivery_id network hints for two-step queries
```
