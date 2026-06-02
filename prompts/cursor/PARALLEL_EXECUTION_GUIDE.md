# Parallel Cursor Task Execution Guide for This Migration

The workflow explicitly supports running multiple Cursor agents/sessions in parallel.

## How Parallel Works (from WORKFLOW.md and the .cursor rule)

1. Each Cursor instance, when told **"Work on the next task."** (or similar), will:
   - Scan `prompts/cursor/next/`
   - Pick the oldest remaining `.md` file
   - **Immediately move it** to `prompts/cursor/in-progress/`
   - Work only on the task it claimed

2. The move to `in-progress/` is the **claim/lock**.

3. **Critical safety rule** (mandatory):
   - When finishing, the agent **must remove ONLY the specific file it personally claimed** from `in-progress/`.
   - It must **never delete, move, or touch any other files** in `in-progress/`, even if they look abandoned.
   - If it sees unexpected files in `in-progress/`, it should only document them, not touch them.

This prevents one agent from corrupting another's in-progress work.

## Recommended Safe Parallel Strategy for These 12 Tasks

The tasks have some dependencies:

**Safe to run in parallel (low/no dependency):**
- 1000 (model simplification)
- 1010 (CLI removal)
- 1020 (MCP removal)
- 1030 (responses cleanup)
- 1040 (routing simplification)
- 1050 (supervisor cleanup)

These mostly operate on different files. They can be launched together.

**Next wave (after some of the above are done or in progress):**
- 1060 (create core_data_agent) — can run once model is simplified
- 1090 (documentation) — can run early, as it's mostly cleanup of references

**Dependent (run after prerequisites):**
- 1070 (graph wiring) — needs the core_data_agent from 1060 to exist
- 1080 (tests cleanup) — benefits from knowing what the final agent/graph looks like
- 1100 (wire + agents __init__)
- 1110 (final verification) — must be last

## How to Actually Run a Few at a Time

Option 1 (easiest, recommended):
- Open 3-4 separate Cursor windows/sessions.
- In each, type: "Work on the next task."
- They will each grab a different task from `next/` and claim it.
- Monitor the `in-progress/` directory (it will show what is claimed by whom).
- When one finishes, it will clean only its own file from in-progress/.
- Repeat.

Option 2 (more control):
- Manually move 2-3 non-dependent tasks from `next/` to `in-progress/` yourself (this pre-claims them).
- Then in separate Cursor sessions, tell each one something like:
  "Work on the task that is already in in-progress/ called 2026-06-05-10XX-..."
- This bypasses the auto "next" scanner for those.

**Do NOT**:
- Manually delete files from in-progress/ that you didn't start.
- Have one Cursor session try to "help" by cleaning up in-progress/ for another.
- Run dependent tasks (like graph wiring) before their prereqs are at least claimed and making progress.

The system is explicitly designed for this ("Support for parallel agents relies on this move operation...").

If you follow the claiming rules, it is not dangerous.

After the first few independent removals are done, you can have one session working on the new core_data_agent while another does docs or test cleanup.

Current tasks in next/ (as of creation) are listed in the directory.

Use `ls -1 prompts/cursor/in-progress/` to see what's actively claimed at any time.
