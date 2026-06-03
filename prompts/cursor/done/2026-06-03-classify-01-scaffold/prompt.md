# Task: Classification Engine Phase 1 - Slice 01: Scaffold seed data and package

**Read these first (mandatory):**
- `docs/plans/classification-engine-phase1.md` (the approved plan - the immutable source of truth for the overall design, lightweight priority note, exact seed JSON, Pydantic models, CategoryTree sketch, supervisor integration diff, risks, and verification commands)
- `prompts/cursor/WORKFLOW.md`
- `.cursor/rules/04-cursor-workflow.mdc`
- `docs/architecture.md` (thin supervisor, query-only, small/reviewable changes, scope discipline)

**Objective**
Perform the scaffold portion of the approved plan (Step 1 + skeleton for Step 2): create the committed `data/categories.json` with the exact initial seed (5 categories, 18 attributes including demographic, contact, relationships), and scaffold the `src/agents/classification/` package with `__init__.py`, `models.py` (the 4 Pydantic classes), and `engine.py` (class stubs only, no implementation logic).

This is a pure addition with zero changes to existing behavior or files. It delivers the data and package structure for subsequent small slices.

**Lightweight priority (from approved plan - obey strictly)**
"Keep implementation as lightweight as possible in early steps. Prioritize getting `classify()` + supervisor injection working cleanly before polishing `refresh_from_llm` and atomic saves. Err on the side of simplicity for Phase 1."

For this slice: stubs only, no fancy code, no atomic save yet (that comes in later polish if the diff is small).

**Constraints & Principles**
- Strictly limited scope (see box below).
- Reference and align with the approved classification plan and `docs/architecture.md`.
- No changes to existing source, tests (except possibly adding a future test in later slice), docs, or the large superseded prompt.
- Small, reviewable change only.
- Follow "Prefer simplification".
- After implementation, only run smoke tests (`uv run pytest -m smoke -q`).
- The prompt for Cursor must follow the claiming process in WORKFLOW.md exactly.

**Context**
- The approved plan `docs/plans/classification-engine-phase1.md` has the exact content for the seed JSON in its "Initial Seed Content for categories.json" section, and the exact Pydantic class definitions in "Pydantic Models (src/agents/classification/models.py)".
- Current state: no `data/categories.json`, no `src/agents/classification/` directory.
- This slice is the first of a sequence of small prompts (see the planning document for the full 5-slice breakdown). Each slice is independently reviewable.
- The large previous prompt `2026-06-07-classification-engine-phase1.md` in next/ is superseded by this sequence of small slices (per user direction for small verifiable tasks like the 2026-06-05-10xx- and 2026-06-06-mcp-* series). Do not work on it.

See the approved plan for the full "Current state", "Phase 1 Goal", and "Proposed Final File/Folder Structure".

**Exact Steps (perform in order)**
1. **Claim the task first (mandatory per WORKFLOW.md)**: Scan `prompts/cursor/next/`, select the oldest (this one), **immediately move** it to `prompts/cursor/in-progress/2026-06-03-classify-01-scaffold/prompt.md` (or the exact name). Only then begin work. Document the move in your output.md. Never work on a file still in next/.

2. **Discovery (read-only)**: 
   - Read the approved `docs/plans/classification-engine-phase1.md` (focus on the seed JSON section, the Pydantic models section, the "Proposed Final File/Folder Structure", the lightweight note, and Step 1 verification commands).
   - Read `docs/architecture.md` sections on supervisor, non-core, and collaboration model.
   - Run `git status` and `ls data/ src/agents/ ` to confirm current state (no categories.json, no classification/ dir).
   - Confirm the two Kevin Zhang entries exist in seed for later regression (but do not change anything).

3. **Create the seed data (exact content from approved plan)**:
   - Create `data/categories.json` with the exact JSON from the approved plan's "Initial Seed Content for categories.json" section (version 1.0, the 5 categories with description/assigned_agent/examples, the attribute_map with 18 entries, last_updated and model_used as specified).
   - `git add data/categories.json`.

4. **Scaffold the classification package (stubs only)**:
   - Create the directory `src/agents/classification/`.
   - Create `src/agents/classification/__init__.py` with:
     ```python
     """Classification Engine for Phase 1 Supervisor Intelligence (see approved plan)."""
     from .engine import get_category_tree, CategoryTree, reset_category_tree
     __all__ = ["get_category_tree", "CategoryTree", "reset_category_tree"]
     ```
   - Create `src/agents/classification/models.py` with the exact 4 Pydantic classes from the approved plan's "Pydantic Models" section (Category, CategoryTreeData, ClassificationResult, CategoryProposal). Use the exact docstrings and fields.
   - Create `src/agents/classification/engine.py` with:
     - The imports and _default_categories_path from the approved design.
     - The _SEED_CATEGORIES constant (exact from approved).
     - A stub CategoryTree class with __init__, _load, _save (simple write_text for now, per lightweight), _create_seed, reload, classify (can raise NotImplemented or return a dummy "unknown" for now), get_categories, get_category_tree and reset_category_tree at module level (simple global).
     - A comment: "Full implementation in next small slice (02-engine). See approved plan 'Detailed Design of CategoryTree Class / Module'."
     - Do not implement refresh_from_llm logic yet (stub that says "implemented in later slice").

5. **Verification (smoke only)**:
   - `uv run pytest -m smoke -q` (must stay green; no breakage to existing).
   - `git status` (should show exactly the new data file + 3 new files in classification/).
   - `cat data/categories.json | head -30` (confirm exact seed).
   - `uv run python -c '
import json
import pprint
data = json.load(open("data/categories.json"))
pprint.pprint(list(data["attribute_map"].keys()))
print("seed ok")
from agents.classification import get_category_tree
print("import ok")
t = get_category_tree()
print("get ok")
' ` (confirm the package imports and basic get works; the classify may be stub).

6. **Output artifacts (exactly per WORKFLOW)**:
   - Create `prompts/cursor/done/2026-06-03-classify-01-scaffold/output.md` with:
     - Summary of what was done and decisions (e.g. "followed lightweight by using simple write_text stub; exact content copied from approved plan").
     - The diffs or `git diff --stat` + key new file contents.
     - Full output of all verification commands.
     - Confirmation scope respected (only the 4 items).
     - Any open questions (e.g. "ready for slice 02?").
   - Move/copy this prompt into the done/ dir as `prompt.md`.
   - Remove **only** the file you claimed from `prompts/cursor/in-progress/`.
   - Optionally create review.md placeholder.

7. **Process hygiene**:
   - Follow claiming exactly.
   - If you feel you must edit outside the scope box to "make it work", **stop immediately**, document in output.md, and create a follow-up prompt instead of making the change.
   - Do not touch the superseded large prompt or the approved plan.
   - Do not implement any classify logic or wire to supervisor/state (that is slice 03).

## Scope Boundaries (Strict)
You may only create or modify files under the following paths:
- `data/categories.json`
- `src/agents/classification/__init__.py`
- `src/agents/classification/models.py`
- `src/agents/classification/engine.py`

**Out of Scope (Do Not Touch)**
- Any file under `src/models/`, `src/agents/supervisor.py`, `src/agents/core_data.py`, `src/agents/responses.py`, `tests/`, `docs/` (except running verification commands), `src/mycelium_mcp/`, `src/graphs/`, `src/main.py`, `src/storage/`, the large prompt in next/, the approved plan, TODO.md, or anything else.
- Do not implement any real logic in engine.py (stubs only).
- Do not run full tests or make behavior changes.

If you determine that changes outside this scope are necessary to keep the system working:
- **Stop immediately.**
- Clearly document the problem in your `output.md`.
- Do **not** make the out-of-scope changes.
- Create a follow-up prompt in `prompts/cursor/next/` describing what needs to be done instead.

This rule is mandatory. Violating scope boundaries will be treated as a failure to follow instructions.

## Test Execution Policy
- Default: `uv run pytest -m smoke -q` only.
- No new tests required in this slice (the engine test comes in slice 02).
- If you feel a test is needed, stop and document; Grok will decide.

## Required Output Location & Artifacts
- `prompts/cursor/done/2026-06-03-classify-01-scaffold/output.md`
- The claimed prompt moved to the done/ subdir as `prompt.md`

Follow the claiming process in `prompts/cursor/WORKFLOW.md` exactly before doing any implementation work.

## Suggested Acceptance (for Grok + Paul review)
After Cursor delivers, we will review the output.md, confirm only the 4 files were touched, re-run the verification commands, confirm the seed JSON and package scaffold match the approved plan exactly, confirm smoke green and no behavior change, add review.md if needed, then (if good) commit this small slice and prepare the next small prompt (02-engine).

Start by claiming the file (move to in-progress/). Good luck — make the change small, explicit, and reviewable. Reference the approved plan for every detail.