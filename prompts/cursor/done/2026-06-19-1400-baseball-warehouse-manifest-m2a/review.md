# Review — baseball warehouse capability manifest (M2a)

**Verdict:** **Approved + polish nits**  
**Reviewer:** Grok  
**Date:** 2026-06-19 (review completed after Paul return)

## CI

| Check | Result |
|-------|--------|
| `./bin/ci-local` | **565** smoke passed, ruff clean, admin-ui build ok |
| `uv run pytest tests/test_warehouse_manifest.py -q` | **6** passed |

## Delivery

`output.md` claims match files on disk. M2a implementation present; not yet committed (mixed working tree with unrelated fuzzy work — scope M2a-only at commit).

## Spec compliance

| Criterion | Result |
|-----------|--------|
| `warehouse_domains.json` pack config (4 domains, grains, `career_sum`) | Pass |
| `warehouse_manifest.json` written after bootstrap ingest | Pass |
| Idempotent rewrite on sync / ontology install | Pass |
| Introspection capped to domain tables only (not all 30+ Lahman tables) | Pass |
| `build_network_capabilities()` includes `warehouse_manifest` summary | Pass |
| M1b/M1c smoke unchanged | Pass |
| Generic stat resolver (M2b scope) | N/A — correctly deferred |
| `TODO.md` untouched | Pass |

## Legacy / dual-path

M1 batting/bio specialist behavior unchanged. Manifest is additive metadata + describe_network surfacing.

## Tests

Six tests cover: pack config load, sqlite introspection, full baseball refresh write, idempotent rewrite, capabilities summary, merge unit. Gap: no isolated `--sync-only` test without full refresh (acceptable — `install_pack_ontology_from_example` hook covered indirectly via refresh fixture).

## Design critique

**Strong:** Clean split — committed pack rules (`warehouse_domains.json`) merged with runtime introspection; table cap policy avoids full-Lahman PRAGMA sweep; framework module (`warehouse_manifest.py`) is reusable for other warehouse packs; hooks at both bootstrap and sync paths.

**Sub-optimal (non-blocking):** Capabilities summary duplicates `path` and `full_manifest_path`; lazy imports in pack hooks vs top-level import in introspection; MCP instruction blurb does not mention manifest (JSON payload is sufficient for now).

## Polish nits (non-blocking)

| # | Nit | Note |
|---|-----|------|
| P1 | `warehouse_manifest_capabilities` sets `path` and `full_manifest_path` to the same value | Drop one field in a small polish pass or fold into M2b when specialists read manifest. |
| P2 | Lazy `maybe_write_warehouse_manifest` imports in `lahman_seed.py` / `pack_ontology.py` | Fine if avoiding import cycles; otherwise hoist to module top for consistency with `introspection.py`. |
| P3 | `format_mcp_instructions` silent on `warehouse_manifest` | Optional one-liner: “see `warehouse_manifest` in describe_network when present.” |

**Queued:** `prompts/cursor/next/2026-06-19-1700-baseball-warehouse-manifest-m2a-polish.md` (M2a A1–A3 + M2b B1–B4, after M2c).

## Diff reviewed

- `examples/networks/baseball/warehouse_domains.json` (new)
- `src/network/warehouse_manifest.py` (new)
- `tests/test_warehouse_manifest.py` (new)
- `examples/networks/baseball/bootstrap_handlers/lahman_seed.py`
- `src/network/pack_ontology.py`
- `src/network/introspection.py`
- `examples/networks/baseball/README.md` (M2a operator note)
- `prompts/cursor/done/2026-06-19-1400-baseball-warehouse-manifest-m2a/` (`prompt.md`, `output.md`)

## For Paul

- **Commit message:** `baseball: warehouse capability manifest + describe_network surfacing (M2a)`
- **Commit scope:** M2a files only — exclude fuzzy/entity_resolution drift, `checkpoints.sqlite`, unrelated doc edits unless bundled intentionally.
- **Optional manual (~5 min):** After `--sync-only`, `describe_network` should show `warehouse_manifest.present`; read `warehouse_manifest.json` on disk for domains/grains.
- **Next:** Claim **M2b** (`2026-06-19-1500-baseball-generic-warehouse-resolver-m2b.md`) — still in `next/`, ready.
- **TODO.md:** Grok/Paul — mark M2a done after commit.