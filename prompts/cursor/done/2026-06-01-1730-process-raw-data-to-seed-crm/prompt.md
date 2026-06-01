# Task: Process raw_data.json into the initial seed_crm.json (464 name + firm pairs)

**Created:** 2026-06-01  
**For:** Cursor (as senior developer)  
**References:** `docs/architecture.md`, `prompts/cursor/WORKFLOW.md`, `TODO.md`, `prompts/system/CORE_PROMPT.md`

---

## Objective

Replace the placeholder `data/seed_crm.json` (12 famous-person samples) with the **first real MVP input file** containing "name, firm" pairs extracted from `data/raw_data.json` (after applying the explicit deduplication preferences for Andrea Kalmans and Pete Townsend).

The output must be a valid seed file that `CoreStorage.seed_from_file()` and the `Person` model can consume without changes: only the minimal core fields (`id`, `name`, `employer`).

This gives the system a realistic initial dataset (approximately 457 records) for Phase 1 testing and development.

---

## Key Facts (from analysis — re-analyze the current file at runtime)

- `raw_data.json` top-level: `owner`, `firm_count` (currently 220), `contacts[]` (currently 460 entries).
- Every contact has both `name` and `firm_name`.
- As of the latest update, 3 names still appear more than once in the raw file (Andrea Kalmans, Kevin Zhang, Pete Townsend). The user has explicitly requested the following handling for two of them (see Deduplication Rules below). Kevin Zhang was not mentioned, so both of its entries should be kept.

**Deduplication Rules (apply these when building the people list):**
- **Andrea Kalmans**: Include *only* the record where `firm_name == "Lontra Ventures"` (discard the Deus X Capital entry).
- **Pete Townsend**: Include *only* the record where `firm_name == "Techstars"` (discard the Fabric Ventures and Outlier Ventures entries).
- All other contacts (including both Kevin Zhang entries) are included as-is.

After applying the two rules above, the final seed is expected to contain **457** people records (460 raw contacts minus the 3 excluded rows).

**Decision record (include in your output.md):**
- Re-analyze duplicates at the start of the task and report what you found.
- Preserve the relative order of contacts from `raw_data.json["contacts"]` (after applying the dedup filters above).
- Generate zero-padded ids `person-0001` … `person-0457` (or whatever the final count is — use 4-digit padding).
- `name` ← `contact["name"]`
- `employer` ← `contact["firm_name"]`
- No other fields. No `extra`, no role/email/etc.

---

## Success Criteria

- [ ] `data/seed_crm.json` contains the correct final number of people entries (expected **457** after applying the deduplication rules above; confirm the actual count at runtime).
- [ ] Every entry has precisely the keys `id`, `name`, `employer` (employer is never null/empty).
- [ ] All ids are unique and correctly formatted (`person-` + 4-digit zero-padded number).
- [ ] The JSON is pretty-printed (2-space indent) + trailing newline.
- [ ] Old seed is backed up as `data/seed_crm.json.bak` (or `.old`).
- [ ] `README.md` is updated (the table row that says "12 sample CRM people" now accurately describes the real contacts from raw_data.json, including the deduplication applied for Andrea Kalmans and Pete Townsend).
- [ ] `TODO.md` receives a brief note (e.g. under a new "Data" section or High Priority) recording that the initial real seed has been created.
- [ ] The new seed file loads cleanly via the existing seeder (verified with a fresh temp DB + spot checks).
- [ ] All artifacts delivered to `prompts/cursor/done/2026-06-01-1730-process-raw-data-to-seed-crm/` exactly per WORKFLOW.md.
- [ ] Zero scope violations and no source code changes outside docs + data/.

---

## Scope Boundaries (Strict — Enforce)

**You may modify / create only:**

- `data/seed_crm.json` (the replacement)
- `data/seed_crm.json.bak` (backup of the 12-person version)
- `README.md` (update the one descriptive line + table)
- `TODO.md` (add a short status note)
- The required `prompts/cursor/done/.../` directory and its three files (`prompt.md`, `output.md`, optional `review.md`)

**You may read (read-only):**

- `data/raw_data.json`
- `data/seed_crm.json` (only to back it up)
- `src/storage/core.py` (to understand/verify the loader)
- `src/models/state.py` (Person model)
- `README.md`, `TODO.md`, `docs/architecture.md`, `prompts/cursor/WORKFLOW.md`
- `pyproject.toml` (to discover the correct run command, e.g. `uv run ...`)

**Out of Scope — Do Not Touch (stop and escalate if you think you must):**

- Any file under `src/` except for read-only inspection of the two model/storage files listed above.
- `tests/`
- `data/raw_data.json`
- `data/mycelium.db` or `checkpoints.sqlite` (do not mutate the real database in this task)
- Creation of new permanent scripts/ or data/prepare_*.py (if you believe a reusable generator script would be valuable later, *document the recommendation* in `output.md` but do not implement it now)
- Any other documentation or prompts

**If the work cannot be completed inside this scope:**  
Stop. Document the blocker clearly in `output.md`. Create a follow-up prompt in `prompts/cursor/next/` describing exactly what additional change is required. Never proceed outside the boundaries.

---

## Step-by-Step Instructions

1. **Claim the task (mandatory first action)**  
   - Scan `prompts/cursor/next/`.  
   - Sort the `.md` files alphabetically.  
   - Confirm this file (`2026-06-01-1730-process-raw-data-to-seed-crm.md`) is the oldest/only one.  
   - **Immediately move** it to `prompts/cursor/in-progress/`.  
   - Only after the move succeeds, continue. This is the parallel-safety claim per WORKFLOW.md.

2. **Backup the current seed**  
   Copy `data/seed_crm.json` → `data/seed_crm.json.bak` (overwrite the bak only if you must; prefer not to lose previous bak if it exists).

3. **Generate the new seed**  
   Write a small, self-contained Python snippet (you may use `python -c '...' ` or a short-lived `/tmp/seed_gen.py` that you delete afterwards).  
   The snippet must:
   - Load `data/raw_data.json`
   - First, analyze and report which names currently have multiple entries.
   - Apply the **Deduplication Rules** defined in the Key Facts section (keep only Lontra Ventures for Andrea Kalmans; only Techstars for Pete Townsend).
   - Build the people list while preserving relative order from the (filtered) contacts.
   - Assign sequential zero-padded ids starting at `person-0001`.
   - Build the `{"people": [ {"id": "person-0001", "name": ..., "employer": ...}, ... ]}` structure
   - Write the result to `data/seed_crm.json` with `json.dumps(..., indent=2)` + trailing newline
   - Print a clear summary including the raw contact count, how many rows were excluded for deduplication, and the final people count.

4. **Verify the output rigorously**
   - Confirm the final count matches what you calculated after applying the dedup rules (expected ~457).
   - Spot-check 3–4 entries, including the two specially handled names (Andrea Kalmans must be Lontra Ventures only; Pete Townsend must be Techstars only).
   - Confirm the JSON round-trips and validates against the `Person` model.
   - **Loader test (fresh DB):** Use `tempfile` + `CoreStorage` directly (bypass the singleton) to call `seed_from_file` on a brand-new temp database and assert the correct number of inserts + successful lookups for a couple of real names (e.g. "Nichanan Kesonpat", "Aaron Holiday", "Andrea Kalmans", "Pete Townsend").
   - Run the project's normal lint/type commands on any temp script you created (`uv run ruff check ...`, `uv run mypy ...` if applicable).

5. **Update documentation (minimal, accurate)**
   - `README.md`: Replace the "12 sample CRM people loaded on startup" description with something accurate like "460 contacts from raw_data.json (with deduplication applied for Andrea Kalmans and Pete Townsend) loaded on startup".
   - `TODO.md`: Add a short note (new "Data" subsection or under High Priority) recording completion of the initial real seed. Keep the note small and reviewable.

6. **Deliver artifacts (exactly per WORKFLOW.md)**
   - Create the directory `prompts/cursor/done/2026-06-01-1730-process-raw-data-to-seed-crm/`
   - Place a copy of this prompt inside it as `prompt.md`
   - Write a high-quality `output.md` containing:
     - Summary of actions taken
     - Exact counts and verification results (paste key log output)
     - Any decisions or observations (ordering, padding, duplicate-name handling, backup)
     - List of files changed
     - Open questions / recommended follow-ups (e.g. "To see the new data, delete or reset data/mycelium.db", "Consider whether we want a canonical `data/prepare_seed.py` in the future", "Should we also expose a `list_people` MCP tool that returns the full core set?")
   - Remove **only** the file you claimed from `prompts/cursor/in-progress/`
   - (Optional) Add an empty `review.md` as a placeholder for Paul/Grok feedback

7. **Git hygiene**  
   The changes (especially the large seed file) should be committed as a single, well-described unit when you are finished. Include the task slug in the commit message.

---

## Suggested Implementation Snippet (you may copy/adapt)

```python
import json
from pathlib import Path
from collections import defaultdict

raw_path = Path("data/raw_data.json")
out_path = Path("data/seed_crm.json")

raw = json.loads(raw_path.read_text(encoding="utf-8"))
contacts = raw["contacts"]

# Deduplication preferences (per user instructions)
PREFERRED_FIRMS = {
    "Andrea Kalmans": "Lontra Ventures",
    "Pete Townsend": "Techstars",
}

# Group by name to apply rules
name_to_recs = defaultdict(list)
for c in contacts:
    name = c.get("name")
    if name:
        name_to_recs[name].append(c)

# Build filtered list preserving original relative order
filtered_contacts = []
for c in contacts:
    name = c.get("name")
    if name in PREFERRED_FIRMS:
        if c.get("firm_name") == PREFERRED_FIRMS[name]:
            filtered_contacts.append(c)
    else:
        filtered_contacts.append(c)

people = []
for i, c in enumerate(filtered_contacts, 1):
    people.append({
        "id": f"person-{i:04d}",
        "name": c["name"],
        "employer": c["firm_name"],
    })

payload = {"people": people}
out_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
print(f"Raw contacts: {len(contacts)}")
print(f"Rows excluded for dedup: {len(contacts) - len(filtered_contacts)}")
print(f"Wrote {len(people)} people to {out_path}")
```

Use a fresh DB + the real `CoreStorage` class for the verification step (do not rely on `get_storage()` singleton during the test).

---

## Principles to Internalize While Working

- From `docs/architecture.md`: the core is deliberately tiny. This task is *only* about producing the minimal name/firm seed. Everything else (emails, roles, LinkedIn, specialist agents, etc.) is explicitly out of scope for the core table.
- From `prompts/system/CORE_PROMPT.md` and WORKFLOW.md: small, reviewable changes; strict scope discipline; high-quality artifacts for the `done/` record.
- Prefer deletion/simplification. Do not add new abstractions "just in case."

---

**When you have completed everything above, the only thing left in `prompts/cursor/next/` should be this task's done directory under the proper location, and you should have reported success.**

Good luck — this is an important milestone for the MVP data foundation.
