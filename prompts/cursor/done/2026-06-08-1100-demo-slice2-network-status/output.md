# Output: Demo slice 2 — `mycelium network status`

## Summary

Added read-only **`mycelium network status`** with shared **`src/network/introspection.py`** for CLI and future admin daemon (slice 3).

## Files changed

| File | Change |
|------|--------|
| `src/network/introspection.py` | New — `build_network_status()`, dataclasses, human + JSON formatters |
| `src/main.py` | `network status` subcommand |
| `src/network/__init__.py` | Export introspection API |
| `tests/test_network_status.py` | 4 smoke + 1 full |
| `README.md`, `examples/networks/crm/README.md` | Status usage |
| `TODO.md` | Slice 2 marked done |

## Sample output

### Empty network (seed only)

```text
Network: crm (CRM example)
Root: .../examples/networks/crm
Seed: 15 people
Ontology: not created yet — run a query to bootstrap categories.json
Specialists: none registered
```

### Populated (fixture with categories + contact storage)

```text
Network: network
Root: /tmp/.../populated
Seed: 15 people
Ontology: 6 categories
  contact: agent=contact_specialist examples=5
  ...
Specialists:
  contact_specialist  category=contact  module=no  records=1  fields=email
    status counts: found=1 pending=0 na=0
  ...
```

### JSON (`--json`)

```json
{
  "network_name": "crm",
  "network_root": "/path/to/root",
  "display_name": "CRM example",
  "seed_people_count": 15,
  "ontology_present": false,
  "ontology_message": "not created yet — run a query to bootstrap categories.json",
  "categories": [],
  "specialists": [],
  "person_key": null,
  "person_matches": 0,
  "person_fields": []
}
```

## Verification

```text
uv run pytest -m smoke -q tests/test_network_status.py  → 4 passed
uv run pytest -m smoke -q  → 116 passed
uv run ruff check src/network/introspection.py src/main.py tests/test_network_status.py  → clean
uv run mycelium network status --network-dir examples/networks/crm  → OK
```

## Unblocks

Demo slice 3 (admin daemon reuses `introspection.py`).
