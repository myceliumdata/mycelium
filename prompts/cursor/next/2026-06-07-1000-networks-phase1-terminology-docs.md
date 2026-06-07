# Task: Networks Phase 1 — terminology & architecture docs

**Read these first (mandatory):**
- `prompts/cursor/WORKFLOW.md`
- `docs/plans/networks-terminology.md` (locked decisions)
- `docs/architecture.md`
- `README.md`
- `TODO.md` (Networks roadmap)

**Depends on:** `prototype` git tag (`f706194` area) — pre-networks migration baseline.

**Prototype return:** `git checkout prototype` if networks work needs rollback.

---

## Objective

Document the **networks product model** before any runtime changes. No `src/` logic changes in this slice.

Users download the **framework** (repo) and run **named networks** at user-chosen **`network_root`** paths. One MCP server per network (parallel via `MYCELIUM_NETWORK_ROOT`). v1 name→path registry = local config file (Phase 3). Distributed discovery = long-term future.

---

## Doc updates required

### `docs/architecture.md`

Add a **Networks** section covering:

- Framework vs **network root** (user-chosen directory; standard layout from plan).
- Selection: `--network-dir`, env `MYCELIUM_NETWORK_ROOT`, default network (Phase 3), legacy `data/` shim (current prototype).
- MCP: one long-lived process per network; framework `cwd` + env for data root.
- Disambiguate product **network** vs agent collective vs social **profiles**.
- Link to `docs/plans/networks-terminology.md`.

### `README.md`

- Lead with: download framework → create/copy network at a path you choose.
- Note current flat `data/` is **prototype / transitional** until Phase 2+ lands.
- Mention `examples/networks/crm/` as forthcoming reference (Phase 4).
- MCP example: two parallel servers with different `MYCELIUM_NETWORK_ROOT`.
- Point to `prototype` tag for pre-migration snapshot.

### `docs/plans/networks-terminology.md`

- Remove or resolve open question “Start Cursor work” (Phase 1 in progress).
- No structural rewrite — light status note only if needed.

### Optional (small)

- `docs/full-code-walkthrough.md` — one paragraph alignment if networks are mentioned vaguely.
- Category seed copy in `src/agents/classification/engine.py`: “social and professional **profiles**” only if a one-line change fits without regenerating specialists.

---

## Scope boundaries (strict)

**May modify:** `docs/architecture.md`, `README.md`, `docs/plans/networks-terminology.md`, `docs/full-code-walkthrough.md` (minimal), optional one-line classification description.

**Out of scope:** `src/` runtime, CLI flags, config file implementation, moving `data/seed.json`, `TODO.md` (Grok updates after review).

---

## Verification

No tests required. Grep audit: README + architecture contain “network root”, “framework”, “default network”, MCP-per-network.

---

## Deliverables

Per `WORKFLOW.md` → `prompts/cursor/done/2026-06-07-1000-networks-phase1-terminology-docs/` with `prompt.md`, `output.md`.

**Next slice in queue:** Phase 2 path resolver (`2026-06-07-1100-...`).