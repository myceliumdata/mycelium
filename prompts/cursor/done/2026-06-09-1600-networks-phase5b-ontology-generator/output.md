# Output: Networks Phase 5b — skeleton ontology generator

## Summary

Implemented `src/network/ontology.py` with `generate_skeleton_ontology()`: one structured LLM call (mockable via `llm=`) produces a validated skeleton ontology — `CategoryTreeData` + companion `RegisteredAgent` list. Validation includes category slugify, agent-name regex, 3–8 category bounds, minimal `attribute_map` from examples only, and one retry on validation failure.

## Files changed

| File | Change |
|------|--------|
| `src/network/ontology.py` | New — LLM + validation + `SkeletonOntologyResult` |
| `src/network/__init__.py` | Export `generate_skeleton_ontology`, errors |
| `tests/test_network_ontology.py` | 5 smoke tests (all LLM mocked) |

## Verification

```bash
uv run pytest -m smoke -q tests/test_network_ontology.py   # 5 passed
uv run pytest -m smoke -q                                   # 96 passed
uv run ruff check src tests                                 # clean
```

## Example mock ontology shape

LLM returns `ProposedOntology`; post-processing yields serializable artifacts for slice 5c:

```json
{
  "categories": {
    "version": "1.0",
    "last_updated": "2026-06-09T12:00:00+00:00",
    "model_used": "gpt-4o-mini",
    "categories": {
      "crop": {
        "description": "Crop yields and planting data.",
        "assigned_agent": "crop_specialist",
        "examples": ["wheat_yield", "planting_date", "harvest_window"]
      },
      "soil": {
        "description": "Soil chemistry and moisture.",
        "assigned_agent": "soil_specialist",
        "examples": ["ph_level", "moisture", "nitrogen"]
      },
      "equipment": {
        "description": "Farm machinery and maintenance.",
        "assigned_agent": "equipment_specialist",
        "examples": ["tractor_id", "last_service", "fuel_level"]
      }
    },
    "attribute_map": {
      "wheat_yield": "crop",
      "planting_date": "crop",
      "harvest_window": "crop",
      "ph_level": "soil",
      "moisture": "soil",
      "nitrogen": "soil",
      "tractor_id": "equipment",
      "last_service": "equipment",
      "fuel_level": "equipment"
    }
  },
  "agents": [
    {
      "name": "crop_specialist",
      "category": "crop",
      "description": "Crop yields and planting data.",
      "module_path": "agents.specialists.crop_specialist",
      "entrypoint": "crop_specialist",
      "storage_path": "agents/crop/storage.json",
      "strategy_path": "agents/crop/storage_strategy.json",
      "is_generated": true,
      "created_at": "2026-06-09T12:00:00+00:00"
    }
  ]
}
```

(`storage_path` values are network-relative when `MYCELIUM_NETWORK_ROOT` + `MYCELIUM_AGENT_DATA_DIR` are set under the same root.)

## Test checklist

| Test | Status |
|------|--------|
| Happy path mock | **PASS** |
| Invalid agent name → retry → error | **PASS** |
| Empty prompt before LLM | **PASS** |
| Missing `OPENAI_API_KEY` | **PASS** |
| Diverse domain ≠ CRM six | **PASS** |

## Next queue item

`prompts/cursor/next/2026-06-09-1700-networks-phase5c-network-create-cli.md`
