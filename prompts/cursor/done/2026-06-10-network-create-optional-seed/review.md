# Review: Network create v2 — optional `--seed`

**Verdict: Approved**

**Reviewer:** Grok (June 2026)

---

## Summary

Slice delivers exactly what Paul and Grok agreed: `--seed` is optional on `network create`, empty networks match `empty-crm`, seeded create unchanged, refresh auto-bootstraps with explicit stdout. Shared `bootstrap_seed_at_paths()` removes duplicate import logic. **305 passed**, ruff clean.

Small, focused diff — much lighter than the identity rename.

---

## Checklist

| Requirement | Status |
|-------------|--------|
| CLI `--seed` optional | Pass |
| `create_network(..., seed_path=None)` keyword-only | Pass |
| No seed → no `seed.json`, no `entities.json` | Pass (`test_create_network_without_seed`) |
| With seed → copy + bootstrap | Pass (existing tests updated to `seed_path=`) |
| `--force` without seed clears stale bootstrap | Pass |
| Dry-run validates seed only when provided | Pass |
| `entities_bootstrapped` on result + CLI stdout | Pass |
| Refresh uses shared bootstrap + `seed_bootstrap_count` | Pass |
| Refresh script reports import line | Pass |
| README with/without seed + refresh note | Pass |
| No `--seed` on refresh script | Pass |

---

## Non-blocking nits

| ID | Note |
|----|------|
| N1 | `validate_seed_file` and `_load_seed_people` still duplicate validation (pre-existing; fine to dedupe later) |
| N2 | Dry-run CLI could print dim hint when `--seed` omitted (optional UX) |
| N3 | `docs/plans/network-create-optional-seed.md` status still "Queued" — Grok can mark shipped on commit |

---

## API note for callers

`create_network(name, root, creation_prompt, *, seed_path=...)` — positional `seed_path` removed. All in-repo call sites updated.

---

## Suggested commit message

```
Network create: make --seed optional; unify refresh seed bootstrap.

Empty networks match empty-crm; refresh auto-imports when seed.json
shipped in example; shared bootstrap_seed_at_paths helper.
```