# Review — LLM computation codegen model remediation (0900)

**Verdict:** **Approved**

**CI:** `./bin/ci-local` — 579 smoke passed, ruff clean, admin-ui build ok.

---

## Scope reviewed

Rename `MYCELIUM_DERIVE_MODEL` → `MYCELIUM_COMPUTATION_CODEGEN_MODEL`; `derive_model()` → `computation_codegen_model()`; doc fixes (`.env.example`, `architecture.md`, hand-test); no backward compat; spot-check greps clean in `src/`, `tests/`, `examples/`, `.env.example`, `docs/architecture.md`, `docs/manual-checks/`.

---

## What works

- Operator-facing name aligns with provenance `computation` + `codegen` behavior; not baseball-specific in shipped docs.
- `.env.example` lists all five `MYCELIUM_*_MODEL` vars with computation-codegen guidance (`gpt-4o+` recommendation; OPS as parenthetical example only).
- `derive_resolve.py` stamps `computation.model` from `computation_codegen_model()`.
- No `MYCELIUM_DERIVE_MODEL` / `derive_model(` remain in production paths.

---

## Operator action (Paul)

Rename framework `.env`:

```bash
MYCELIUM_COMPUTATION_CODEGEN_MODEL=gpt-4o
```

Remove `MYCELIUM_DERIVE_MODEL` — it is **not** read.

---

## Known limitations (accepted; on TODO)

- v1 still uses `FALLBACK_MODEL` when vars unset — see **LLM model configuration — strict (review)** in `TODO.md`.

---

## Polish nits (non-blocking)

| # | Item |
|---|------|
| P1 | `.env.example` header “unset defaults to gpt-4o-mini” documents current behavior Paul intends to replace — leave until strict slice. |
| P2 | `output.md` “mark env-only done” superseded by Grok `TODO.md` partial + strict follow-up. |

---

## Suggested commit message

```
config: central LLM model env selection; rename computation codegen var
```