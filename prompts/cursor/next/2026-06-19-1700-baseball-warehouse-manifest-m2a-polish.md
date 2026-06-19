# Baseball warehouse manifest polish (M2a nits)

> **READY** — Claim per `prompts/cursor/WORKFLOW.md`. **After M2c** (or anytime — does not block M2b/M2c).

**Priority:** Non-blocking nits from Grok review [`prompts/cursor/done/2026-06-19-1400-baseball-warehouse-manifest-m2a/review.md`](../done/2026-06-19-1400-baseball-warehouse-manifest-m2a/review.md).

**Do not edit `TODO.md`.**

---

## Objective

Small cleanup on M2a warehouse manifest surfacing — no behavior change for specialists or manifest generation.

---

## Nits (from review)

| # | Fix |
|---|-----|
| P1 | `warehouse_manifest_capabilities()` — remove duplicate field: keep `path`, drop `full_manifest_path` (or vice versa). Update any test asserting both. |
| P2 | Hoist `maybe_write_warehouse_manifest` import to module top in `lahman_seed.py` and `pack_ontology.py` if no import cycle; otherwise leave lazy and add one-line comment why. |
| P3 | `format_mcp_instructions()` — optional one sentence when `capabilities.get("warehouse_manifest")` is present: full manifest on disk at `path`; grains/conventions in describe_network JSON. |

---

## Verification

```bash
./bin/ci-local
uv run pytest tests/test_warehouse_manifest.py -q
```

---

## For Grok + Paul (output.md)

- M2a polish done; no follow-up required unless new nits.

**Suggested commit message:**

```
polish(baseball): warehouse manifest capabilities cleanup (M2a nits)
```