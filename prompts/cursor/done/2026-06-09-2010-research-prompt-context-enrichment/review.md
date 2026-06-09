# Review — Research prompt context enrichment (`2010`)

**Verdict: Approved**

Reviewed 2026-06-09 (Grok). Re-ran smoke tests locally: 23 passed; ruff clean.

## What landed

| Requirement | Status |
|-------------|--------|
| MVR-driven bind disambiguation (`bind_disambiguators`, `has_extra_bind_disambiguators`, `load_mvr`) | ✅ No `bind_employer` / `bind_has_employer` hardcoding |
| `_disambiguation.j2` loops bind fields generically | ✅ |
| `_bind_search_hint.j2` + `_system.j2` shared partials | ✅ |
| Peer context in `_research_context()` (template) | ✅ |
| `peer_specialists_for_entity()` + `_peer_context.j2` in prompts | ✅ Pending peers omitted from header |
| `relationships.md.j2` category homonym guidance | ✅ Category-scoped, not CRM |
| `context_bind` audit = MVR-filtered disambiguators | ✅ |
| Smoke tests: CRM employer, name-only, custom `account_id` MVR, peers, audit | ✅ |

CRM default MVR still produces `employer: Talentcare` disambiguation as a consequence of `bind_fields`, not a special case. Custom MVR test proves generalization.

## Nits (non-blocking)

1. **Network specialist regen for peers** — Template updated; `relationships_specialist` / `financial_specialist` live under network `specialists/` (gitignored). Paul must regen network specialists (e.g. `./bin/refresh-example-network crm` or Agent Factory) for **peer context** on relationships research. **MVR bind disambiguation** works without regen (lives in `tools.research` + runtime templates).

2. **`_research_context` peers include `pending` fields in JSON** — `peer_specialists_for_entity()` omits pending from the plain-text header only. Acceptable; optional polish later.

3. **`examples/networks/crm/specialists/contact_specialist.py`** — Still old `_research_context` (no peers). Stale example copy; network runtime is authoritative.

## Manual sign-off (Paul)

After commit + admin restart + clear `spouse` storage:

- LangSmith user message should start with `DISAMBIGUATION` listing `employer: Talentcare` (MVR, not employer special-case).
- First `web_search` should include `Talentcare`.
- Peer block appears only after network `relationships_specialist` regen **and** peer categories have non-pending data for the entity.

Angela synthesis failure (wrong spouse from IMDB) may persist — out of scope for `2010`; see `docs/plans/research-robustness-backlog.md`.

## Commit

Suggested: `feat(research): MVR bind disambiguation and peer specialist context in prompts`