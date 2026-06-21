# Example network documentation

Operator and contributor docs for committed networks under [`examples/networks/`](../../examples/networks/).

---

## Start here

| Doc | Audience |
|-----|----------|
| [getting-started.md](getting-started.md) | **Shared** clone, `.env`, two-step protocol, MCP, gates |
| [exploration-walkthroughs.md](exploration-walkthroughs.md) | How feature walkthroughs are organized |

---

## Per network

| Network | Getting started | Feature walkthroughs |
|---------|-----------------|----------------------|
| **CRM (seeded)** | [crm-seeded/getting-started.md](crm-seeded/getting-started.md) | [crm-seeded/explore/](crm-seeded/explore/README.md) |
| **CRM (empty)** | [crm-empty/getting-started.md](crm-empty/getting-started.md) | [crm-empty/explore/](crm-empty/explore/README.md) |
| **CRM metering** | [crm-metering/getting-started.md](crm-metering/getting-started.md) | [crm-metering/explore/](crm-metering/explore/README.md) |
| **Baseball** | [baseball/getting-started.md](baseball/getting-started.md) | [baseball/explore/](baseball/explore/README.md) |

Pack READMEs under `examples/networks/<name>/` cover maintainer layout and bootstrap internals; prefer **`docs/examples/`** for runnable query guides.

---

## Reference samples

| File | Purpose |
|------|---------|
| [sample-categories.json](sample-categories.json) | Illustrative `categories.json` shape (not loaded at runtime) |

---

## Related

- [onboarding.md](../onboarding.md) — contributor terminology and read order
- [manual-checks/2026-06-20-live-gate-program.md](../manual-checks/2026-06-20-live-gate-program.md) — automated live regression
- [manual-checks/2026-06-21-baseball-program-post-program-gate.md](../manual-checks/2026-06-21-baseball-program-post-program-gate.md) — baseball v1 sign-off