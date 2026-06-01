# Task: Rename CoreIdentityAccessor to CoreIdentity

**Created:** 2026-06-02

**Objective:** Rename the class `CoreIdentityAccessor` to `CoreIdentity` (and update all related references) to better reflect its role as the agent responsible for the system's core identity data.

**Context:**  
Paul has decided that the name should be `CoreIdentity` rather than `CoreIdentityAccessor`. The goal is for the name to represent the concept/agent itself ("from the outside it *is* the core data"), not just an accessor or adapter to the data.

---

## Scope (Strict)

**You must rename:**
- The class `CoreIdentityAccessor` → `CoreIdentity` in `src/agents/core_identity.py`
- All imports and type hints referencing it
- The internal singleton variable (currently `_accessor`)
- Docstrings that use the old name or describe it as an "accessor"

**Files you are allowed to modify:**
- `src/agents/core_identity.py`
- `src/agents/routing.py`
- `tests/test_supervisor_routing.py`
- `TODO.md`

**You must NOT modify:**
- Any files under `prompts/cursor/done/` (these are historical records)
- Any other documentation or code outside the files listed above

---

## Step-by-Step Instructions

1. **Claim the task**
   - Move this file from `prompts/cursor/next/` to `prompts/cursor/in-progress/`.

2. **Perform the rename**
   - Rename the class `CoreIdentityAccessor` to `CoreIdentity`.
   - Update the module docstring in `core_identity.py` to better reflect the new intent (it is the Core Identity agent, not just an accessor).
   - Update the class docstring accordingly.
   - Rename the private singleton from `_accessor` to something appropriate (e.g. `_core_identity`).
   - Update the `get_core_identity()` function's return type and docstring.
   - Update `reset_core_identity()` docstring if needed.
   - Update the import and type hint in `src/agents/routing.py`.
   - Update the variable usage inside `evaluate_supervisor_turn` (currently uses `accessor`).
   - Update the test file (`tests/test_supervisor_routing.py`).
   - Update the reference in `TODO.md`.

3. **Improve docstrings (lightly)**
   - While renaming, update the module and class docstrings in `core_identity.py` to describe it as the Core Identity agent responsible for the core person data (id, name, employer), rather than just an "accessor" or "adapter".

4. **Verify**
   - Run `uv run pytest`
   - Run `uv run ruff check src tests`
   - Confirm there are no remaining references to `CoreIdentityAccessor` in the allowed files (except inside historical prompt/review files, which you must not touch).

5. **Deliver artifacts**
   - Create the done folder: `prompts/cursor/done/2026-06-02-1200-rename-coreidentityaccessor-to-coreidentity/`
   - Include `prompt.md`, a clear `output.md` describing the changes, and any relevant notes.
   - Remove only this file from `in-progress/`.

---

## Success Criteria

- [ ] Class is now named `CoreIdentity` everywhere in the allowed files.
- [ ] `get_core_identity()` returns `CoreIdentity`.
- [ ] All references in `routing.py`, the test file, and `TODO.md` are updated.
- [ ] Docstrings have been lightly improved to reflect the new naming intent.
- [ ] No behavior has changed.
- [ ] Tests pass and ruff is clean.
- [ ] No files outside the allowed list were modified.

---

**Keep this change narrow and mechanical.** This is a pure rename + light docstring refresh. Do not combine it with other refactors.