# Mycelium — TODO

Open tasks and roadmap (**Grok + Paul only** — Cursor reads for context, does not edit; see `prompts/cursor/WORKFLOW.md`).  
**New contributors:** [`docs/onboarding.md`](docs/onboarding.md). **Architecture:** [`docs/architecture.md`](docs/architecture.md).  
**Cursor queue:** `prompts/cursor/next/`. **Website:** `../mycelium-website/prompts/cursor/next/`.

**Shipped history:** `docs/plans/`, `prompts/cursor/done/`, git log.

---

## Next up (Paul)

- [ ] **Program 4 — Operator write** — Admin edit + force re-research UI (deferred from Program 3). Plan TBD.
- [ ] **Non-CRM example network** — Second committed example beside `crm` / `empty-crm` / `crm-metering`: distinct MVR `bind_fields`, ontology, and seed (not people-at-funds). `examples/networks/<name>/` + `refresh-example-network` + onboarding/docs second path; CRM stays default. Domain TBD (e.g. companies, vehicles — see [`docs/plans/networks-terminology.md`](docs/plans/networks-terminology.md) vision).

### Shipped (2026-06-14)

- [x] **Program 3 — Entity protocol legacy cleanup** — Gate **CLEAR**; tag `program_3`; polish **1560** (P1–P4 `require_full_bind_values`, fail-loud load). Slices 1500–1555 + 1560 + admin poll fix (1555). [`docs/manual-checks/2026-06-14-program3-post-program-gate.md`](docs/manual-checks/2026-06-14-program3-post-program-gate.md).

---

## OSS collaboration (Paul + Grok)

External contributors should not be forced into the Grok + Cursor handoff. Open decisions:

- [ ] **CONTRIBUTING.md** — Ignore `prompts/cursor/`; normal PRs; `./bin/ci-local` sufficient.
- [ ] **Soften always-on Cursor rule** — `alwaysApply: false` on `04-cursor-workflow.mdc`, or move maintainer rules out of public tree.
- [ ] **Gitignore local Cursor config** — `.cursor/permissions.json` at minimum.
- [ ] **Optional: split maintainer ops** — `prompts/cursor/`, `AGENTS.md`, `.cursor/rules/` in private meta repo vs public framework.

**Reference:** `docs/onboarding.md`; `prompts/cursor/README.md` (maintainers only).

---

## Process (Grok + Paul)

- **Website review after major pushes** — Review [myceliumdata.org](https://myceliumdata.org) vs `docs/architecture.md` + `docs/onboarding.md`. Queue in **`../mycelium-website/prompts/cursor/next/`**. Paul pushes and deploys.

---

## Admin UI (open)

- [ ] **Admin auth** — localhost-only today; design before remote admin.
- [ ] **Binding context** — full negotiation metadata on `/status`; query panel binding UX.
- [ ] **Edit / correct attribute values** — see **Operator attribute correction** below.
- [ ] **Force re-research** — see **Operator force re-research** below.

---

## Brand

- [ ] **Explainer video** — *de-prioritized*; short networks intro when time allows.

---

## Query, entity & research (open)

- [ ] **Settlement protocol** — Real x402 `PaymentProvider`, fundable-wallet harness, HTTP 402 gateway, rebate/pool ledger. Deferred from metering Slice 11.
- [ ] **Per-record query messages (multi-match)** — Collective `message` today; per-id status when attrs diverge per match.
- [ ] **Multi-turn thread semantics** — Reuse specialist cache across attributes on one `thread_id` without redundant research.
- [ ] **Long-running threads** — Suspend and ask client for clarification (`thread_id` + checkpoints).
- [ ] **Search indices** — Scale partial lookup + secondary indices (email → id, etc.). Design when beyond CRM scale.
- [ ] **Fuzzy match upgrades (aliases & prefixes)** — `645` → 645 Ventures, `ibm` → IBM; prefix index, alias table, or token-overlap. Policy: [`docs/plans/fuzzy-lookup-policy.md`](docs/plans/fuzzy-lookup-policy.md).
- [ ] **Query / search any field** — Lookup/search on extended attrs, not only MVR/indexed fields; fuzzy on 0-hit. After index story matures.
- [ ] **Operator attribute correction** — Admin (primary): view/edit specialist storage values, operator override provenance, re-research policy.
- [ ] **Operator force re-research** — Explicit retry per entity + attribute; optional operator hints in research context.
- [ ] **Research robustness** — [`docs/plans/research-robustness-backlog.md`](docs/plans/research-robustness-backlog.md): source-quality rules, multi-identity → `na`, `network.json` research policy.
- [ ] **Data attribution (product — USP)** — MCP/`describe_network` surfacing, staleness/re-research policy beyond Slice 8 basics.
- [ ] **Seed export (`export-growth-seed`)** — Validated `entities.json` → `seed.json` fragment.
- [ ] **Seed vs grown entity linking** — Network-type-specific merge/override rules.

---

## Future / deferred

- [ ] **Toolbox** — TBD.
- [ ] **Agent tools review** — Catalog tools by domain; framework vs per-network packs; factory binding.
- [ ] **Per-network LangSmith projects** — Optional `mycelium-<network>` per root.
- [ ] **Non-person seed schemas** — Generic entity seed beyond `people[]`.
- [ ] **`network regen-ontology`** — Re-run creation prompt on existing root.
- [ ] **Per-network credentials** — vs framework `.env` today.
- [ ] **Distributed network discovery** — Prerequisite for inter-network handoff.
- [ ] **Inter-network handoff** — Cross-network query routing.
- [ ] **Data addition (internal)** — New core records without public `provided_data`.
- [ ] **Response builders** — Refactor `assemble_response` / message shaping.
- [ ] **MCP packaging** — In-repo vs extract.
- [ ] **CoreStorage DI** — When multiple agents share storage.
- [ ] **Release / versioning** strategy.
- [ ] **Process** — `WORKFLOW.md`, `done/` retention, status tooling.

---

Last updated: 2026-06-14 (Program 3 **complete** incl. 1560 polish; Program 4 next; non-CRM example queued)