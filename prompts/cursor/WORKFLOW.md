# Mycelium — Cursor Agent Workflow

**Note on reorganization (June 2025):**  
The Cursor handoff directories (`next/`, `in-progress/`, `done/`) and this `WORKFLOW.md` were moved under `prompts/cursor/` for better organization. Historical task records in `prompts/cursor/done/` may contain older path references from before this move.

This document defines how Grok + Paul direct Cursor (as a senior developer) using structured prompts.

A dedicated Cursor rule (`.cursor/rules/04-cursor-workflow.mdc`) is also in place so that Cursor agents automatically understand the "work on the next task" behavior without needing the full context every time.

## Quick Start: How Paul Gets Cursor to Work on the Next Task

You no longer need to specify which prompt to work on.

Simply open Cursor and give it one of these simple instructions:

- "Work on the next task."
- "Pick up the next available prompt and execute it."
- "Start the next task in the queue."

Cursor will automatically:
1. Look in `prompts/cursor/next/`
2. Select the oldest task (sorted by filename)
3. Claim it by moving the file to `prompts/cursor/in-progress/`
4. Execute the work
5. Deliver results under `prompts/cursor/done/`

This is the preferred way to hand work to Cursor.

A project-level Cursor rule (`.cursor/rules/04-cursor-workflow.mdc`) is active, so Cursor should already understand this protocol when you say "Work on the next task."

A simple test task currently exists in `prompts/cursor/next/` (`2025-06-01-1650-test-workflow.md`) that you can use to validate the full flow before running real work.

## Philosophy

- **Grok + Paul** decide *what* should be done and the architectural direction.
- **Cursor** (the AI in the IDE) acts as the senior developer that executes the work.
- We want low-friction, reviewable handoffs without constant copy-pasting of long prompts.

## Roadmap ownership — `TODO.md` (Grok + Paul only)

**Cursor must never edit `TODO.md`.** Not to check off items, not to add prompt paths, not to update "Last updated", not for vocabulary sweeps unless a prompt explicitly lists it under *may modify* (legacy prompts may be wrong — this section wins).

| Owner | Role |
|-------|------|
| **Grok + Paul** | `TODO.md` — roadmap, slice status, priorities, prompt queue references |
| **Cursor** | Code, tests, task-scoped docs (`README.md`, example READMEs when prompted); report in `output.md` |

After completing work, Cursor documents what Grok + Paul should update in **`output.md`** under a **"For Grok + Paul"** section (e.g. "Mark Demo slice 4 done", "Add fuzzy matching note"). Grok or Paul applies `TODO.md` changes after review.

**If Cursor already changed `TODO.md` in a branch:** revert those edits; put the same notes in `output.md` instead.

## Directory Structure

```
prompts/
├── cursor/
│   ├── WORKFLOW.md             # This file
│   ├── next/                   # Ready-to-pickup work for Cursor
│   ├── in-progress/            # Work currently being executed by a Cursor agent
│   └── done/                   # Completed work + review artifacts
│       └── <timestamp>-<slug>/
│           ├── prompt.md
│           ├── output.md
│           ├── review.md
│           └── ...
├── grok-build/
└── system/
```

## Workflow

### 1. Creating New Work (Grok + Paul)

- We agree on a piece of work.
- Grok creates a new file in `prompts/cursor/next/` named:
  `<YYYY-MM-DD>-<short-description>.md`
- The file is a **self-contained prompt** for Cursor.
- The prompt must include:
  - Clear objective
  - Constraints and principles (especially from `docs/architecture.md`)
  - Required output format and location (`prompts/cursor/done/<name>/`)
  - Instructions telling Cursor to follow the discovery + claiming process defined in this `WORKFLOW.md` (i.e. do not assume the filename will be provided directly)

### 2. Discovering and Claiming the Next Task (Cursor)

When Paul tells Cursor to "work on the next task", Cursor **must** follow this process:

1. Scan the directory `prompts/cursor/next/`.
2. List all `.md` files.
3. Sort them alphabetically (this works because filenames start with `YYYY-MM-DD-HHMM`).
4. Select the **first** file in the sorted list — this is considered the "next" task.
5. **Immediately move** that file from `prompts/cursor/next/` to `prompts/cursor/in-progress/`.
6. Begin executing the task described in the prompt.

This move to `in-progress/` serves as the claim/lock. Other Cursor agents will see the file is no longer in `next/` and will pick a different one (or find nothing left).

**Rules for Cursor:**
- Never work on a file that is still in `prompts/cursor/next/`. Always claim it first by moving it.
- If `prompts/cursor/next/` is empty, clearly report that there is no work available.
- Support for parallel agents relies on this move operation happening atomically before any real work begins.

### 3. Completing Work (Cursor)

When Cursor finishes, run this **completion checklist** in order. Do not tell Paul the slice is done until every item passes.

#### Completion checklist (mandatory)

| # | Step | Verify |
|---|------|--------|
| 1 | **Run CI** | `./bin/ci-local` green (or document failure in `output.md` — do not claim complete). |
| 2 | **Verify code exists** | Every file listed in your planned `output.md` is actually written on disk — not tests-only when the prompt required implementation. |
| 3 | **Create `done/` folder** | `prompts/cursor/done/<prompt-basename>/` (same name as the claimed prompt, without `.md`). |
| 4 | **Move prompt → `prompt.md`** | Copy/move the claimed prompt into that folder as `prompt.md`. **Remove it from `next/` and `in-progress/`** — never leave a duplicate in `next/`. |
| 5 | **Write `output.md`** | Summary, decisions, verification counts, **"For Grok + Paul"** (TODO notes — do not edit `TODO.md`), suggested commit message. |
| 6 | **Remove your claim** | Delete **only** the file you moved to `in-progress/` (your slice). Do not touch other agents' files in `in-progress/`. |
| 7 | **Do not commit** | Leave all code changes in the working tree. **Grok** commits after review on `mycelium`; **no push** until Paul asks. |
| 8 | **Tell Paul** | "Slice ready for review" (or report CI/blocker). Do **not** write `review.md` — Grok does that. |

**Common failures (avoid):**

- `output.md` describes code that was never saved.
- Prompt file left in `next/` after work moved to `done/` (stale duplicate).
- `git commit` / `git push` before Grok review.
- Deleting or moving another agent's file in `in-progress/`.

### Parallel Safety Notes
- Never assume you are the only agent working.
- Never delete files in `in-progress/` that you did not personally move there.
- If you see unexpected files in `in-progress/`, document them in your `output.md` but do not touch them.

### 4. Review (Grok + Paul)

- We review the contents of `prompts/cursor/done/<name>/`
- Grok adds `review.md` with: **Approved** / **Approved + fix slice** / **Approved + polish nits** / **Not Approved**

#### Grok review rules (mandatory)

| Rule | Detail |
|------|--------|
| **Read-only review** | Grok **must not write or edit source code** during slice review — no “fixing” failing CI, no patching missing implementation. Exception: Paul explicitly authorizes Grok to implement in that message. |
| **Full diff review** | Before any **Approved** verdict, Grok reads the **entire** slice diff — every changed and new file. Use `git diff` (staged + unstaged + untracked via the WORKFLOW local-diff recipe) or read each file in the changed-files list. Spot-checking key files alone is **not** sufficient. |
| **Substantive critique** | Grok applies real engineering judgment: architecture fit, edge cases, naming, duplication, scope creep, test gaps, and whether the approach is the **best** option — not merely “CI green.” **Push back** when Cursor’s implementation is sub-optimal; say why and what to do instead. Blocking design/spec issues → **Not Approved** + fix slice; improvements that can wait → **Approved + polish nits** with concrete rows in `review.md`. |
| **Cursor implements** | Blocking failures (CI red, incomplete delivery, spec miss, unacceptable design) → **fix / remedial slice** in `prompts/cursor/next/` for Cursor — **before** the next planned slice. Do not queue the next slice until the fix slice is approved (unless Paul waives). |
| **Verify delivery** | Compare `output.md` claims to `git diff` / changed files. Tests-only or docs-only delivery when the prompt required code is **Not Approved**. |
| **Run CI** | `./bin/ci-local` before any **Approved** verdict (mandatory). |
| **Large slices** | When the diff is large (graph, state, metering, multi-module), Grok may additionally run the **`/review` skill** (reviewer subagent on the full diff) and fold findings into `review.md`. That supplements — does not replace — Grok’s own full read. |

```bash
./bin/ci-local
```

Mirrors `.github/workflows/ci.yml` — do not rely on `pytest -q` alone; CI also builds `admin-ui` and runs **smoke** tests only.

Record pass/fail and counts in `review.md` (e.g. `316 smoke passed`, ruff clean, admin-ui build ok). If CI fails, verdict is **Not Approved** — queue a fix slice; Grok does **not** patch code to green CI.

Optionally also run `LANGCHAIN_TRACING_V2=false uv run pytest -q` for major slices; that is extra, not a substitute for `ci-local`.

#### `review.md` checklist (Grok fills per slice)

Include these sections (can be brief; “Pass” / “N/A” is fine when true):

| Section | What to confirm |
|---------|-----------------|
| **CI** | `./bin/ci-local` table (mandatory). |
| **Delivery** | `output.md` matches actual files; no missing implementation. |
| **Diff reviewed** | List files read; note if `/review` subagent was used. |
| **Spec compliance** | Slice prompt exit criteria — table with Pass/Fail. |
| **Legacy / dual-path** | Unchanged behavior where the prompt required it. |
| **Tests** | New/changed tests cover the slice; gaps called out. |
| **Design critique** | What is strong; what is sub-optimal (even if approved). |
| **Nits** | Non-blocking polish rows, or “none.” |
| **For Paul** | Commit message; next slice queued; push reminder (local only until program done). |

Verdict line at top: **Approved** / **Approved + polish nits** / **Approved + fix slice** (rare — open blocking nit but Paul waived advance) / **Not Approved**.

#### Git — commit and push (Paul, June 2026)

| Repo | Who commits | Who pushes `origin` |
|------|-------------|---------------------|
| **`mycelium`** (this framework repo) | **Grok** — locally after **Approved** review (+ fix slice if any) | **Paul only** — Grok pushes **only when Paul explicitly asks**, typically after a **full program** is implemented and tested. **No mid-program pushes.** |
| **`mycelium-website`** (public site) | **Paul** | **Paul** — after local review. Grok/Cursor do not push. Deploy (Cloudflare Pages, etc.) is also Paul's step. |

**During multi-slice programs** (e.g. MVR M1–M10): Grok may commit each approved slice locally on `mycelium`; keep `origin` unchanged until Paul requests a program-level push. Anyone cloning `origin` mid-program would otherwise see inconsistent docs and half-wired code.

**Fix-slice naming:** timestamp between parent and next (e.g. `1205-…-fix-…` between `1200` and `1300`). Batch related blocking issues into one fix prompt when sensible.

#### Nit triage

| Severity | Grok action |
|----------|-------------|
| **Blocking** | **Not Approved** + fix slice in `prompts/cursor/next/` (see above). Applies to **all** programs, not only entity-protocol. |
| **Non-blocking** | **Approved + polish nits** — for entity-protocol program, add a row to `docs/plans/entity-protocol-polish-post8.md` (polish slice `1800`). Other programs: note nits in `review.md` or program polish doc. |

Do not advance the planned slice queue past a slice with open **blocking** issues unless Paul waives.

- Other programs / ad-hoc work: follow-up prompt in `prompts/cursor/next/`, or ask Cursor to continue in the same done folder.

## How to Get a Cursor Agent to Start Working (Paul)

The recommended way is now very simple:

Open Cursor and say one of the following:

- "Work on the next task."
- "Pick up the next available prompt."
- "Start the next task in the queue."

Cursor has been instructed (via this `WORKFLOW.md`) to:
- Automatically discover the oldest task in `prompts/cursor/next/`
- Claim it by moving it to `prompts/cursor/in-progress/`
- Execute it according to the instructions inside the prompt
- Deliver output under `prompts/cursor/done/`

You should no longer need to specify filenames when starting work.

## Prompt Template Requirements

Every prompt in `prompts/cursor/next/` **must** contain:

- A clear title and objective
- References to `docs/architecture.md` and `TODO.md` (read-only context for Cursor)
- Explicit instructions on **output location** and **required artifacts**
- Clear instructions telling Cursor to **move the prompt file to `in-progress/`** before starting work
- The **Governance** block below (mandatory — do not tell Cursor to edit `TODO.md`)
- **No commit before review** — see §3 step 5

### Governance block (copy into every new prompt)

```markdown
## Governance (mandatory)

- **Do not edit `TODO.md`.** Roadmap updates are for Grok + Paul after review.
- In `output.md`, add **"For Grok + Paul"**: what to check off, any roadmap notes.
- Cursor delivers: code, tests, task-scoped docs, and `output.md` only.

## When finished (mandatory — see WORKFLOW.md §3)

1. `./bin/ci-local` green
2. `prompts/cursor/done/<slice>/` with `prompt.md` + `output.md`
3. Remove claimed file from `in-progress/` **and** ensure no duplicate remains in `next/`
4. **Do not commit or push** — tell Paul "slice ready for review"
```

## History & Auditability

- All completed work is archived under `prompts/cursor/done/<prompt-name>/`.
- Each folder contains:
  - The original prompt (`prompt.md`)
  - Cursor's output and artifacts
  - Optional review notes from Grok + Paul (`review.md`)
- This structure provides a durable, git-tracked history of all agentic work.

## How Grok + Paul Track Work That Needs Review

**Simple rule:** Any directory inside `prompts/cursor/done/` that does **not** contain a `review.md` file is considered "pending review."

To see what needs attention:
- Look for folders under `prompts/cursor/done/` without a `review.md`
- Or run a quick command like: `ls prompts/cursor/done/*/review.md 2>/dev/null || echo "Nothing reviewed yet"`

We may add lightweight tooling later (e.g. a script or GitHub Action) to surface pending reviews, but for now the absence of `review.md` is the signal.

When reviewing:
- Read `output.md`, then the **full diff** (every changed/new file)
- Run `./bin/ci-local`; record results in `review.md` using the checklist above
- Critique design quality — approve only when spec **and** approach are acceptable; push back when sub-optimal
- Grok adds `review.md` with verdict, CI results, design critique, and fix-slice path if needed
- Grok commits locally on **`mycelium`** when **Approved**; does **not** push unless Paul asks
- If changes are needed, create a fix / remedial prompt in `prompts/cursor/next/` (Grok does not edit source)

## Preventing Scope Creep

Scope creep has been one of the main issues so far. To reduce it, we apply these techniques (in rough order of preference):

1. **Extremely explicit scope boundaries** in the prompt (e.g. “Only modify files under `src/models/`. If you believe changes are needed elsewhere, stop and document them in `review-notes.md` instead of making them.”).

2. **Two-phase prompts** — First prompt is analysis + plan only. We review and approve the proposed scope before Cursor is allowed to implement.

3. **"Stop and escalate" rule** — If Cursor feels it must go outside the stated scope to keep the system working, it must halt, clearly document the problem, and create a follow-up prompt rather than making the out-of-scope changes itself.

4. **Narrower task slicing** — Break large alignment or cleanup efforts into smaller, tightly-scoped prompts (e.g. one prompt per major file or module).

We will continue refining these approaches based on experience.

### Scope Rules Template (Copy into Prompts)

When creating new prompts, include a section like this (customized per task):

**Scope Boundaries (Strict)**

You may only modify files under the following paths:
- `src/models/state.py`
- `src/models/__init__.py` (only if necessary for exports)

**Out of Scope (Do Not Touch)**

- `TODO.md` (Grok + Paul only — see Roadmap ownership)
- `src/agents/`
- `src/storage/`
- `src/mcp/`
- Any other files not explicitly listed above

If you determine that changes outside this scope are necessary to keep the system working:
- **Stop immediately.**
- Clearly document the problem in your `output.md` and `review-notes.md`.
- Do **not** make the out-of-scope changes.
- Create a follow-up prompt in `prompts/cursor/next/` describing what needs to be done instead.

This rule is mandatory. Violating scope boundaries will be treated as a failure to follow instructions.

## Test Execution Policy (Important for Speed)

To avoid slow full test runs during rapid iteration:

- **Default behavior**: Only ever run smoke tests unless explicitly required otherwise: `uv run pytest -m smoke -q`
- **Exception**: If your work involves *adding a new test* (or significantly changing one), Grok determines its category (you should document the assignment or ask explicitly). You **must immediately run the appropriate test(s)**:
  - Smoke tests: pure unit tests (stubs, mocks, monkeypatches only; no real DB/storage, no `run_query`, no full graph `ainvoke` or checkpointing).
  - Full tests: anything that exercises real storage, checkpoints, `run_query`, `build_core_graph`, or heavy integration (e.g. most of `test_core_graph.py` and the DB-using tests in `test_trace_capture.py`).
- **Grok decides the category**: Grok determines the category for any new test (you should note it or ask if unclear). Document the category in your `output.md`. If it is full, run the full suite (or at minimum the new test using the full marker) right away before claiming the task is complete.
- This policy applies even if a task prompt vaguely says "run tests" or "verify". Interpret "tests" as smoke-only unless the task is adding full-suite tests.
- Update the relevant test file with the correct `@pytest.mark.smoke` or `@pytest.mark.full` decorator as part of the change.
- See `pyproject.toml` for marker definitions, `README.md` and `TODO.md` for usage, and the current reset file for session context.

This keeps frequent work fast while ensuring new full tests are validated immediately.

## Current Status (as of creation)

This workflow is being established in late May 2026 to improve collaboration between Grok, Paul, and Cursor agents.

See `TODO.md` for the long-term task list between Grok and Paul.
See `docs/architecture.md` for the current architectural direction.
