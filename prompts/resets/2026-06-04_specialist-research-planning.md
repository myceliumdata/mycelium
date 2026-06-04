# Context reset — Specialist research planning (2026-06-04)

**Purpose:** Resume this conversation thread after context compaction or a new session. Read [BACKGROUND.md](BACKGROUND.md) Tier 1 first, then this file in full.

**Date:** 2026-06-04  
**Active plan (draft, awaiting Paul's review):** [docs/plans/specialist-research-phase1.md](../../docs/plans/specialist-research-phase1.md)

---

## What we are doing

Planning **Phase 1 specialist research**: replace the empty `_stub_background_research` in generated specialists with a bounded **LLM + tools** loop so specialists can **find** requested attribute values (web search at minimum), validate them, and persist to per-category `data/agents/<category>/storage.json`.

**Not in scope yet:** implementation until the design doc is reviewed and approved.

---

## Key decisions already agreed (discussion)

| Topic | Decision |
|-------|----------|
| Search provider | **Tavily** (`langchain-tavily`, env `TAVILY_API_KEY`) |
| Tools vs LLM | Tool **schemas** are handed to the LLM; **execution** is application-side (tool-calling loop) |
| Who searches | **Specialists only** via shared `src/tools/` — not the supervisor, not MCP callers |
| Specialist invocation | **Always** invoke specialist for classified requested attrs (e.g. `name` → contact), even if seed has a value |
| Seed vs specialist | Specialist **wins** when it has a non-pending value; seed is **provisional** while research is pending |
| Public `results` | Attribute-scoped: `id` + requested keys only; bare lookup returns `id`, `name`, `employer` |
| Canonical id | **`id` only** (no `person_id` in public results); rename landed in slice 1300 |
| LangSmith URL | Stays on **CLI second line** — not inside `PersonResponse` JSON |
| Phase 1 execution mode | **Async** background research thread (keep current UX); sync in-graph deferred |
| Phase 1 tools | **`web_search` only** (Tavily); Extract/Crawl later |
| God agents | **No** — shared `research.py` runner, per-category Jinja prompt fragments only |

---

## LLM + tools (conceptual — for planning discussions)

1. Build system + user messages from person context, `target_fields`, category metadata.
2. Attach Tavily `web_search` tool definition to the model.
3. Model may request tool calls → run Tavily → feed results back → repeat (bounded rounds).
4. Model outputs structured **field proposals** (value, confidence, source URLs).
5. Runner validates and writes `storage.json`; graph assembly already merges contrib + seed.

---

## Work completed earlier in this session (historical)

### Onboarding

- Read `PROJECT_BRIEF.md`, `README.md`, `prompts/system/*` at session start.
- Confirmed SQLite checkpoints + JSON flat files; updated briefs to fix drift (Postgres / `person_id` / bootstrap tasks).

### Query response fixes (implemented — Paul allowed exception for 1400)

- **1300:** Rename `person_id` → `id` everywhere. Reviewed **approved**. Artifacts: `prompts/cursor/done/2026-06-04-1300-rename-person-id-to-id/`.
- **1400:** Attribute-scoped `results`, specialist-first merge, honest messaging (e.g. `--attributes name` → only `id`+`name`; “shown from seed; verification in progress”). Reviewed **approved**. Artifacts: `prompts/cursor/done/2026-06-04-1400-filter-query-results-and-trace-url/`.
- **Note:** Grok implemented 1400 directly; Paul said to let it go this time. **Going forward: Cursor implements, Grok reviews/plans only** unless Paul explicitly asks Grok to code.

### Git (pushed to origin)

Commits on `main` include: cursor done-folder renames; agent briefs; `feat: canonical person id and attribute-scoped query results`; remove `CORE_PROMPT.md.~1~`. Branch was synced with `origin/main` after push.

### Specialist research planning

- Discussed smarter specialists, web search, prompt generation.
- Wrote **`docs/plans/specialist-research-phase1.md`** (full design — **Paul is about to review**).
- Grok **mistakenly** started Tavily code before design approval; Paul corrected: **planning only**. Any local Tavily scaffold may still be **uncommitted** — treat as optional/discardable until plan approved.

---

## Git / workspace state (verify on resume)

Run `git status` — expect at least:

- **Committed + pushed:** 1300/1400 code, briefs, cursor done artifacts.
- **Possibly uncommitted:** `docs/plans/specialist-research-phase1.md`, Tavily-related files (`src/tools/tavily.py`, `pyproject.toml`, `tests/test_web_search.py`, `.env.example` tweaks), doc pointer in `architecture.md`.

Do not assume — inspect.

---

## Design doc — open questions for Paul

From bottom of `specialist-research-phase1.md`:

1. **Low confidence:** default `na` vs stay `pending`?
2. **LangSmith:** child run naming preference?
3. **Rollout:** prove `contact` + `email` first vs regen all six specialists at once?
4. **Research prompt:** always include seed `name`/`employer` as hints?

---

## Approval checklist (plan not approved yet)

- [ ] Paul reviews `docs/plans/specialist-research-phase1.md`
- [ ] Open questions resolved
- [ ] Paul explicitly approves implementation
- [ ] Then: Grok drafts `prompts/cursor/next/` slices (or Paul says “work on next task” to Cursor)

**Do not** add Cursor prompts or source changes until approval.

---

## Suggested next steps after Paul’s doc review

1. Incorporate feedback into `specialist-research-phase1.md`.
2. Mark plan **Approved** in doc header when Paul agrees.
3. Draft Cursor slice prompts (1000 tavily → 1100 research runner → 1200 template → 1300 integration).
4. Paul runs Cursor on `next/` queue; Grok writes `review.md` in `done/`.

---

## Manual repro (for testing query behavior — post-1400)

```bash
uv run mycelium query --person-key "Nichanan Kesonpat" --attributes name
```

Expected: `results` with `id` + `name` only; message mentions seed provisional + specialist verification — not “name not currently available” while `name` is present.

---

## Strict rule for Grok on resume

Until Paul says otherwise:

- **Planning and discussion OK** (including editing `docs/plans/*` when asked).
- **No** `src/` implementation, **no** Cursor queue changes, **no** git commits — unless Paul explicitly requests them in that turn.

---

*End of context reset. Pair with [BACKGROUND.md](BACKGROUND.md) on every restart.*