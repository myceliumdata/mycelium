# Mycelium — Grok Build agent rules

Standing behavior for **Grok Build** in this repo. Cursor has its own rules under `.cursor/rules/` and `prompts/cursor/WORKFLOW.md`.

## Default mode: diagnose only

Unless Paul explicitly authorizes implementation in the **current message**, Grok is **read-only on production code**.

**Do**

- Read, search, explain, and diagnose (root cause, repro steps, what to verify).
- Review Cursor slices: write `review.md`, run `./bin/ci-local`, commit **after Approved** per `prompts/cursor/WORKFLOW.md` §4.
- Queue work for Cursor: write prompts in `prompts/cursor/next/`.
- Update review artifacts, manual gate docs, and planning docs when Paul asks or when review workflow requires it.

**Do not**

- Edit `src/`, `tests/`, `bin/`, `examples/`, or `admin-ui/` to “fix” something you found while diagnosing.
- Run `git add` or `git commit` for ad-hoc fixes, experiments, or “helpful” patches Paul did not request.
- Treat “I found the bug” as permission to implement. Finding the cause ≠ authorization to change code.

**Implementation belongs to Cursor.** If a fix is needed, describe it and either queue a slice in `prompts/cursor/next/` or wait for Paul to say implement.

## When Paul authorizes implementation

Grok may edit source or commit only when Paul’s **current message** clearly asks, for example:

- “implement”, “fix it”, “make the change”, “apply the patch”
- “queue a slice and …” (if Paul wants Grok to write the prompt only, that is not a license to edit `src/` — only to write under `prompts/cursor/next/`)
- “commit” (for an already-reviewed, approved slice — not for a new unsolicited fix)

If unclear, **ask** or stay in diagnose-only mode.

## Ownership reminders

| Artifact | Owner |
|----------|--------|
| `TODO.md` | Grok + Paul only — Grok does not edit unless Paul asks for a roadmap update |
| `src/`, `tests/`, etc. | Cursor (via claimed slices) — Grok only with explicit authorization above |
| `prompts/cursor/next/` | Grok + Paul create prompts; Cursor executes |
| `prompts/cursor/done/*/review.md` | Grok after slice review |
| `origin` push | Paul only — Grok pushes only when Paul explicitly asks |

## Related docs

- `prompts/cursor/WORKFLOW.md` — full handoff, review checklist, commit/push policy
- `docs/architecture.md` — design source of truth
- `prompts/system/CORE_PROMPT.md` — project principles