# Output: Process raw_data.json → seed_crm.json

## Summary

Replaced the 12-person placeholder seed with **457** real name/firm pairs from `data/raw_data.json`, applying the requested deduplication rules. Backed up the old seed, updated README table row and `TODO.md`, and verified loading via `CoreStorage.seed_from_file()` on a fresh temp database.

## Duplicate analysis (runtime)

| Name | Raw entries | Firms |
|------|-------------|-------|
| Andrea Kalmans | 2 | Deus X Capital, Lontra Ventures |
| Kevin Zhang | 2 | Bain Capital Ventures, Upfront Ventures |
| Pete Townsend | 3 | Fabric Ventures, Outlier Ventures, Techstars |

**Applied rules:**
- Andrea Kalmans → kept **Lontra Ventures** only (excluded Deus X Capital)
- Pete Townsend → kept **Techstars** only (excluded Fabric Ventures, Outlier Ventures)
- Kevin Zhang → **both** entries kept (no user rule)

## Counts

| Metric | Value |
|--------|-------|
| Raw contacts | 460 |
| Rows excluded (dedup) | 3 |
| Final `people` count | **457** |
| ID format | `person-0001` … `person-0457` (4-digit zero-padded) |

## Verification

- Every entry has exactly `id`, `name`, `employer`; no empty employers.
- All 457 ids unique; JSON pretty-printed (2-space indent) + trailing newline.
- `Person.model_validate` on all rows — OK.
- Spot-checks: Andrea Kalmans → Lontra Ventures; Pete Townsend → Techstars; Kevin Zhang ×2.
- Fresh temp DB: `CoreStorage.seed_from_file` inserted **457** rows; lookups succeeded for Nichanan Kesonpat, Aaron Holiday, Andrea Kalmans, Pete Townsend.

## Decision record

- Preserved relative order from `raw_data.json["contacts"]` after filtering.
- Sequential ids assigned in that order starting at `person-0001`.
- No extra fields (`email`, `role`, etc.) — core-only per architecture.

## Files changed

| File | Action |
|------|--------|
| `data/seed_crm.json` | Replaced (457 records) |
| `data/seed_crm.json.bak` | Backup of 12-person placeholder |
| `README.md` | Seed table row updated |
| `TODO.md` | New **Data** section with completion note |
| `prompts/cursor/done/2026-06-01-1730-process-raw-data-to-seed-crm/` | Artifacts |

**Scope:** No `src/` or `tests/` changes.

## Follow-ups (not in scope)

- **Local DB:** Delete `data/mycelium.db` (or see `docs/database-notes.md`) so startup re-seeds from the new file.
- **README quick start** still uses `ada.lovelace@analytical.engine` examples from the old seed; update in a separate doc/UX task if desired.
- **Optional:** A canonical `data/prepare_seed.py` could regenerate from `raw_data.json`; documented here only, not implemented per scope.
- **Optional:** `list_people` MCP tool for browsing the full core set.

## In-progress cleanup

Removed only `prompts/cursor/in-progress/2026-06-01-1730-process-raw-data-to-seed-crm.md`.
