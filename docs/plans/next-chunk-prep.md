# Next chunk — prep brief (Paul + Grok, June 2026)

**Prerequisite:** MVR redesign manual gate **CLEAR** — [`2026-06-13-mvr-redesign-post-program-gate.md`](../manual-checks/2026-06-13-mvr-redesign-post-program-gate.md).

---

## Where we are

| Track | Status |
|-------|--------|
| **Program 1 — Provenance** | **Complete** — pushed June 2026 |
| **MVR redesign** | **Complete** (M1–M10) — on `origin/main` |
| **Program 2 — MVR / entity storage** | **Complete locally** (Slices 1–3 + polish) — manual gate pending → push |
| **Program 3 — Operator write** | Next — admin edit + force re-research |
| **Toolbox** | TBD (Paul to define) |
| **Research robustness** | Backlog — [`research-robustness-backlog.md`](research-robustness-backlog.md) |
| **Website sync** | Review [myceliumdata.org](https://myceliumdata.org) after major pushes |

**Manual gate:** [`2026-06-13-program2-post-program-gate.md`](../manual-checks/2026-06-13-program2-post-program-gate.md) — run before push.

**Active Cursor prompt:** None — Program 2 complete; queue Program 3 when ready.

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
| **Program 3** | Operator edit + force re-research UI |
| **Research robustness** | Independent hardening |
| **Toolbox** | Paul defines |

---

## What waits on Paul

1. Run Program 2 manual gate (morning) — [`2026-06-13-program2-post-program-gate.md`](../manual-checks/2026-06-13-program2-post-program-gate.md).
2. On **CLEAR**, push `origin/main` and bump `TODO.md`.
3. **`TODO.md`** — Grok + Paul bump when Program 2 ships (Cursor does not edit).

---

*Updated: June 2026 (Program 2 complete; Program 3 next)*