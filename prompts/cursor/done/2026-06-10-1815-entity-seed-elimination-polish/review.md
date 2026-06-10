# Review — Seed elimination Polish (vocabulary + code nits)

**Reviewer:** Grok (June 2026)  
**Verdict:** **Approve** — scoped polish complete; tests green. Patch README §How it works before batch commit (Slice 18 carry-over).

---

## Summary

Polish closes the Slice 16–18 nit backlog in scope: CLI/MCP operator strings, registry `list_entities()`, `matched_records` param, P5 docs, `empty-crm` example + smoke test, supervisor internal renames, admin dist build verified. Runtime grep clean; full pytest **299 passed** (+1 from `empty-crm` smoke). Deferred field renames (`SeedRecord`, `seed_records`) correctly left alone.

**Pre-commit:** Root `README.md` §How it works (lines ~305–341) and `PKG-INFO` echo still describe deleted `agents/seed.py` and `mycelium seed` CLI — out of polish scope per prompt (Slice 18) but must be fixed in the 17+18+polish batch commit.

---

## Checklist (polish scope)

| Item | Verdict | Notes |
|------|---------|-------|
| **P1** CLI/MCP strings | Pass | `query` help → entity/registry; `network status --entity` → entity; introspection has no `Seed:` |
| **P1 stragglers** | Nit | `main.py` L70 `seed identity`; MCP `health_check` L280 `seed data` — acceptable bootstrap wording; optional tighten |
| **P2** docstrings | Partial | `state.py` L116–118, `responses.py` L439 still say `seed match` / `seed identity only` |
| **P3** `list_entities()` | Pass | Public API; `entity_resolution.py` uses it (no `_data` peek) |
| **P4** `matched_records=` | Pass | `context.py` + `dispatch.py`; graph state field aligned |
| **P5** docs | Pass | `full-code-walkthrough.md`, `database-notes.md`, `CORE_PROMPT.md`, `PROJECT_BRIEF.md` — no runtime-loader refs |
| **P6** crm README | Pass | Bootstrap vs registry clarified; L62 `seed hit` → optional `registry hit` nit |
| **P7** `empty-crm` | Pass | `network.json`, `guide.md`, `README.md`, `queries/01-bind-paul-murphy.json`; smoke test added |
| **P8** admin dist + PKG-INFO | Pass* | `npm run build` OK per `output.md`; `uv pip install -e .` run — PKG-INFO still mirrors stale README long description |
| **Supervisor renames** | Pass | `_identity_records_from_match`, `_seed_records_from_match` |
| **Governance** | Pass | No Cursor `review.md`; no `TODO.md` edits |
| **Runtime grep** | Pass | No `agents.seed` / `get_seed_data` / `find_by_key` / `seed_people_count` in `src/`, `tests/`, `admin-ui/src/` |

---

## Tests (re-verified — no shortcuts)

```bash
uv run ruff check src tests
→ All checks passed!

LANGCHAIN_TRACING_V2=false uv run pytest -q
→ 299 passed in 29.76s

uv run pytest -q   # tracing on (LangSmith rate-limit warnings only)
→ 299 passed in 33.06s

uv run pytest -m smoke -q
→ 273 passed, 26 deselected
```

LangSmith multipart ingest logs 429s during runs; **zero test failures** with or without `LANGCHAIN_TRACING_V2=false`.

---

## Docs review (all changed / operator-facing)

| Doc | Verdict | Notes |
|-----|---------|-------|
| `docs/architecture.md` | Pass* | Seed-elimination section (L60–65) correct; L69 still says "resolves **seed** matches" → should say registry |
| `docs/full-code-walkthrough.md` | Pass | Registry + bootstrap import; no `agents.seed` |
| `docs/database-notes.md` | Pass | `entities.json` resolution; legacy `mycelium seed` removal noted |
| `prompts/system/CORE_PROMPT.md` | Pass | Bootstrap fixture vocabulary |
| `prompts/system/PROJECT_BRIEF.md` | Pass | June 2026 blurb |
| `examples/networks/crm/README.md` | Pass | Bootstrap-only import; growth section accurate |
| `examples/networks/crm-metering/guide.md` | Pass | "bootstrap fixture" wording |
| `examples/networks/empty-crm/*` | Pass | Contrast with `crm`; Paul Murphy bind arc documented |
| `README.md` (top / quick start) | Pass | `empty-crm` row, `registry_entity_count` curls, bootstrap note L205 |
| `README.md` (§How it works) | **Fail** | L307, L325–333, L341 still reference `agents/seed.py`, runtime seed loader, `mycelium seed` CLI |
| `src/mycelium.egg-info/PKG-INFO` | **Fail** | Mirrors stale README §How it works (regen after README fix) |

`docs/plans/*` and `prompts/cursor/done/*` historical refs to seed loader are expected and out of scope.

---

## Nits

| Severity | Item | Owner |
|----------|------|-------|
| **Pre-commit** | README L305–341: rewrite for `entities.json` + bootstrap import; drop `agents/seed.py` row and `mycelium seed` CLI; mermaid `Seed` node → `entities.json` / registry | Grok/Paul (batch commit) |
| **Pre-commit** | `docs/architecture.md` L69: "registry matches" not "seed matches" | Same |
| **Pre-commit** | Re-run `uv pip install -e .` after README fix so PKG-INFO long description updates | Paul |
| Low | P2: `state.py` / `responses.py` outcome strings — `registry` / `entity` not `seed match` | Optional in batch |
| Low | `examples/networks/crm/README.md` L62: "validated or registry hit" | Optional |
| Low | `main.py` L70 / MCP `health_check` docstring — "core identity" vs "seed identity" | Optional |

`output.md` claims README "how-it-works" updated — only partial (quick-start / demo lines); §How it works block untouched.

---

## Phase sign-off

| Criterion | Verdict |
|-----------|---------|
| Polish P1–P8 in scope | Pass |
| `empty-crm` shipped + smoke | Pass |
| Full pytest green | Pass — 299 |
| Smoke pytest green | Pass — 273 |
| Operator docs accurate end-to-end | Pass after README patch |

---

## Recommendation

1. **Approve polish** — safe to batch commit **Slices 17 + 18 + polish** together.
2. **Before commit:** patch README §How it works + `architecture.md` L69; regen PKG-INFO.
3. After commit: Grok + Paul check `TODO.md` + `entity-seed-elimination-phase.md` (Slices 14–18, empty-seed demo, phase exit).
4. Rebuild `admin-ui/dist/` locally if using `--demo` (dist gitignored; source already Entities-only).

Suggested batch commit message (unchanged from `output.md`):

```
Polish seed-elimination vocabulary, empty-crm, and review nits.

CLI/MCP/docstrings; list_entities; matched_records param;
empty-crm example; admin dist build verified.
```

Add README/architecture doc fix to commit body or follow-up amend if patched separately.