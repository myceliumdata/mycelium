# Output: Rename CoreIdentityAccessor → CoreIdentity

## Summary

Mechanical rename per Paul’s naming decision: the class represents the Core Identity agent, not an “accessor” adapter.

## Changes

| Item | Before | After |
|------|--------|-------|
| Class | `CoreIdentityAccessor` | `CoreIdentity` |
| Singleton | `_accessor` | `_core_identity` |
| `get_core_identity()` return type | `CoreIdentityAccessor` | `CoreIdentity` |
| `routing.py` parameter / variable | `accessor` | `core_identity` |
| Test stub | `_StubIdentity(CoreIdentityAccessor)` | `_StubCoreIdentity(CoreIdentity)` |
| `TODO.md` | replace `CoreIdentityAccessor` | evolve `CoreIdentity` |

## Docstrings (`core_identity.py`)

- Module describes **Core Identity agent** (Phase 1), not a facade/accessor.
- Class docstring: responsible for core person identity data (`id`, `name`, `employer`).

## Files modified (scope only)

- `src/agents/core_identity.py`
- `src/agents/routing.py`
- `tests/test_supervisor_routing.py`
- `TODO.md`

No other files touched (including `docs/architecture.md` and `prompts/cursor/done/**` per scope).

## Verification

- `rg CoreIdentityAccessor` in allowed paths — no matches
- `uv run pytest` — **8 passed**
- `uv run ruff check src tests` — clean

## In-progress cleanup

Removed only `prompts/cursor/in-progress/2026-06-02-1200-rename-coreidentityaccessor-to-coreidentity.md`.
