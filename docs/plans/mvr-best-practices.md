# MVR best practices (network operators)

**Audience:** Paul + Grok, network designers, `describe_network` / capabilities text  
**Program:** [`mvr-redesign-program.md`](mvr-redesign-program.md)

---

## Runtime (MVR redesign M1–M10, shipped)

Clients use step 1 `id` or `lookup`, step 2 `delivery_id` (+ `quote_id` when metered). Step-1 outcome `lookup_resolved` replaces the legacy single-step `entity_key` handshake. When step 2 will create a new row (full MVR, 0 registry matches), step 1 includes `delivery.create_on_deliver: true` (omitted for existing matches). Examples: [`mvr-redesign-entity-query-examples.md`](mvr-redesign-entity-query-examples.md). Program spec: [`mvr-redesign-program.md`](mvr-redesign-program.md).

---

## What MVR is

**Minimum Viable Record** — the field set **your network** requires before Mycelium will:

1. **Create** a new entity (registry row), and  
2. **Run extended-attribute research** (email, linkedin, …) on that entity.

MVR is **not** how clients find records. Lookup uses **any subset** of indexed MVR fields (AND semantics). A loose lookup can return many matches; that is expected.

**Identity** in the protocol is always **`id` (UUID)**. Clients obtain `id` from delivery after resolve, or from a prior session.

---

## Designer tradeoffs

| MVR shape | Pros | Cons |
|-----------|------|------|
| **Loose** (e.g. `name` only) | Easy to add people | Many collisions (common names); ambiguous research context |
| **Tight** (e.g. `name` + `employer` + `employee_id`) | Fewer collisions; better research disambiguation | Harder for visiting agents to create rows; more negotiation |

**Your network, your tradeoff.** Mycelium does not mandate CRM’s `name` + `employer`; that is only the example default.

### Examples

| Domain | Reasonable MVR | Notes |
|--------|----------------|-------|
| **CRM (people)** | `name`, `employer` | Two “Kevin Zhang” rows OK if employers differ |
| **Enterprise HR** | `name`, `employer`, `employee_id` | Large orgs: same name + same division collisions |
| **Alibaba-scale** | `name`, `employee_id` (or similar) | Name alone is intentionally insufficient |

---

## Lookup vs MVR

| | Lookup | MVR |
|---|--------|-----|
| **Purpose** | Find existing rows | Gate create + research |
| **Fields** | Any subset of indexed MVR fields | Full `bind_fields` set |
| **Match** | AND within provided fields | All fields required together for uniqueness intent |
| **Example** | `employer=IBM` → many | `name` + `employer` both required to **add** Paul @ IBM |

---

## Two-step delivery (agent clients)

1. **Resolve** — send `lookup` or `id`; optional `requested_attributes` on this step only. Receive `total_matches` + `delivery_id` (`create_on_deliver: true` when step 2 will create) (+ quote if metered).  
2. **Deliver** — send `delivery_id` (+ `quote_id` if metered). Receive `results[]` (`found` / `assembled`).

Visiting agents should treat this as one logical operation; humans using CLI may use a wrapper or two commands.

---

## Metering

- **`metering.enabled: false`** — delivery on `delivery_id` is free.  
- **`metering.enabled: true`** — step 1 returns a **quote** for delivering the resolved scope (MVR rows and, if requested, extended-attribute research for **all** matches). Paying clients are not capped by `max_results` in v1.

---

## Indexes

Framework maintains **one index per MVR field** (normalized value → `[uuid, …]`). Compound indexes are optional operator optimizations later.

---

## Anti-patterns

- Using a single common field as MVR when collisions are common in your domain (unless you accept ambiguity).  
- Expecting lookup to require full MVR (it should not).  
- Storing “entity key” as name string instead of resolving to `id` before durable references.  
- Assuming MVR fields imply global uniqueness without index design — document collision handling for agents.

---

## Collision handling (agents)

When `total_matches` > 1:

- Return identities on deliver; let the agent pick or refine `lookup`.  
- Do not silently merge people.  
- Optional: network-specific guidance in `guide.md` (e.g. “always include employer for people queries”).

---

*Last updated: June 2026*