# Review: reset-mycelium-cleanup (Cursor delivery)

## Summary
Cursor successfully cleaned up the three issues identified in the previous review:

1. Dead code removed from the git add block.
2. Plan header logic fixed — no more "specialists: False" for pure `--specialist` runs; only prints `specialists: True` when `--specialists`/`--all` is used, otherwise shows `specific:` cleanly.
3. Smarter git add / write: now uses `registry_changed` (based on actual removals from registry) so that nonexistent specialists (or no-op cases) do not touch the registry file or trigger `git add`.

**Scope compliance: Perfect.** Only `bin/reset-mycelium` was edited. No other files touched.

## Verification from Cursor output.md + independent spot checks
- Dry-run for specific specialist: header shows only `specific:`, no "specialists:" line at all. Good.
- Dry-run --all: shows `specialists: True`. Good.
- Edge case nonexistent: no "registry entry removed", no "registry written", no modification to registry file (confirmed via timestamp check in my tests). Script still attempts to clean the (nonexistent) py file as before, which is correct per original design.
- Full --all still works, produces clean state (only core_data).
- git status / changes only when actual registry modification happens.

I re-ran several commands:
- Header for --specialist only: clean.
- Header for --all: correct.
- Nonexistent actual run (--yes --no-git): registry timestamp unchanged (Confirmed: no write).
- --help unchanged (as expected, since no changes to parser).

All original behaviors preserved.

## Code Changes Analysis
- `_prune_registry` now returns a third value `registry_changed: bool` (computed from `removed_from_registry` list).
- Write to registry now guarded by `if not dry_run and registry_changed`.
- `_reset_specialists` unpacks the third value and passes it through.
- Git add block now: `if not dry_run and not no_git and registry_changed:` (dead inner `if dry_run` removed).
- Header printing in `main()`: 
  ```python
  if do_all_specialists:
      print("  specialists: True")
  elif specific:
      print(f"  specific:    {', '.join(specific)}")
  ```
  (Note: when do_all_specialists, it prints "specialists: True" (hardcoded string) instead of the var; this is fine and avoids the False case.)
- No other logic changes. Dry-run paths, printing, singletons, etc. untouched in behavior.

The changes are minimal, targeted, and correct. No new bugs introduced. Code remains clean and readable.

## Minor Observations (not blockers)
- In the plan header for --all, it prints "specialists: True" (literal). Could have been `print(f"  specialists: {do_all_specialists}")` but since the if guards it, and original review wanted to avoid False, the if/elif is better.
- For nonexistent specific, it still prints "Specialists to remove: ..." and attempts py clean (even if file doesn't exist). This matches the original prompt's intent for cleaning "everything new" / orphans, so acceptable.
- The return type of _prune_registry changed (now 3-tuple), but since only one call site, fine.
- No impact on help text or examples.

## Overall Verdict
**Excellent cleanup.** All mentioned issues resolved cleanly. The script is now more polished without changing its core contract or adding complexity.

The delivery matches the cleanup prompt perfectly.

No further issues found. This can be considered complete.

(If desired, we can squash the two commits or update the main done/reset-mycelium review, but not necessary.)

Ready for integration / use in dev workflow.