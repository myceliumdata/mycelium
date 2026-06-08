# Output: Demo status output — scannable default + `--verbose`

## Summary

Default human output of **`mycelium network status`** is now a **demo-scannable** layout (✅/❌, category slugs, abbreviated ontology examples). The prior debug layout lives behind **`--verbose`**. **`--json`** unchanged (additive `CategorySummary.examples` field).

## Files changed

| File | Change |
|------|--------|
| `src/network/introspection.py` | `format_status_demo()`, `format_status_verbose()`, `format_category_examples()`; `CategorySummary.examples` |
| `src/main.py` | `--verbose` flag; default → demo, verbose → debug |
| `src/network/__init__.py` | Export new formatters |
| `tests/test_network_status.py` | Demo/verbose smoke tests; category-examples unit tests |
| `README.md`, `examples/networks/crm/README.md` | Demo default + `--verbose` note |
| `TODO.md` | Slice marked done |

## Before / after — new network (seed only)

### Before (old default)

```text
Network: crm (CRM example)
Root: .../examples/networks/crm
Seed: 15 people
Ontology: not created yet — run a query to bootstrap categories.json
Specialists: none registered
```

### After (new default)

```text
Network: crm (CRM example)
Seed: ✅ (15)
Current ontology: ❌
Existing specialists: ❌
```

### After (`--verbose`, same network)

```text
Network: crm (CRM example)
Root: .../examples/networks/crm
Seed: 15 records
Ontology: not created yet — run a query to bootstrap categories.json
Specialists: none registered
```

## Before / after — running network (post-query fixture)

### Before (old default)

```text
Network: crm (CRM example)
Root: /tmp/.../populated
Seed: 15 people
Ontology: 6 categories
  contact: agent=contact_specialist examples=5
  ...
Specialists:
  contact_specialist  category=contact  module=no  records=1  fields=email
    status counts: found=1 pending=0 na=0
```

### After (new default)

```text
Network: crm (CRM example)
Seed: ✅ (15)
Current ontology:
  contact (e.g., email, phone, …)
  demographic (e.g., age, birthday, …)
  financial (e.g., net_worth, salary, …)
  professional (e.g., title, bio, …)
  relationships (e.g., spouse, partner, …)
  social (e.g., linkedin, x_handle, …)
Existing specialists:
  contact (1)
```

### After (`--verbose`, same fixture)

```text
Network: crm (CRM example)
Root: /tmp/.../populated
Seed: 15 records
Ontology: 6 categories
  contact: agent=contact_specialist examples=5
  ...
Specialists:
  contact_specialist  category=contact  module=no  records=1  fields=email
    status counts: found=1 pending=0 na=0
```

## Verification

```text
uv run pytest -m smoke -q tests/test_network_status.py  → 10 passed
uv run pytest -m smoke -q  → 124 passed
uv run ruff check src/network/introspection.py src/main.py tests/test_network_status.py  → clean
uv run mycelium network status --network-dir examples/networks/crm  → demo layout
uv run mycelium network status --network-dir examples/networks/crm --verbose  → Root: present
```

## Unblocks

Paul hands-on demo testing; Demo slice 3 (admin daemon reuses `introspection.py`).
