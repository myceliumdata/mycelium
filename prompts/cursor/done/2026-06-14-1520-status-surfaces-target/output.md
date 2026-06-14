# Program 3 — Slice 1520: Status surfaces — target resolve JSON (D2-b)

## Summary

Aligned CLI and admin inspect with the target step-1 protocol. Status JSON now exposes `resolve: { id, lookup }` instead of `entity_key`, and inspect uses exact resolution only (no fuzzy suggestions).

## Breaking changes

| Surface | Before | After |
|---------|--------|-------|
| CLI | `--entity KEY` | `--id UUID` or `--lookup-json '{…}'` |
| Admin `GET /status` | `?entity=` | `?id=` or `?lookup=` |
| Status JSON | `entity_key`, `entity_matches`, … | `resolve`, `resolve_matches`, `resolve_kind`, … |

## Code changes

| File | Change |
|------|--------|
| `src/network/introspection.py` | `StatusResolve` + renamed summary fields; `build_network_status(resolve_id, resolve_lookup)`; id → `lookup_by_id`, lookup → `resolve_status_for_target_lookup`; formatters print `Resolve:` |
| `src/main.py` | `--id` / `--lookup-json`; removed `--entity` |
| `src/mycelium_admin/server.py` | `id` query param; removed `entity` |
| `admin-ui/src/types.ts` | `StatusResolve`, renamed response fields |
| `admin-ui/src/mvr.ts` | `inspectStatusParams` sends `id`; `hasStatusTarget` checks `id` |
| `admin-ui/src/api.ts` | `fetchStatus` uses `id` param |
| `admin-ui/src/EntityDrilldown.tsx` | Header from `status.resolve` |
| `tests/test_network_status.py` | Updated drill-down tests; added `test_status_json_omits_entity_key`, `test_status_cli_lookup_json`; replaced fuzzy near-miss with `test_status_exact_inspect_no_fuzzy` |
| `tests/test_admin_daemon.py` | Updated lookup/entity drill-down; added `test_status_by_id` |
| `docs/manual-checks/2026-06-13-program2-post-program-gate.md` | Check 1/7 use `--lookup-json` |

## Verification

```bash
./bin/ci-local
# CI local: all steps passed.
# 427 passed, 26 deselected
```

## For Grok + Paul

- Inspect no longer calls `resolve_entity_for_lookup` — fuzzy ranking is query-only.
- **Committed** after Grok review (see `review.md`).

Suggested commit message:

```
feat(status): target resolve JSON and id/lookup-json inspect inputs
```
