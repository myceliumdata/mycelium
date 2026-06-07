# Task: Networks Phase 4 — CRM example network + extract from `data/`

**Read these first (mandatory):**
- `prompts/cursor/WORKFLOW.md`
- `docs/plans/networks-terminology.md` (Phase 4, CRM example decision)
- `data/seed.json`, `data/prepare_seed.py`, `data/seed_crm.json`
- Phase 2–3 path resolver + registry (must be landed)

**Depends on:** Phase 2 (path resolver) minimum; Phase 3 recommended for quick-start `network register`.

**Prototype reference:** `git show prototype:data/seed.json` for migration source.

---

## Objective

1. Add committed **`examples/networks/crm/`** — standard `network_root` layout, evolving public CRM reference (subset of current seed is OK; synthetic rows OK if cleaner).
2. Remove committed CRM seed from repo root **`data/`** default layout (no `data/seed.json` in clone).
3. Update quick start: copy example → user path, register, query.

Paul: example **will evolve** — structure matters more than row count.

---

## `examples/networks/crm/` layout

```
examples/networks/crm/
  network.json          # name: "crm", description for docs
  seed.json             # people array (public-safe)
  README.md             # how to copy to your network_root
```

Optional: minimal `categories.json` only if needed for demo queries without factory regen.

**Do not** commit private/sensitive rows if any exist in current seed — curate or synthesize.

---

## Tooling

- `bin/copy-example-network` (or `mycelium network init --from-example crm --root <path>` if CLI group exists):
  - Copy `examples/networks/crm/` → target `network_root`
  - Optionally run `network register` if Phase 3 landed

---

## Repo cleanup

| Remove / stop committing | Replace with |
|--------------------------|--------------|
| `data/seed.json` | `examples/networks/crm/seed.json` |
| `data/seed_crm.json`, `raw_data.json` | `examples/` scripts or archive note |

Keep `data/` directory with `.gitkeep` or README explaining runtime dir / legacy shim.

Update tests that assumed `data/seed.json`:
- Use `examples/networks/crm/seed.json` via `--network-dir` or tmp copy in fixtures.
- Ensure smoke suite still passes.

Update `.env.example`: `MYCELIUM_SEED_PATH` deprecated in favor of network root (note in comments).

---

## Docs

- README quick start: framework clone → `copy-example-network` → `network register` → query.
- `docs/architecture.md` seed section → points at network root + example.

---

## Scope boundaries

**May modify:** `examples/networks/crm/`, `bin/`, `data/` (remove committed seed), tests, README, architecture, `.gitignore` if needed.

**Out of scope:** Network creation prompt (Phase 5), distributed discovery, changing graph logic.

---

## Verification

```bash
uv run pytest -m smoke -q
uv run ruff check src tests bin/
```

Manual: fresh clone path — copy example, register, query Nichanan or example person.

---

## Deliverables

`prompts/cursor/done/2026-06-07-1300-networks-phase4-crm-example/`