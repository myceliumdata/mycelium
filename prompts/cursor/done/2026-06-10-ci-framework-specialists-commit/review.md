# Review: CI fix — commit framework fallback specialists

**Verdict: Approved**

**Reviewer:** Grok (June 2026)

---

## Summary

Fix is correct and minimal: removed gitignore rule, committed four regenerated framework specialists, maintainer notes in `.gitignore` + `base.py`. **279 smoke tests pass** on fresh tree; ruff clean; no `SeedRecord` in specialists.

CI should go green on next push.