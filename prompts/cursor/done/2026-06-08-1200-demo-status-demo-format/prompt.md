# Task: Demo status output — scannable default + `--verbose`

**Read these first (mandatory):**
- `prompts/cursor/WORKFLOW.md` — claim by moving to `in-progress/` before starting
- `src/network/introspection.py`, `src/main.py`, `tests/test_network_status.py`
- `docs/examples/sample-categories.json` (category `examples` arrays)
- Paul’s spec (this prompt) and demo runbook in `README.md`

**Depends on:** Demo slices 1–2 + slice 5 polish complete.

**Blocks:** Paul hands-on demo testing with final status UX.

---

## Workflow

1. Move this file to `prompts/cursor/in-progress/`.
2. Implement below.
3. Deliver `prompts/cursor/done/2026-06-08-1200-demo-status-demo-format/` with `prompt.md`, `output.md` (include before/after samples).
4. Update `TODO.md` (new slice or note under Demo phase).

---

## Objective

Replace the **default** human output of `mycelium network status` with a **demo-scannable** format. Move today’s debug-oriented layout behind **`--verbose`**. **`--json` unchanged** (full `NetworkStatusSummary`; additive fields OK if useful).

---

## Default demo format (human)

### Header (always)

```
Network: crm (CRM example)
```

Use `display_name` in parens when present (same as today). **Do not print `Root:`** in demo mode.

### Seed

```
Seed: ✅ (15)
```

- Always `✅` when status runs successfully (seed loaded).
- Number is **record count only** — no “people” (domain-agnostic: CRM, cars, etc.).
- Use `summary.seed_people_count` (field name can stay internal; label must not say “people”).

### Current ontology

**Absent** (`categories.json` missing / not parseable):

```
Current ontology: ❌
```

**Present** — list each category with abbreviated example attributes from ontology `examples` array:

```
Current ontology:
  contact (e.g., email, phone, …)
  demographic (e.g., age, birthday, …)
  financial (e.g., net_worth, salary, …)
  professional (e.g., title, bio, …)
  relationships (e.g., spouse, partner, …)
  social (e.g., linkedin, x_handle, …)
```

**Abbreviation rules** (helper e.g. `_format_category_examples(examples: list[str]) -> str`):

| `len(examples)` | Output suffix |
|-----------------|---------------|
| 0 | `contact` only (no parens) |
| 1 | `contact (e.g., email)` |
| 2 | `contact (e.g., email, phone)` |
| ≥3 | first two + `, …)` → `contact (e.g., email, phone, …)` |

Read examples from `categories.json` → `categories[name].examples`. Extend `CategorySummary` with `examples: list[str]` in `_category_summaries` (sorted category names). Additive `--json` field is fine.

### Existing specialists

**No storage** (no specialist with `record_count > 0`):

```
Existing specialists: ❌
```

**Has storage** — one line per category that has records; use **category slug**, not agent name:

```
Existing specialists:
  contact (1)
```

- Only categories with `record_count > 0`.
- Count is total records in that category’s storage (today usually 0 or 1).
- Sort alphabetically by category.

---

## `--verbose` (today’s debug layout)

Rename/refactor current `format_status_human` body into **`format_status_verbose`** — keep behavior:

- `Root:` path
- `Seed: N people` (or update to `Seed: N records` for consistency — optional)
- Per-category `agent=` / `examples=` counts
- Full specialist table (`module=`, `fields=`, status counts)
- “none with storage yet” branch when applicable

Wire CLI:

```python
status_cmd.add_argument("--verbose", action="store_true", help="Debug-oriented status layout")
# ...
if args.json:
    print(json.dumps(...))
elif args.verbose:
    console.print(format_status_verbose(summary))
else:
    console.print(format_status_demo(summary))
```

Export `format_status_demo`, `format_status_verbose` from `src/network/__init__.py`.

---

## `--person` drill-down (defer demo polish)

**Out of scope for demo formatting** — when `--person` is set, **append** the existing verbose person block (today’s `Person lookup:` / `Fields:` section) below the demo summary. Do not redesign person UX in this task.

---

## Tests (`tests/test_network_status.py`)

| Test | Marker |
|------|--------|
| Demo — seed-only network | smoke — assert `Seed: ✅ (15)`, `Current ontology: ❌`, `Existing specialists: ❌`; no `Root:` |
| Demo — ontology, no storage | smoke — `Current ontology:` + `contact (e.g., email, phone, …)`; `Existing specialists: ❌` |
| Demo — contact has 1 record | smoke — `Existing specialists:` + `contact (1)`; no `contact_specialist` agent line |
| `_format_category_examples` unit cases | smoke — 0/1/2/3+ examples |
| Verbose — still has `Root:` and agent lines | smoke |
| `--json` unchanged shape | smoke — existing round-trip still passes |
| CLI `--verbose` | smoke — subprocess asserts `Root:` present |

Update/remove tests that asserted old default strings (`none with storage yet`, `none registered`, etc.) on **default** path.

---

## Docs

- **README** — default status is demo layout; mention `--verbose` for debugging; update sample output block.
- **`examples/networks/crm/README.md`** — same one-line note.

---

## Verification

```bash
uv run pytest -m smoke -q tests/test_network_status.py
uv run pytest -m smoke -q
uv run ruff check src/network/introspection.py src/main.py tests/test_network_status.py
uv run mycelium network status --network-dir examples/networks/crm
uv run mycelium network status --network-dir examples/networks/crm --verbose | head -5
```

---

## Scope boundaries

**May modify:** `src/network/introspection.py`, `src/network/__init__.py`, `src/main.py`, `tests/test_network_status.py`, `README.md`, `examples/networks/crm/README.md`, `TODO.md`

**Out of scope:** `--person` demo redesign, admin daemon, `query --json`, changing `build_network_status()` read logic beyond `CategorySummary.examples`

---

## Deliverables

`prompts/cursor/done/2026-06-08-1200-demo-status-demo-format/` with before/after terminal samples for **new network** and **running network** (post-query fixture).