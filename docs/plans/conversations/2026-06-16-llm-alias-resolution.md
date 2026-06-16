# LLM alias resolution — design note

**Date:** 2026-06-16  
**Participants:** Paul + Grok/Cursor  
**Status:** Direction locked for design; not implemented  
**Related:** [`fuzzy-lookup-policy.md`](../fuzzy-lookup-policy.md), [`baseball-example-program.md`](../baseball-example-program.md)

---

## Problem

Bind-field fuzzy matching today uses `SequenceMatcher` — strong on **typos**, weak on **shorthand and nicknames**:

| Query | Target | Works today? |
|-------|--------|--------------|
| `645 venture` | `645 Ventures` | ✅ typo |
| `645` | `645 Ventures` | ❌ |
| `ibm` | `IBM Corporation` | ❌ |
| `Yanks` | `New York Yankees` | ❌ (expected) |

TODO lists “fuzzy match upgrades (aliases & prefixes)” — explicit prefix index / alias table would complicate the framework per domain.

---

## Direction (Paul)

Use an **LLM with domain context** when exact + sequence fuzzy fail:

- CRM: *“In the context of companies, what could `465` refer to?”*
- Baseball: *“In the context of baseball teams, what could `Yanks` refer to?”*

Return canonical MVR field value(s) → existing `lookup_suggested` / `suggested_lookup` retry contract.

**Assumption:** **local LLMs** eventually — inference cost acceptable; no need to maintain huge static alias maps in code.

**Goal:** avoid explicit alias/prefix infrastructure unless the LLM path proves insufficient.

---

## Distinction

**LLM aliases** — expand nicknames/shorthand to canonical bind values.

**Multi-alias bind index** (baseball players) — many exact `(name, team)` pairs → one uuid after the canonical team name is known (Aaron + Braves / Aaron + Red Sox). Not nickname expansion; different mechanism.

---

*Archived from design discussion, June 2026.*