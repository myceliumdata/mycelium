# Bootstrap experiment v0 — first results

**Date:** 2026-06-16  
**Script:** `examples/networks/baseball/bootstrap_experiment.py`

---

## What ran

1. Ingest Lahman CSVs → SQLite warehouse (`People`, `Teams`, `Appearances`, `Batting`, `Pitching`, `TeamsFranchises`)
2. Enumerate distinct season team labels from warehouse (agent/specialist discovers `Teams.name` in heuristic path)
3. **Auto-commit** all labels as full canonical team names (uuid4)
4. Optional **LLM enrichment** (`--llm`): which table/column + aliases for sample — merged onto full list

---

## Results

| Mode | Teams committed | Notes |
|------|----------------:|-------|
| `--no-llm` | 241/241 | Distinct `Teams.name` strings as canon |
| `--llm` (first try) | 40/241 | Bug: prompt sent only 40-label sample |
| `--llm` (full list) | 149/241 | Model did not return complete JSON |
| **`--llm` hybrid** | **241/241** | Heuristic enumerate all + LLM alias enrichment on sample |

---

## Learnings

1. **Auto-commit all distinct labels** works for Lahman fan teams without hand labeling.
2. **LLM cannot reliably emit 241 structured rows in one shot** — use LLM for **strategy + alias enrichment**, not full enumeration (v0).
3. **Hybrid matches design:** network specialist explores schema; warehouse enumeration is mechanical; LLM adds shorthand aliases (`LA Dodgers` → `Los Angeles Dodgers` when present).
4. **Next:** player registry + multi-alias `(name, team)` index; wire bootstrap into framework.

---

*Archived June 2026.*