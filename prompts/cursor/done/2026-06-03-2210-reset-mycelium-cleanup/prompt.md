# Cursor Prompt: Cleanup for bin/reset-mycelium (follow-up to previous delivery)

## Context
This is a small, targeted cleanup slice for the `bin/reset-mycelium` dev/ops tool that was delivered in the previous step (see `prompts/cursor/done/reset-mycelium/prompt.md`, `output.md`, and `review.md`).

The script is already functional and passes the original verification matrix. The previous review identified a few minor issues that should be cleaned up for polish. The goal is to address only those issues with the smallest possible changes.

**Strict scope:** This slice must **only** edit `bin/reset-mycelium`. Do not touch any other files (no tests, no docs, no src/, no prompts/, no changes to the previous review/output files, etc.). After your changes, `git diff --stat` must show changes **only** in `bin/reset-mycelium`.

You must re-run a focused verification at the end (see below) and include the output + final `git diff --stat` in your response.

## Issues to Fix (from the review)
Address these exactly, in priority order. Keep changes minimal and clean.

1. **Dead code in the git add block** (clear bug / leftover):
   In `_reset_specialists`, there is unreachable code:
   ```python
   if not dry_run and not no_git:
       ...
       if dry_run:  # unreachable
           print(...)
       elif _in_git_repo():
   ```
   Remove the dead inner `if dry_run` branch. Clean up the logic so it simply does the git add when appropriate (or the warning). Make the code correct and readable with no dead branches.

2. **Plan header prints "specialists: False" for pure --specialist runs** (cosmetic inconsistency):
   Currently in `main()`:
   ```python
   print(f"  specialists: {do_all_specialists}")
   if specific:
       print(f"  specific:    {', '.join(specific)}")
   ```
   This produces output like:
   ```
   === reset-mycelium ===
     ...
     specialists: False
     specific:    demographic_specialist
   ```
   Fix the header printing logic so it only prints the `specialists:` line when `do_all_specialists` is True. When using `--specialist` (without `--specialists` or `--all`), print only the `specific:` line (or a clean equivalent). Match the spirit of the examples in the original prompt and the help text (e.g. don't emit "specialists: False").

   You may adjust the printing of the plan header for clarity (e.g. only emit relevant lines), but keep the overall "=== reset-mycelium ===" format and the other fields (base, categories, dry-run, git).

3. **Git add timing** (minor over-add, harmless but not ideal):
   The registry `git add` currently runs whenever there are `remove_names` (even if the prune removed zero entries, e.g. a non-existent specialist name was requested). 
   Make the git add conditional on whether any actual removal happened in the registry prune (i.e., only `git add` if the registry content actually changed, or if at least one specialist was successfully removed from the registry). This keeps the working tree cleaner in edge cases.

   (The prune function already returns the pruned data; you can use that to detect changes.)

Do **not** change help text wording, epilog examples, or other behaviors unless they are directly required to fix the above three issues. Do not add new features.

## Additional Guidance
- Preserve all existing good behavior: canonical paths only, ignore MYCELIUM_* envs, dry-run semantics, confirmation, git --ignore-unmatch + skips, reseeds via singletons, final singleton resets, trio sync, etc.
- Keep the code style consistent (helpers, deferred imports for resets, etc.).
- The script must remain a pure dev/ops tool with no impact on mainline code.
- After edits, the previous full verification matrix from the original prompt should still pass (you don't need to re-run the entire matrix, but the focused steps below should demonstrate the fixes).

## Verification Steps (run these after edits and include full output)
You must execute these steps and paste the results (plus final `git diff --stat`) into your response. Start from a clean state (use `git checkout --` on affected paths if needed before starting).

1. `chmod +x bin/reset-mycelium` (if not already)

2. `./bin/reset-mycelium --help` (confirm help is unchanged except for any incidental effects of header logic)

3. `./bin/reset-mycelium --dry-run --specialist demographic_specialist` (or any current generated specialist; use one that exists)
   - Verify the plan header does **not** contain a "specialists: False" line. It should cleanly show only the relevant `specific:` line (and other fields).
   - Verify dry-run still works correctly for the prune, data dir, py file, and singletons.

4. `./bin/reset-mycelium --dry-run --all`
   - Verify header shows `specialists: True` (or equivalent) + no spurious lines.

5. Actual run: `./bin/reset-mycelium --specialist <existing-one> --yes --no-git`
   - After: confirm registry pruned (only core + non-removed remain), py and data dir gone, git status shows the expected M/D.
   - Confirm the git add happened only for the registry (and that it was appropriate).

6. Restore the state: `git checkout -- data/agent_registry.json src/agents/specialists/<name>.py data/agents/<cat>/`

7. Edge case: `./bin/reset-mycelium --specialist nonexistent_specialist --yes --no-git`
   - Verify no unnecessary git add happened (registry should not be modified in git status if nothing was removed).
   - Header should be clean (no "specialists: False").

8. `./bin/reset-mycelium --all --yes --no-git` (quick sanity that full flow still works)

9. Restore again as needed.

10. `git diff --stat` (must show changes **only** in `bin/reset-mycelium`; no other files touched in this slice).

Include the exact terminal output for the key steps (especially the plan headers in dry-runs and the edge case).

## Success Criteria
- The three listed issues are fixed with minimal, clean changes.
- All original functionality and safety properties are preserved.
- The script remains readable and consistent with the previous delivery.
- Verification passes with clean headers, no dead code, and smarter git add.
- Scope strictly limited to the one file.
- `git diff --stat` at the end reflects only this cleanup.

Implement the fixes now. When complete, run the verification steps above and report the full results + diff. 

If any part of the original verification matrix would now fail due to your changes, fix it as part of this slice (but keep changes minimal).