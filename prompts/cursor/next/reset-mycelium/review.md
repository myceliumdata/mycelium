# Review: Cursor Prompt for bin/reset-mycelium

## Overall Assessment
The prompt is high-quality, comprehensive, and tightly aligned with the long discussion. It correctly captures:
- Python script strictly in `bin/` (no integration into main CLI or `src/`).
- Explicit dev/ops tool with security considerations (not in primary interface).
- Always canonical source paths, deliberately ignoring `MYCELIUM_*` redirections.
- Granular/selective resets matching the cycles described (global `--all` vs surgical `--specialist`).
- Trio sync via git rm + registry prune + data dir cleanup.
- Leverage existing code (reset_* singletons, get_* for reseeding, Pydantic models for safe registry work) while keeping zero changes to main source.
- "Keep it simple now, assume it will change later" philosophy (no over-engineering for future agent reset hooks/staleness/DB cleanup).
- Safety (dry-run, confirmation, --no-git, --yes).
- Verification matrix that is concrete and forces the implementer to demonstrate the key behaviors.

It follows the established style from the agent-factory prompts (strict guards, limited scope, explicit verification commands the AI must run, "only touch X" rules).

**Ready to hand to Cursor** with only minor suggested refinements below.

## Strengths
- Strong emphasis on "no complication to the main code" and "only edit bin/reset-mycelium".
- Correctly uses the Pydantic models (`AgentRegistryData`, `RegisteredAgent`) for the prune to avoid needing a `remove_agent` API in the registry for now.
- Verification steps are thorough (dry-run, actual with --no-git, restore, full --all, git status checks, final diff --stat limited to the one file).
- Handles the "human default = canonical paths" reality vs. test redirections.
- Good coverage of the comma-list + repeatable --specialist behavior.
- Includes the plan header output and end-of-run messaging from the original proposal.
- Epilog/examples in --help are explicitly called out.

## Minor Issues / Suggestions for Improvement
1. **Verification step 3/5/7 assume generated specialists exist**  
   The prompt says "or any current generated one; adjust name if none exist — first run a query that triggers creation if needed". This is good, but make it slightly more robust in the prompt: tell Cursor to first ensure at least one generated specialist exists by running a minimal query if the registry only has core_data. This prevents the verification from failing on a clean tree.

2. **Registry prune implementation guidance**  
   The prompt says "prefer loading via the Pydantic models directly for the prune to stay self-contained." This is correct. However, note that `AgentRegistryData` has `last_updated: datetime`. Cursor will need to set it properly (e.g. `datetime.now(timezone.utc)`). The prompt should remind Cursor to import `datetime, timezone` from the stdlib and set it, to avoid validation errors. Add a one-line note in the prompt under "Prune the registry".

3. **Path handling in the script**  
   The prompt correctly requires the path hack at the top for `sys.path`. It also says the script must `cd` to repo root like the old bash version. Good. Consider adding an explicit `os.chdir(...)` or relying on the hack + relative Paths. The current wording is sufficient.

4. **--help text**  
   The prompt says "Excellent `--help` text with examples" and lists them. The simulated help I provided earlier matches closely. To make it even tighter, we could add a short "After running..." sentence in the epilog (already in the prompt). No change needed, but Cursor might make the description a bit more concise.

5. **Dry-run vs real behavior for singleton resets**  
   The prompt says "After any specialists work (or at the very end if base/categories were touched), always reset the relevant singletons". This should only happen in non-dry-run. The prompt already says "if not in dry" for the reseed calls, but the final singleton reset block should be guarded too ("if not dry-run: ... reset singletons"). Minor clarification to add in the prompt.

6. **Git root / subprocess robustness**  
   The prompt requires using `git rm --ignore-unmatch` and handling the case of not being in a git repo. Good. Cursor may need `subprocess.run(..., cwd=repo_root)` if they do extra path logic. The prompt is fine as-is.

## Recommended Edits to the Prompt (optional but would make it tighter)
- Add the `datetime` import reminder in the registry prune section.
- Add a sentence: "The final singleton reset calls must be skipped in dry-run mode."
- Strengthen verification step 3: "If no generated specialists exist yet, first run a simple query (e.g. via the CLI) that triggers creation of at least one so the specialist reset paths can be exercised."

These are small. The prompt is already in very good shape.

## Scope Guard Compliance
The prompt does an excellent job enforcing the key constraints we discussed:
- Pure `bin/` Python script only.
- No edits to `src/`, `tests/`, `main.py`, registry, factory, etc.
- Security / dev-only nature preserved.
- Simple now, future evolution left open.

No over-scope instructions (no new tests, no architecture doc updates, no CLI subcommand).

## Verdict
**Approved with minor polish suggestions above.**

You can hand the current prompt to Cursor as-is and it should produce a solid implementation. If you want, I can apply the small clarifications to the prompt file before you use it.

Once Cursor produces the implementation + runs the verification commands, paste the output here and I'll do the detailed code + behavior review (comparing against the requirements and the previous discarded version).

Ready when you are.