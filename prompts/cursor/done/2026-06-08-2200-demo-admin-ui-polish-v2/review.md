# Review: Demo admin UI polish v2 (`2026-06-08-2200`)

**Reviewer:** Grok  
**Date:** 2026-06-08  
**Commit:** `c025558`  
**Verdict:** **Approved**

---

## Scope check

| Requirement | Status |
|-------------|--------|
| Overview: `✅/❌ Categories` (not Ontology) | ✅ |
| Guide card inner summary: **Categories** | ✅ |
| Card title: **Network guide & ontology** | ✅ |
| Entity lookup **Category** / **All** unchanged | ✅ |
| Guide card wrapped in collapsible `<details>`, collapsed on load | ✅ |
| Inner Author guide + Categories nested `<details>`, collapsed | ✅ |
| Overview stays always visible | ✅ |
| Unified `.disclosure-summary` arrows (1.1em) on all summaries | ✅ |
| Specialist rows uncontrolled `<details>`, stable `key={category}` | ✅ |
| `fetchJson` HTML guard + 200-char truncation | ✅ |
| v1 poll / visibility / error split preserved | ✅ |
| Governance: no `TODO.md` edit | ✅ |
| `output.md` + **For Grok + Paul** | ✅ |
| `npm run build` | ✅ |

---

## Verification (Grok re-run)

```text
cd admin-ui && npm run build  → success
```

Paul manual: specialist expand in place (no `index.html` flash) — per `output.md` acceptance.

---

## What looks good

- **Specialist fix** — removing controlled `open`/`onToggle` is the right call; stable keys preserve expand state across polls.
- **`api.ts`** — `looksLikeHtml`, `truncateBody`, and `JSON.parse` fallback give clear operator errors without dumping SPA HTML.
- **Guide card** — outer collapsible matches Entity lookup; inner sections uncontrolled (simpler than v1’s partially-controlled nesting).
- **CSS** — single `.disclosure-summary` source of truth for arrows.

---

## Issues

None blocking.

---

## Decision

**Approve.** Bundled with v3 review; Paul hands-on smoke on live queries remains the real acceptance test for specialist expand + poll.