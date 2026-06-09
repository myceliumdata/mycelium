# Research robustness — design backlog

**Status:** Design backlog (Paul + Grok, June 2026)  
**Related:** [`specialist-research-phase1.md`](specialist-research-phase1.md) (implemented), slice `2010` (in progress), Angela Murphy @ Talentcare incident

This document captures **network-agnostic** ideas for making specialist field research more reliable. It deliberately avoids CRM-only hacks (e.g. hardcoded `employer`-in-snippet validation). Items already on `TODO.md` are cross-linked, not duplicated in full.

---

## Problem layers

Wrong-person research (Angela Murphy example) can fail at several layers:

| Layer | Example failure | In progress |
|-------|-----------------|-------------|
| **Bind in context** | Missing or wrong `context.bind` | Fixed (entity protocol) |
| **Search query** | Name-only query when bind has disambiguators | Slice `2010` Part A (MVR-driven) |
| **Evidence selection** | IMDB spouse chosen despite Talentcare hit in same result set | Partially prompt-only today |
| **Persistence gate** | `found` saved without corroboration | Min confidence + sources URL only |
| **Operator recovery** | Wrong value stuck as `found` | Backlog (force re-research, correction) |

Slice **`2010`** addresses **search queries** (MVR bind disambiguation) and **context** (peer specialist findings). It may help Angela if professional/social already stored Talentcare-linked profiles — but **will not fix** wrong synthesis when the model ignores corroborating hits. The items below target that gap.

---

## Principles

1. **Network-agnostic core** — behavior driven by `network.json` (`MvrPolicy.bind_fields`, optional future `research` policy), not hardcoded CRM fields.
2. **Category-scoped quality** — relationships vs professional vs financial have different source-trust norms; express in category metadata/fragments, not employer checks in `research.py`.
3. **Prompt first, enforce when needed** — prefer stronger prompts + peer context; add code guardrails only where models repeatedly fail compliance.
4. **Fail to `na`** — ambiguous multi-person result sets should not become confident `found` guesses.

---

## Backlog items

### 1. Category source-quality rules (prompt / metadata)

**Idea:** Each category declares what counts as sufficient evidence for `found`, independent of bind field names.

| Category | Guidance (examples) |
|----------|---------------------|
| `relationships` | Do not treat entertainment DBs (IMDB), genealogy aggregators, or generic social profiles as sole proof of spouse/partner without bind corroboration |
| `professional` | Prefer employer site, LinkedIn, filings over people-search directories |
| `financial` | Require filings, news, or official disclosures |
| `social` | Prefer verified or widely cross-cited profiles |

**Where:** `data/categories.json` extended hints, `research/<category>.md.j2` fragments, or a shared `_source_quality.j2` partial keyed by category.

**Not:** “employer string must appear in snippet” in Python.

**Effort:** Small–medium (prompt + tests on fragment text).

---

### 2. Multi-identity conflict → `na` (homonym clustering)

**Idea:** When top `web_search` results clearly describe **different people** (incompatible employers, geographies, lifetimes, industries), the model must not merge them into one `found` answer. Return `na` with reason: *“Search results describe multiple distinct people; insufficient bind corroboration.”*

**Implementation options:**

| Approach | Pros | Cons |
|----------|------|------|
| **Prompt-only** | No code coupling | Model may ignore (Angela case) |
| **Lightweight heuristic** | Scan snippets for bind tokens; flag if top hits split into incompatible clusters | Heuristic maintenance |
| **Second LLM pass** | “Cluster these hits by person; which cluster matches bind + peers?” | Latency, cost |

**Network-agnostic:** Uses `bind_disambiguators` from MVR + peer context, not employer-specific logic.

**Effort:** Medium (prompt); larger if heuristic or second pass.

---

### 3. MVR-generic first-query enforcement (tool loop)

**Idea:** If `has_extra_bind_disambiguators`, the **first** `web_search` tool call must include all non-name bind values in the query string. If the model omits them, **reject the tool result** (or auto-retry once) with a ToolMessage: *“Query must include bind values: …”*

**Distinction from slice `2000`:** Driven by `MvrPolicy.bind_fields` values, not `if employer` branches. Works for `account_id`, `vin`, etc.

**Effort:** Small–medium in `src/tools/research.py` (`_run_llm_loop`).

**Risk:** False rejects if model uses equivalent tokens (abbreviations, parent company names). May need fuzzy match or allow one retry.

---

### 4. Bind-consistent source gate before `found` (generic persistence)

**Idea:** Before persisting `status: found`, verify cited sources are **consistent with the entity’s bind disambiguators** — not that a specific field name appears, but that the evidence cluster matches the bound identity.

**Examples:**

- CRM: spouse claim supported only by IMDB with no Talentcare link → downgrade to `na`
- Hypothetical parts network: claim supported by VIN mismatch → `na`

**Implementation:** Optional `research.bind_corroboration` in `network.json`:

```json
{
  "research": {
    "require_bind_corroboration_for_found": true,
    "corroboration_mode": "any_source_snippet"
  }
}
```

Default **off** or **lenient** for Phase 1; networks opt in. Implementation reads `bind_disambiguators` dynamically.

**Rejected pattern:** Hardcoding `employer in sources` in core framework without network policy.

**Effort:** Medium–large.

---

### 5. Evidence synthesis step (structured clustering)

**Idea:** Split research into two phases:

1. **Gather** — tool loop returns raw hits (today).
2. **Synthesize** — structured step: group hits by implied identity; select cluster matching `bind` + `context.specialists`; then propose `ResearchProposal`.

Could use `with_structured_output` on a summary of hits before field proposals.

**Effort:** Large (runner redesign).

**Benefit:** Addresses Angela-style failure where gather succeeded but synthesis picked wrong cluster.

---

### 6. Network `research` policy block (`network.json`)

**Idea:** Extend per-network config beside `mvr`:

| Key | Purpose |
|-----|---------|
| `bind_corroboration` | Strictness for `found` vs bind |
| `forbidden_domains` | Per-category domain blocklist (e.g. `imdb.com` for relationships) |
| `min_distinct_sources` | Require N independent URLs for `found` |
| `max_tool_rounds` | Override env default |

Loaded by `tools.research` alongside `load_mvr()`. Keeps framework generic; CRM/network packs policy.

**Effort:** Medium.

---

### 7. Research audit enhancements

**Idea:** Extend `meta.research_audit` for operator debug (no LangSmith required):

| Field | Purpose |
|-------|---------|
| `context_bind` | MVR-filtered bind disambiguators (slice `2010`) |
| `first_query` | First `web_search` query string |
| `peer_categories` | Which peer specialist slices were in context |
| `bind_corroboration_result` | If gate #4 implemented: pass/fail + reason |

**Effort:** Small.

---

### 8. Operator recovery (product — already on `TODO.md`)

Not repeated here in full. Essential for cases automation cannot disambiguate:

- **Operator attribute correction** — manual override with provenance
- **Operator force re-research** — explicit retry + optional hint text merged into research context

Angela Murphy: even with all prompt fixes, operators need a path to clear wrong `found` and retry.

See `TODO.md` → *Operator attribute correction*, *Operator force re-research*.

---

### 9. Richer tool surface (already on `TODO.md`)

Tavily `web_search` alone is weak for disambiguation (ranking favors SEO/homonyms). Future networks may need structured lookups (LinkedIn API, company registries, etc.).

See `TODO.md` → *Agent tools review*.

---

## Suggested sequencing

| Priority | Item | Rationale |
|----------|------|-----------|
| **Now** | `2010` — MVR bind disambiguation + peer context | Foundation; network-agnostic |
| **Next** | #1 Category source-quality | Cheap; helps relationships without CRM logic |
| **Next** | #3 First-query enforcement | Closes loop when prompts ignored |
| **Then** | #2 Multi-identity → `na` | Addresses Angela synthesis failure |
| **Then** | #7 Audit (`first_query`) | Debug without LangSmith |
| **Later** | #6 Network research policy + #4 Bind corroboration gate | Per-network strictness |
| **Later** | #5 Evidence synthesis step | Bigger runner change |
| **Product** | #8 Operator tools | Human-in-the-loop for long tail |

---

## Explicitly deprioritized

| Idea | Why |
|------|-----|
| Hardcoded `employer in source snippet` in `research.py` | CRM-shaped; superseded by MVR-generic policy (#4, #6) |
| Slice `2000` employer-only Jinja branches | Reverted; generalized in `2010` |
| Regen-all-specialists for prompt-only tweaks | Research templates load at runtime; regen only when `specialist_agent.py.j2` changes |

---

## References

- Angela Murphy incident — LangSmith trace, June 2026 (bind correct; synthesis wrong)
- Slice `2026-06-09-2000-research-prompt-bind-disambiguation` — approved then superseded
- Slice `2026-06-09-2010-research-prompt-full-peer-context` — MVR + peers
- `src/network/mvr.py` — `MvrPolicy`, `load_mvr()`
- `src/tools/research.py` — runner, prompts, audit