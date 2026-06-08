# Task: Demo slice 2 — `mycelium network status`

**Read these first (mandatory):**
- `prompts/cursor/WORKFLOW.md`
- `TODO.md` → Demo (phase) → Slice 2
- `src/network/paths.py`, `src/network/registry.py`
- `src/agents/specialists/base.py` (`SpecialistStorage`)
- `src/agents/registry.py`, `src/agents/seed.py`
- Demo slice 1 output (if merged): `prompts/cursor/done/2026-06-08-1000-demo-slice1-refresh-example-network/`

**Depends on:** Demo slice 1 recommended (canonical `network_root` + refresh); may run in parallel if slice 1 not merged — use `--network-dir` in tests.

**Blocks:** Demo slice 3 (admin daemon reuses introspection module).

---

## Objective

Add a **read-only network snapshot** for Paul’s demos: show ontology, specialists, and storage counts **before and after** queries — without `ls`, `cat`, or invoking specialist agents.

```bash
uv run mycelium network status
uv run mycelium network status --network crm
uv run mycelium network status --json
```

Human-readable output is the primary UX (Rich tables or aligned columns). `--json` for scripting and future admin UI.

---

## Architecture (locked)

### Shared module: `src/network/introspection.py`

Single read model used by CLI now and **admin daemon later** (slice 3). Do not duplicate logic in `main.py`.

**Read via framework APIs — not specialist agent invoke, not ad-hoc JSON scattered in CLI:**

| Source | API / path |
|--------|------------|
| Network root | `NetworkPaths`, `resolve_network_root`, optional `network_metadata` |
| Seed | `get_seed_data()` / seed loader — person count |
| Ontology | `categories.json` if present; else report “not created yet (run a query)” |
| Registry | `get_agent_registry().list_agents()` |
| Specialist modules | `MYCELIUM_SPECIALISTS_DIR` — `*_specialist.py` on disk vs registry |
| Per-category storage | `SpecialistStorage(category).load()` — **do not** trigger research or mkdir side effects beyond what `SpecialistStorage` already does on init |

Design for future multi-store: summarize via storage payload + `storage_strategy.json` `strategy` field; do not assume flat JSON only in public summary types.

### Suggested summary shape (Python dataclasses or TypedDict)

```python
NetworkStatusSummary:
  network_name, network_root, display_name (from network.json if any)
  seed_people_count: int
  ontology_present: bool
  categories: list[CategorySummary]  # name, assigned_agent, example attrs count
  specialists: list[SpecialistSummary]  # agent name, category, py_on_disk, record_count, fields_tracked
```

`SpecialistSummary` per category storage:
- `record_count` — len(`records`)
- `fields_tracked` — union of keys across records (excluding meta)
- Optional: counts of `status: pending` / `na` / values found (best-effort on flat_json_v1)

Optional drill-down flags (implement if straightforward):
- `--category contact` — one specialist section
- `--person "Andrea Kalmans"` — resolve seed id via `find_by_key`, show per-field status for matching categories

---

## CLI wiring

Add **`mycelium network status`** subcommand under existing `network` parser in `src/main.py`.

| Flag | Purpose |
|------|---------|
| `--network-dir` | Path (highest precedence) |
| `--network` | Registry name |
| `--json` | Machine-readable dump of summary |
| `--category` | Filter (optional) |
| `--person` | Person drill-down (optional) |

Apply `apply_network_paths()` before introspection (same as `query`). **Read-only** — no graph, no `run_query`.

### Human-readable output (demo-oriented)

Example sections:

```
Network: crm (CRM example)
Root: /Users/paul/mycelium-networks/crm
Seed: 15 people
Ontology: not created yet — run a query to bootstrap categories.json
Specialists: none registered
```

After queries:

```
Specialists:
  contact_specialist   category=contact   module=yes   records=1   fields=email, address
```

Keep it scannable for non-engineers in a terminal recording.

---

## Tests

| Test | Marker |
|------|--------|
| Empty network (seed only) — 0 specialists, ontology absent | smoke |
| Post-query fixture — registry agents + storage record count ≥ 1 | smoke or full |
| `--json` round-trip | smoke |
| `--person` drill-down with known seed name | full |
| Isolated registry + `tmp_path` network root | use `tests/network_helpers.py` |

Prefer building fixture by copying `examples/networks/crm/seed.json` into tmp root + optional pre-baked `categories.json` / minimal `storage.json` — avoid live API keys.

---

## Docs

- **README** — one paragraph under CLI network section: `network status` for demo/ops visibility.
- **`examples/networks/crm/README`** — mention status before/after demo queries.

No large architecture rewrite.

---

## Verification

```bash
uv run pytest -m smoke -q tests/test_network_status.py  # or named tests
uv run ruff check src/network/introspection.py src/main.py tests/
uv run mycelium network status --network-dir examples/networks/crm  # seed only; may error if examples dir lacks full root — use tmp in manual check
```

---

## Scope boundaries

**May modify:** `src/network/introspection.py` (new), `src/network/__init__.py` exports, `src/main.py`, `tests/`, README, `examples/networks/crm/README.md`

**Out of scope:** HTTP admin daemon, UI, write/mutate operations, changes to specialist generated code

---

## Deliverables

`prompts/cursor/done/2026-06-08-1100-demo-slice2-network-status/` with `prompt.md`, `output.md` (sample human + JSON output from empty vs populated network).