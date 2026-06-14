# Next chunk — prep brief (Paul + Grok, June 2026)

**Prerequisite:** MVR redesign manual gate **CLEAR** — [`2026-06-13-mvr-redesign-post-program-gate.md`](../manual-checks/2026-06-13-mvr-redesign-post-program-gate.md).

---

## Where we are

| Track | Status |
|-------|--------|
| **Program 1 — Provenance** | **Complete** — pushed June 2026 |
| **MVR redesign** | **Complete** (M1–M10) — on `origin/main` |
| **Program 2 — MVR / entity storage** | **Complete** — on `origin/main`; manual gate **CLEAR** (2026-06-14) |
| **Program 3 — Entity protocol legacy cleanup** | **Next** (Paul) — remove name/`entity_key`/status `--entity` special cases — [`entity-protocol-legacy-cleanup-program.md`](entity-protocol-legacy-cleanup-program.md) |
| **Program 4 — Operator write** | Deferred — admin edit + force re-research (after Program 3) |
| **Toolbox** | TBD (Paul to define) |
| **Research robustness** | Backlog — [`research-robustness-backlog.md`](research-robustness-backlog.md) |
| **Website sync** | Review [myceliumdata.org](https://myceliumdata.org) after major pushes |

**Manual gate:** [`2026-06-13-program2-post-program-gate.md`](../manual-checks/2026-06-13-program2-post-program-gate.md) — **CLEAR** (2026-06-14).

**Active Cursor prompt:** None — lock Program 3 when ready.

---

## Program 2 — locked requirements (summary)

| Topic | Decision |
|-------|----------|
| Bind-field history | Specialist `versions[]` only — **no** entity-level `bind_versions[]` |
| Ownership | **`attribute_map`** in taxonomy (not hardcoded Python) |
| Research vs operator | **Allow** new versions; **prompt deference** when human set current value |
| Index correction | **Replace** keys — no aliases |
| Slices | **3:** write → read/admin → polish |

**Program spec:** [`attribute-provenance-program2.md`](attribute-provenance-program2.md)  
**Architecture:** [`attribute-provenance-and-storage.md`](attribute-provenance-and-storage.md)

---

## Post-MVR notes for Program 2

- Unified write must maintain **`bind_index`** and **`field_index.py`** indexes (MVR M4).
- Bind entry points: `ensure_bound_entity`, seed import, `target_deliver.bind_provisional_from_scope` (step-2 create).
- `query_provenance.py` includes bind fields when versioned specialist storage exists (Program 2 Slice 2).
- Research prompts defer to `actor: operator` current versions; research may still append a new version (Program 2 Slice 3).

---

## After Program 2

| Track | Why |
|-------|-----|
| **Program 3** | Legacy protocol cleanup — one MVR `lookup` story for query, status, admin |
| **Program 4** | Operator edit + force re-research UI |
| **Research robustness** | Independent hardening |
| **Toolbox** | Paul defines |

---

## What waits on Paul

1. Lock Program 3 scope — [`entity-protocol-legacy-cleanup-program.md`](entity-protocol-legacy-cleanup-program.md).
2. Queue first Program 3 slice in `prompts/cursor/next/` when ready.

---

*Updated: June 2026 (Program 2 gate **CLEAR**; Program 3 = legacy cleanup per Paul)*