# Review: bin/reset-mycelium (Cursor delivery)

## Summary
Cursor implemented `bin/reset-mycelium` as a self-contained Python script per the prompt.

**Scope compliance: Excellent.** Only `bin/reset-mycelium` was created/edited. No changes to `src/`, tests, CLI, registry, factory, etc. Matches the strict "no complication to main code" and "dev/ops tool only" requirements.

**Verification:** Cursor executed the full matrix (help, dry-runs, surgical with --no-git, restores, --all, base+categories, final git diff --stat limited to the new file). Output.md documents the runs and results. The provided verification claims success on key behaviors.

The script is clean, uses the Pydantic models for safe registry pruning, hardcodes canonical paths, skips env redirections, handles git with --ignore-unmatch + skips in dry/no-git, performs reseeds via the existing singletons, ends with full singleton resets, has confirmation + dry-run, supports comma/repeat --specialist, and produces the expected plan header + final messaging.

## Positives
- Faithful to prompt: Python in bin/, shebang + path hack, argparse with exact flags, help includes the required examples.
- Registry handling: Loads via AgentRegistryData.model_validate, rebuilds keeping core_data + non-removed, updates last_updated, writes JSON directly (no main code change). Also scans for orphan data dirs post-prune.
- Git/FS: Dedicated _git_rm and _remove_path helpers that respect dry/no_git. Uses subprocess for git, graceful no-repo fallback.
- Dry-run: Prints "(would ...)" / "[skipped]" for everything, no side effects. Singletons reset also skipped in dry.
- Reseed logic: Unlinks then calls reset_* + get_* inside the helpers (imports deferred inside the non-dry paths).
- Collection: _collect_all_specialist_names combines registry non-core + disk orphans, deduped/sorted.
- Arg parsing: _parse_specialist_args handles comma lists + repeats + dedup.
- Safety: Confirmation prompt (unless --yes/dry), early exit on no targets (prints help).
- Output: Clear "=== reset-mycelium ===" plan, "=== Executing ===", per-item messages, final "Done." + git status advice.
- Small touches: os.chdir to repo root, _in_git_repo check, relative paths for git commands.

## Issues Found
1. **Dead code in git add block** (minor bug):
   ```python
   if not dry_run and not no_git:
       ...
       if dry_run:  # This branch is unreachable
           print(...)
       elif _in_git_repo():
   ```
   This is leftover copy-paste. The inner `if dry_run` will never trigger. Harmless but ugly. Should be removed or the logic cleaned (the outer already guards).

2. **Plan header always prints "specialists: False" for pure --specialist runs**:
   ```
   === reset-mycelium ===
     ...
     specialists: False
     specific:    demographic_specialist
   ```
   Functional, but the header logic in main() always prints the `do_all_specialists` flag even when using specific. The prompt examples showed "specialists: ..." only when relevant. Minor polish: could conditional-print or use "specialists (all):" vs "specific:" more cleanly. Cursor's dry-run example in output.md abbreviated it away.

3. **Git add for registry happens unconditionally after any specialist removal (even if no actual change)**:
   If you run `--specialist nonexistent`, prune still runs (no names removed), but if registry was written? No, prune only writes if not dry. But the git add block is after _reset_specialists and runs if remove_names (even if prune did nothing). Harmless, but could check if anything was actually removed.

4. **No explicit "registry written" message in some paths?** Wait, in non-dry prune it does print "registry written: data/agent_registry.json" inside _prune_registry. Good. In the surgical verification, the git status showed M as expected (from the write + later git add in the code).

5. **Help text is slightly different from my earlier simulation** (wording on base/categories is abbreviated: "Reset data/mycelium.db" instead of full). But matches what the prompt asked for in the epilog. Cursor chose concise option help texts. Acceptable.

6. **Verification output.md is a bit summarized** (e.g. "Plans base unlink..." for dry-all). But the key claims (registry only core after --all, files gone, reseeds happened, no main code touched) are believable and align with code inspection.

7. **Minor: In dry-run output, paths are shown with full /Users/...** because of how _repo_path + print happens. Not a problem, but real runs from repo root would be relative-ish. Fine for dev tool.

No security, correctness, or scope violations. No new deps, no main code edits.

## Behavior vs Prompt Requirements
- Canonical paths: Yes (hardcoded globals, _repo_path always from REPO_ROOT).
- Ignore MYCELIUM_*: Yes (never calls _default_* helpers; models loaded directly with explicit paths).
- Git sync: Yes (git rm for py + data dirs, git add for registry only when not no-git).
- Reseeds + singletons: Yes (via the four reset/get pairs + final _reset_singletons).
- Selective + all: Yes.
- Dry-run / no-git / yes: Yes.
- Help + examples: Yes.
- Simple, no over-engineering: Yes (no specialist hooks yet, as expected).

## Recommendations
- Fix the dead `if dry_run` branch inside the git add block (easy one-liner removal).
- Optionally improve the plan header to avoid printing "specialists: False" when using --specialist only (e.g. only print "specialists:" when do_all_specialists, always print specific if present).
- The rest is solid. The implementation is production-ready for a dev tool.

**Overall: Good delivery. Minor cleanups suggested, but core functionality matches the prompt and our requirements.**

Cursor respected the "only this file" rule and the verification matrix. The script is readable and maintainable.

If the user wants, we can accept with the small fixes or ask Cursor for a patch.

(The pre-existing WIP in the tree from agent-factory work is noted in Cursor's output.md and is out of scope for this slice.)